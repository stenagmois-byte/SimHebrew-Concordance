#!/usr/bin/env python3
"""Create a conservative, per-verse punctuation review report.

The Hebrew accent flags identify places to inspect; they do not determine
English punctuation. This script never edits the source or inserts punctuation.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from collections import defaultdict
from pathlib import Path


WORD_RE = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)*", re.UNICODE)
MAX_GLOSS_GAP_WORDS = 5


def read_items(path: Path) -> list[dict[str, str]]:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # The supplied export is a JSON object fragment beginning at "items":.
        fragment = raw.strip()
        # Some SQL exports prepend a comma before the top-level property.
        if fragment.startswith(","):
            fragment = fragment[1:].lstrip()
        try:
            data = json.loads("{" + fragment + "}")
        except json.JSONDecodeError:
            # Some exports retain the closing wrappers from the larger JSON
            # document they were copied from. Read the items array itself.
            property_match = re.search(r'"items"\s*:\s*', fragment)
            if not property_match:
                raise
            array_start = property_match.end()
            while array_start < len(fragment) and fragment[array_start].isspace():
                array_start += 1
            items, _ = json.JSONDecoder().raw_decode(fragment, array_start)
            data = {"items": items}
    items = data["items"] if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("Expected a top-level items list")
    return items


def verse_key(item: dict[str, str]) -> str:
    return "_".join(item["k"].split("_")[:3])


def decode_gloss(text: str) -> str:
    return html.unescape(text or "").strip()


def gloss_spans(text: str, gloss: str, start: int = 0) -> list[tuple[int, int]]:
    """Find all exact, case-insensitive gloss phrase occurrences."""
    gloss = decode_gloss(gloss)
    if not gloss:
        return []
    # Normalize whitespace but preserve the original span for context checks.
    words = [re.escape(w) for w in gloss.split()]
    if not words:
        return []
    return [
        (start + match.start(), start + match.end())
        for match in re.finditer(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)", text[start:], re.I)
    ]


def gloss_span(text: str, gloss: str, start: int = 0) -> tuple[int, int] | None:
    matches = gloss_spans(text, gloss, start)
    return matches[0] if matches else None


def aligned_gloss_span(
    text: str, gloss: str, prefix_rows: list[dict[str, str]]
) -> tuple[int, int] | None:
    """Choose a repeated gloss occurrence following the prior Hebrew prefix."""
    matches = gloss_spans(text, gloss)
    if len(matches) <= 1:
        return matches[0] if matches else None
    prior_positions = [
        span
        for row in prefix_rows[:-1]
        for span in record_word_positions(text, row)
    ]
    if not prior_positions:
        return None
    anchor = max(prior_positions, key=lambda span: span[1])[1]
    following = [span for span in matches if span[0] >= anchor]
    return following[0] if len(following) == 1 else None


def repeated_gloss_boundary_span(
    text: str,
    gloss: str,
    next_gloss: str,
    kind: str,
) -> tuple[int, int] | None:
    """Resolve repeats only when boundary evidence identifies one occurrence."""
    matches = gloss_spans(text, gloss)
    if len(matches) < 2:
        return None

    if kind == "ATNAH":
        atnah_matches = [span for span in matches if line_break_after(text, span[1])]
        if len(atnah_matches) == 1:
            return atnah_matches[0]

    if kind == "ZAQEF-QATAN":
        comma_matches = [span for span in matches if punctuation_after(text, span[1]) == ","]
        if len(comma_matches) == 1:
            return comma_matches[0]
        punctuated = [span for span in matches if punctuation_after(text, span[1])]
        if len(punctuated) == 1:
            return punctuated[0]

    # Use the following Hebrew gloss as a forward anchor only if it occurs
    # between exactly one candidate and the next repeated occurrence.
    if next_gloss:
        following_boundaries = []
        for index, span in enumerate(matches):
            window_end = matches[index + 1][0] if index + 1 < len(matches) else len(text)
            next_spans = [
                candidate
                for candidate in gloss_spans(text, next_gloss, span[1])
                if candidate[0] < window_end
            ]
            if len(next_spans) == 1:
                following_boundaries.append(span)
        if len(following_boundaries) == 1:
            return following_boundaries[0]
    return None


def noun_this_boundary_span(
    text: str, item: dict[str, str], previous_item: dict[str, str] | None
) -> tuple[int, int] | None:
    """Align Hebrew noun + demonstrative `this` to English `this` + noun."""
    if decode_gloss(item.get("e", "")).casefold() != "this" or not previous_item:
        return None
    noun_gloss = decode_gloss(previous_item.get("lemma", "")) or decode_gloss(previous_item.get("e", ""))
    noun_words = WORD_RE.findall(noun_gloss)
    if len(noun_words) != 1:
        return None
    noun_spans = gloss_spans(text, noun_words[0])
    this_spans = gloss_spans(text, "this")
    pairs = []
    for this_span in this_spans:
        for noun_span in noun_spans:
            if noun_span[0] < this_span[1]:
                continue
            gap = len(WORD_RE.findall(text[this_span[1]:noun_span[0]]))
            if gap <= 2:
                pairs.append((this_span, noun_span))
    return pairs[0][1] if len(pairs) == 1 else None


def construct_trimmed_span(text: str, gloss: str) -> tuple[int, int] | None:
    """Match a construct gloss after trimming a terminal `of` only."""
    gloss = decode_gloss(gloss)
    if not gloss.casefold().endswith(" of"):
        return None
    trimmed = gloss[:-3].rstrip()
    return gloss_span(text, trimmed) if trimmed else None


def ordered_term_positions(text: str, term: str) -> list[tuple[int, int]]:
    """Align phrase tokens in order, allowing a small number of inserted words.

    A result is returned only when there is one uniquely tight alignment.
    """
    words = [word.casefold() for word in WORD_RE.findall(decode_gloss(term))]
    english = list(WORD_RE.finditer(text))
    if not words or not english:
        return []
    candidates = [
        [index for index, token in enumerate(english) if token.group().casefold() == word]
        for word in words
    ]
    if any(not found for found in candidates):
        return []

    paths: list[tuple[int, ...]] = []

    def extend(path: tuple[int, ...], depth: int) -> None:
        if len(paths) > 512:
            return
        if depth == len(words):
            paths.append(path)
            return
        for index in candidates[depth]:
            if path:
                gap = index - path[-1] - 1
                if gap < 0 or gap > MAX_GLOSS_GAP_WORDS:
                    continue
            extend(path + (index,), depth + 1)

    extend((), 0)
    if not paths:
        return []
    best_gap = min(path[-1] - path[0] - len(path) + 1 for path in paths)
    best = [path for path in paths if path[-1] - path[0] - len(path) + 1 == best_gap]
    if len(best) != 1:
        return []
    return [english[index].span() for index in best[0]]


def record_word_positions(text: str, item: dict[str, str]) -> list[tuple[int, int]]:
    """Align gloss tokens, then lemma tokens, to English positions."""
    gloss = decode_gloss(item.get("e", ""))
    if gloss and gloss != "--":
        aligned = ordered_term_positions(text, gloss)
        if aligned:
            return aligned
    lemma = decode_gloss(item.get("lemma", ""))
    if lemma and lemma.casefold() != gloss.casefold():
        return ordered_term_positions(text, lemma)
    return []


def line_break_after(text: str, end: int) -> bool:
    return re.match(r"(?:[,;:.!?—–][ \t]*)?\r?\n", text[end:]) is not None


def reordered_prefix_boundary(
    text: str, prefix_rows: list[dict[str, str]], kind: str
) -> tuple[tuple[int, int], bool] | None:
    """Find a boundary after the rightmost English token aligned to the Hebrew prefix.

    This fallback applies only when the marked Hebrew word's English position
    is earlier than an aligned token from a preceding Hebrew word.
    """
    scope = text.split("\n", 1)[0] if kind == "ATNAH" else text
    previous_positions: list[tuple[int, int]] = []
    for row in prefix_rows[:-1]:
        previous_positions.extend(record_word_positions(scope, row))
    current_positions = record_word_positions(scope, prefix_rows[-1])
    if not previous_positions or not current_positions:
        return None
    previous_rightmost = max(previous_positions, key=lambda span: span[1])
    current_rightmost = max(current_positions, key=lambda span: span[1])
    if current_rightmost[1] >= previous_rightmost[1]:
        return None
    boundary = max(previous_positions + current_positions, key=lambda span: span[1])
    if kind == "ATNAH":
        return boundary, line_break_after(text, boundary[1])
    return boundary, bool(punctuation_after(text, boundary[1]))


def reordered_preceding_glosses_span(
    text: str, prefix_rows: list[dict[str, str]]
) -> tuple[int, int] | None:
    """Find preceding Hebrew glosses that all follow the marked gloss in English.

    English may place the marked word before a suffix of its preceding Hebrew
    glosses (for example, Hebrew ``fear / name / glorious / fearful / this``
    versus English ``fear this glorious and fearful name``). Return the last
    English word aligned to that reordered suffix, but only when its glosses
    are uniquely alignable and all occur after the marked gloss.
    """
    if len(prefix_rows) < 2:
        return None

    marked_positions = record_word_positions(text, prefix_rows[-1])
    if not marked_positions:
        return None
    marked_end = max(span[1] for span in marked_positions)

    reordered_positions: list[tuple[int, int]] = []
    marked_start = min(span[0] for span in marked_positions)
    for row in reversed(prefix_rows[:-1]):
        positions = record_word_positions(text, row)
        if not positions:
            break
        if min(start for start, _ in positions) >= marked_end:
            reordered_positions.extend(positions)
            continue
        if max(end for _, end in positions) <= marked_start:
            break
        # A gloss that straddles the marked word does not give a clear order.
        return None

    return max(reordered_positions, key=lambda span: span[1]) if reordered_positions else None


def reordered_adjacent_gloss_boundary(
    text: str, item: dict[str, str], previous_item: dict[str, str] | None
) -> tuple[tuple[int, int], str] | None:
    """Resolve a repeated marked gloss followed by the previous Hebrew gloss.

    This handles concise reversals such as Hebrew ``said / God`` versus
    English ``God said,``. It is accepted only when exactly one occurrence
    of the marked gloss is followed by the previous gloss's final word and
    punctuation.
    """
    if not previous_item:
        return None
    previous_words = WORD_RE.findall(decode_gloss(previous_item.get("e", "")))
    if not previous_words:
        previous_words = WORD_RE.findall(decode_gloss(previous_item.get("lemma", "")))
    if not previous_words:
        return None
    previous_word = previous_words[-1]
    marked_gloss = decode_gloss(item.get("e", ""))
    target_spans = gloss_spans(text, marked_gloss)
    pairs: list[tuple[tuple[int, int], str]] = []
    for target_start, target_end in target_spans:
        following = re.search(
            r"(?<!\w)" + re.escape(previous_word) + r"(?!\w)",
            text[target_end:],
            re.I,
        )
        if not following:
            continue
        previous_span = (target_end + following.start(), target_end + following.end())
        gap_words = len(WORD_RE.findall(text[target_end:previous_span[0]]))
        if gap_words > 3:
            continue
        punctuation = punctuation_after(text, previous_span[1])
        if punctuation:
            pairs.append((previous_span, punctuation))
    return pairs[0] if len(pairs) == 1 else None


def punctuation_after(text: str, end: int) -> str:
    tail = text[end:]
    match = re.match(r"\s*([,;:.!?—–])", tail)
    return match.group(1) if match else ""


def punctuation_before(text: str, start: int) -> str:
    head = text[:start]
    match = re.search(r"([,;:.!?—–])\s*$", head)
    return match.group(1) if match else ""


def inferred_negated_span(
    text: str, item: dict[str, str], previous_item: dict[str, str] | None
) -> tuple[int, int] | None:
    """Recover a reordered gloss's final word after an adjacent `not` gloss."""
    if not previous_item or decode_gloss(previous_item.get("e", "")).casefold() != "not":
        return None
    words = decode_gloss(item.get("e", "")).split()
    if not words:
        return None
    final_word = re.sub(r"^[^\w]+|[^\w]+$", "", words[-1])
    if not final_word:
        return None
    candidates = list(re.finditer(r"(?<!\w)" + re.escape(final_word) + r"(?!\w)", text, re.I))
    plausible = []
    for match in candidates:
        prefix = text[max(0, match.start() - 40):match.start()]
        if re.search(r"\bnot\b(?:\W+\w+){0,3}\W*$", prefix, re.I):
            plausible.append(match)
    if len(plausible) == 1:
        return plausible[0].span()
    return None


