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


PUNCT_RE = re.compile(r"[,;:.!?—–]$", re.UNICODE)


def read_items(path: Path) -> list[dict[str, str]]:
    raw = path.read_text(encoding="utf-8-sig")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # The supplied export is a JSON object fragment beginning at "items":.
        data = json.loads("{" + raw + "}")
    items = data["items"] if isinstance(data, dict) else data
    if not isinstance(items, list):
        raise ValueError("Expected a top-level items list")
    return items


def verse_key(item: dict[str, str]) -> str:
    return "_".join(item["k"].split("_")[:3])


def decode_gloss(text: str) -> str:
    return html.unescape(text or "").strip()


def gloss_span(text: str, gloss: str, start: int = 0) -> tuple[int, int] | None:
    """Find an exact, case-insensitive gloss phrase in English verse text."""
    gloss = decode_gloss(gloss)
    if not gloss:
        return None
    # Normalize whitespace but preserve the original span for context checks.
    words = [re.escape(w) for w in gloss.split()]
    if not words:
        return None
    match = re.search(r"(?<!\w)" + r"\s+".join(words) + r"(?!\w)", text[start:], re.I)
    if match:
        return start + match.start(), start + match.end()
    return None


def construct_trimmed_span(text: str, gloss: str) -> tuple[int, int] | None:
    """Match a construct gloss after trimming a terminal `of` only."""
    gloss = decode_gloss(gloss)
    if not gloss.casefold().endswith(" of"):
        return None
    trimmed = gloss[:-3].rstrip()
    return gloss_span(text, trimmed) if trimmed else None


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
    for line in text.splitlines()[:-1]:
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
    previous_item: dict[str, str] | None,
    next_item: dict[str, str] | None,
    kind: str,
) -> str:
    gloss = decode_gloss(item.get("e", ""))
    span = gloss_span(text, gloss)
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
        return f"REVIEW: gloss not located ({gloss or 'empty gloss'})"
    mark = punctuation_after(text, span[1])
    # English may reorder words inside the Hebrew-to-English alignment span.
    # Punctuation just before the next record's gloss can therefore represent
    # the boundary even when it does not follow this record's gloss.
    next_gloss = decode_gloss(next_item.get("e", "")) if next_item else ""
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
                boundaries.append((item, previous_item, next_item, "ATNAH"))
            if item.get("z_q") == "1":
                boundaries.append((item, previous_item, next_item, "ZAQEF-QATAN"))
        if not boundaries:
            continue
        entries = []
        for item, previous_item, next_item, kind in boundaries:
            result = analyze_boundary(text, item, previous_item, next_item, kind)
            if not checks_only or result.startswith(("CHECK", "REVIEW")):
                entries.append(
                    f"  {kind} {item['k'].split('_')[-1]} "
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