def final_gloss_word_before_newline(text: str, gloss: str) -> bool:
    """Whether the gloss's final word ends an English line (before punctuation)."""
    words = decode_gloss(gloss).split()
    if not words:
        return False
    final_word = re.sub(r"^[^\w]+|[^\w]+$", "", words[-1])
    if not final_word:
        return False
    matches = 0
    lines = text.splitlines()
    if not text.endswith(("\n", "\r")):
        lines = lines[:-1]
    for line in lines:
        content = re.sub(r"[,;:.!?—–\s]+$", "", line)
        if re.search(r"(?<!\w)" + re.escape(final_word) + r"$", content, re.I):
            matches += 1
    return matches == 1


def prior_initial_gloss_comma(
    text: str, previous_item: dict[str, str] | None
) -> str:
    """Find a comma after the previous gloss's last word in an initial clause.

    The previous gloss's first word must begin a verse line (verse start or
    immediately after a linefeed); its final word must then be followed by a
    comma on that same line.
    """
    if not previous_item:
        return ""
    prior_words = decode_gloss(previous_item.get("e", "")).split()
    if not prior_words:
        return ""
    first = re.sub(r"^[^\w]+|[^\w]+$", "", prior_words[0])
    last = re.sub(r"^[^\w]+|[^\w]+$", "", prior_words[-1])
    if not first or not last:
        return ""
    for line in text.splitlines():
        if not re.match(r"^\s*" + re.escape(first) + r"(?=\W|$)", line, re.I):
            continue
        first_match = re.search(r"(?<!\w)" + re.escape(first) + r"(?!\w)", line, re.I)
        if not first_match:
            continue
        last_match = re.search(
            r"(?<!\w)" + re.escape(last) + r"(?!\w)", line[first_match.end():], re.I
        )
        if not last_match:
            continue
        end = first_match.end() + last_match.end()
        if re.match(r"\s*,", line[end:]):
            return ","
    return ""


def analyze_boundary(
    text: str,
    item: dict[str, str],
    prefix_rows: list[dict[str, str]],
    previous_item: dict[str, str] | None,
    next_item: dict[str, str] | None,
    kind: str,
) -> str:
    gloss = decode_gloss(item.get("e", ""))
    if kind == "ZAQEF-QATAN":
        adjacent_reversal = reordered_adjacent_gloss_boundary(
            text, item, previous_item
        )
        if adjacent_reversal:
            boundary_span, mark = adjacent_reversal
            boundary_word = text[boundary_span[0]:boundary_span[1]]
            return (
                "PASS: reordered adjacent Hebrew glosses align through "
                f"'{boundary_word}' and punctuation follows ({mark})"
            )
        reordered_span = reordered_preceding_glosses_span(text, prefix_rows)
        if reordered_span:
            boundary_word = text[reordered_span[0]:reordered_span[1]]
            mark = punctuation_after(text, reordered_span[1])
            if mark:
                return (
                    "PASS: preceding Hebrew glosses all follow the marked gloss in "
                    f"English order; punctuation follows '{boundary_word}' ({mark})"
                )
    reordered = reordered_prefix_boundary(text, prefix_rows, kind)
    if reordered:
        boundary, represented = reordered
        aligned_word = text[boundary[0]:boundary[1]]
        if represented:
            return (
                f"PASS: reordered Hebrew prefix aligns through '{aligned_word}' and "
                f"the punctuation boundary is present"
            )
        if kind == "ATNAH":
            return f"CHECK LINE BREAK at reordered Hebrew-prefix end ('{aligned_word}')"
        return f"CHECK punctuation at reordered Hebrew-prefix end ('{aligned_word}')"

    noun_this_span = noun_this_boundary_span(text, item, previous_item)
    if noun_this_span:
        noun = text[noun_this_span[0]:noun_this_span[1]]
        if kind == "ATNAH":
            if line_break_after(text, noun_this_span[1]):
                return f"PASS: Hebrew noun + 'this' aligns to English 'this {noun}' before the atnah line break"
            return f"CHECK LINE BREAK after English noun following Hebrew 'this' ({noun})"
        if punctuation_after(text, noun_this_span[1]):
            return f"PASS: Hebrew noun + 'this' aligns through English noun '{noun}' and punctuation follows"
        return f"CHECK punctuation after English noun following Hebrew 'this' ({noun})"
    next_gloss = decode_gloss(next_item.get("e", "")) if next_item else ""
    span = repeated_gloss_boundary_span(text, gloss, next_gloss, kind)
    if not span:
        span = aligned_gloss_span(text, gloss, prefix_rows)
    ambiguous_gloss = len(gloss_spans(text, gloss)) > 1 and span is None
    trimmed_of = False
    inferred = False
    if not span:
        span = construct_trimmed_span(text, gloss)
        trimmed_of = span is not None
    if not span:
        if kind == "ATNAH" and final_gloss_word_before_newline(text, gloss):
            return f"PASS: final gloss word occurs immediately before the English line break ({gloss})"
        span = inferred_negated_span(text, item, previous_item)
        inferred = span is not None
    if not span:
        if ambiguous_gloss:
            return f"REVIEW: repeated gloss has no unique occurrence after prior Hebrew alignment ({gloss})"
        return f"REVIEW: gloss not located ({gloss or 'empty gloss'})"
    mark = punctuation_after(text, span[1])
    # English may reorder words inside the Hebrew-to-English alignment span.
    # Punctuation just before the next record's gloss can therefore represent
    # the boundary even when it does not follow this record's gloss.
    next_span = gloss_span(text, next_gloss, span[1]) if next_gloss else None
    before_next = punctuation_before(text, next_span[0]) if next_span else ""
    prior_comma = prior_initial_gloss_comma(text, previous_item)
    if prior_comma:
        prior_gloss = decode_gloss(previous_item.get("e", ""))
        return f"PASS: prior gloss begins the verse/line and its final word has a comma ({prior_gloss})"
    if kind == "ZAQEF-QATAN" and before_next:
        return (
            f"PASS: punctuation before next record's English gloss ({before_next}; "
            f"{gloss} → {next_gloss})"
        )
    if kind == "ATNAH":
        tail = text[span[1]:]
        # Newline must follow the matched phrase nearby; a newline elsewhere
        # in a long verse is not evidence that this boundary is represented.
        newline = re.search(r"\n", tail)
        local_break = newline is not None and newline.start() <= 45
        if not local_break:
            if final_gloss_word_before_newline(text, gloss):
                return f"PASS: final gloss word occurs immediately before the English line break ({gloss})"
            if "\n" in text:
                return f"CHECK LINE BREAK LOCATION: newline not near gloss ({gloss})"
            return f"CHECK LINE BREAK: no newline ({gloss})"
        if mark:
            if inferred:
                return f"PASS: final gloss word inferred after preceding 'not'; line break and punctuation present ({gloss})"
            return f"PASS: aligned gloss has nearby line break and punctuation ({mark}; {gloss})"
        if inferred:
            return f"PASS: final gloss word inferred after preceding 'not'; line break present, punctuation optional ({gloss})"
        return f"PASS: aligned gloss has nearby line break; punctuation is optional here ({gloss})"
    if mark:
        if trimmed_of:
            return f"PASS: gloss matched after trimming terminal 'of'; punctuation follows the matched phrase ({mark}; {gloss})"
        if inferred:
            return f"PASS: final gloss word inferred after preceding 'not'; punctuation present ({mark}; {gloss})"
        return f"PASS: aligned gloss has punctuation nearby ({mark}; {gloss})"
    if inferred:
        return f"CHECK punctuation at inferred final gloss word after preceding 'not' ({gloss})"
    if trimmed_of:
        return f"CHECK punctuation: matched after trimming terminal 'of', none follows ({gloss})"
    return f"CHECK punctuation: gloss located, none immediately after ({gloss})"


def build_report(items: list[dict[str, str]], checks_only: bool = False) -> str:
    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for item in items:
        groups[verse_key(item)].append(item)

    lines = [
        "PUNCTUATION REVIEW CANDIDATES",
        "Generated from Hebrew accent flags; this is a review aid, not an automatic correction.",
        "Exact gloss matching can miss English/Hebrew reorderings, inflections, or split phrases.",
        "",
    ]
    if checks_only:
        lines[0] = "PUNCTUATION REVIEW — CHECKS ONLY"
    for key in sorted(groups):
        rows = groups[key]
        text = next((r.get("e_t", "") for r in rows if r.get("e_t")), "")
        if not text:
            continue
        text = text.replace("\\n", "\n").strip()
        boundaries = []
        for index, item in enumerate(rows):
            previous_item = rows[index - 1] if index else None
            next_item = rows[index + 1] if index + 1 < len(rows) else None
            if item.get("atnah") == "1":
                boundaries.append((index, item, previous_item, next_item, "ATNAH"))
            if item.get("z_q") == "1":
                boundaries.append((index, item, previous_item, next_item, "ZAQEF-QATAN"))
        if not boundaries:
            continue
        entries = []
        for index, item, previous_item, next_item, kind in boundaries:
            atnah_index = next(
                (i for i, row in enumerate(rows) if row.get("atnah") == "1"), None
            )
            prefix_rows = rows[: index + 1]
            analysis_text = text
            if "\n" in text and atnah_index is not None:
                first_half, second_half = text.split("\n", 1)
                if kind == "ATNAH":
                    analysis_text = first_half + "\n"
                elif index <= atnah_index:
                    analysis_text = first_half
                else:
                    analysis_text = second_half
                    prefix_rows = rows[atnah_index + 1:index + 1]
            result = analyze_boundary(
                analysis_text, item, prefix_rows,
                previous_item, next_item, kind
            )
            if not checks_only or result.startswith(("CHECK", "REVIEW")):
                hebrew_word = html.unescape(item.get("h", "")).strip()
                accent_name = "zaqef-qatan" if kind == "ZAQEF-QATAN" else "atnah"
                entries.append(
                    f"  {hebrew_word} ({accent_name}, word {item['k'].split('_')[-1]}) "
                    f"[{decode_gloss(item.get('e', ''))}]: {result}"
                )
        if checks_only and not entries:
            continue
        lines.append(f"{key.replace('_', ':')}  {text.replace(chr(10), ' / ')}")
        lines.extend(entries)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="JSON export with items list")
    parser.add_argument("output", type=Path, help="Plain-text report path")
    parser.add_argument(
        "--checks-only",
        action="store_true",
        help="include only CHECK/REVIEW boundary rows, retaining their verse text",
    )
    args = parser.parse_args()
    items = read_items(args.input)
    report = build_report(items, checks_only=args.checks_only)
    args.output.write_text(report, encoding="utf-8")
    print(f"Reviewed {len(items):,} word records; wrote {args.output} ({len(report):,} characters).")


if __name__ == "__main__":
    main()
