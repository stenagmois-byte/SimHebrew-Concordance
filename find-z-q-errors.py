"""Build a review queue for punctuation associated with zaqef-qatan.

Reads translation.json and ornament_index.json from the repository root. It
does not edit either source. Running it creates a CSV, JSONL, and text report.
"""

import csv
import json
import re
import sys
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ZAQEF_QATAN = "\u0594"
ATNAH = "\u0591"
CAESURA_ENTITY = "&#119059;"
OUTPUT_CSV = Path("zaqef_review_queue.csv")
OUTPUT_JSONL = Path("zaqef_review_queue.jsonl")
OUTPUT_REPORT = Path("zaqef_review_report.txt")

SCROLLS = {
    "GENESIS", "EXODUS", "LEVITICUS", "NUMBERS", "DEUTERONOMY",
    "HOSEA", "JOEL", "AMOS", "OBADIAH", "JONAH", "MICAH", "NAHUM",
    "HABAKKUK", "ZEPHANIAH", "HAGGAI", "ZECHARIAH", "MALACHI", "SONG",
    "RUTH", "LAMENTATIONS", "QOHELET", "ESTHER", "PSALMS", "PROVERBS",
    "JOB", "JOSHUA", "JUDGES", "1_SAMUEL", "2_SAMUEL", "1_KINGS",
    "2_KINGS", "ISAIAH", "JEREMIAH", "EZEKIEL", "DANIEL", "EZRA",
    "NEHEMIAH", "1_CHRONICLES", "2_CHRONICLES",
}


def load_data():
    with open("translation.json", encoding="utf-8") as source:
        translation_data = json.load(source)
    with open("ornament_index.json", encoding="utf-8") as source:
        ornament_data = json.load(source)
    return translation_data, ornament_data


def extract_items(translation_data):
    results = translation_data.get("results", [])
    if isinstance(results, list):
        for block in results:
            if isinstance(block, dict) and "items" in block:
                return block["items"]
    if isinstance(results, dict):
        return results.get("items", [])
    return translation_data.get("items", [])


def verse_key(book, chapter, verse):
    return f"{book}_{str(chapter).zfill(3)}_{str(verse).zfill(3)}"


def split_atnah_words(hebrew_text):
    """Split by words, retaining the atnah word as the end of the first half."""
    words = hebrew_text.split()
    for index, word in enumerate(words):
        if ATNAH in word:
            return words[: index + 1], words[index + 1 :], index + 1
    return words, [], -1


def accented_words(words):
    return [word for word in words if ZAQEF_QATAN in word]


def build_split_zaqef_map(ornament_data):
    zaqef_map = {}
    for verses in ornament_data.get("zaqef-qatan", {}).values():
        for item in verses:
            book = str(item.get("b", "")).strip().upper().replace(" ", "_")
            if book not in SCROLLS:
                continue
            key = verse_key(book, item.get("c", ""), item.get("v", ""))
            first_words, second_words, atnah_word_idx = split_atnah_words(
                item.get("t", "").strip()
            )
            candidate = {
                "first_half": sum(ZAQEF_QATAN in word for word in first_words),
                "second_half": sum(ZAQEF_QATAN in word for word in second_words),
                "first_half_words": accented_words(first_words),
                "second_half_words": accented_words(second_words),
                "heb_total_words": len(first_words) + len(second_words),
                "atnah_word_idx": atnah_word_idx,
            }
            # A verse can occur in several ornament categories. Keep the richest
            # complete record, rather than merging halves from different records.
            previous = zaqef_map.get(key)
            if previous is None or (
                candidate["first_half"] + candidate["second_half"]
                > previous["first_half"] + previous["second_half"]
            ):
                zaqef_map[key] = candidate
    return zaqef_map


def clean_tail_noise(text):
    text = re.sub(r"[.;:?]\s*[PSRW]\s*$", "", text.strip())
    return re.sub(r"[.;:?\"'!]+$", "", text.strip())


def break_count(text):
    commas = text.count(",")
    strong_marks = len(re.findall(r"[.;:?](?!\s*𝄓)", text))
    return commas + strong_marks


def inspect_half(label, english, expected, target_words):
    found = break_count(clean_tail_noise(english))
    return {
        "label": label,
        "expected": expected,
        "found": found,
        "shortfall": max(expected - found, 0),
        "target_words": target_words,
    }


def priority_for(issues, first_half, second_half):
    shortfall = max(first_half["shortfall"], second_half["shortfall"])
    if "MISSING_CAESURA_MARKER" in issues:
        return 1
    if shortfall >= 3:
        return 2
    if shortfall == 2:
        return 3
    if shortfall == 1:
        return 4
    return 5  # caesura alignment only


def build_review_queue():
    translation_data, ornament_data = load_data()
    zaqef_map = build_split_zaqef_map(ornament_data)
    queue = []
    evaluated = matched = 0

    for item in extract_items(translation_data):
        book = str(item.get("book_cd", "")).strip().upper().replace(" ", "_")
        if book not in SCROLLS or item.get("poetry") == "1":
            continue
        evaluated += 1
        chapter = str(item.get("chapter_cd", "")).strip()
        verse = str(item.get("verse_cd", "")).strip()
        profile = zaqef_map.get(verse_key(book, chapter, verse))
        if profile is None:
            continue
        matched += 1

        english = item.get("eng_text", "").strip()
        has_atnah = item.get("has_atnah") == "1"
        issues = []
        caesura_variance = None
        if has_atnah and CAESURA_ENTITY not in english:
            issues.append("MISSING_CAESURA_MARKER")
            first_english, second_english = english, ""
        elif has_atnah:
            first_english, second_english = english.split(CAESURA_ENTITY, 1)
            first_english = re.sub(r",\s*$", "", first_english.strip())
            english_words = english.split()
            caesura_index = next(
                (index + 1 for index, word in enumerate(english_words)
                 if CAESURA_ENTITY in word),
                -1,
            )
            if profile["atnah_word_idx"] != -1 and profile["heb_total_words"]:
                hebrew_ratio = profile["atnah_word_idx"] / profile["heb_total_words"]
                english_ratio = caesura_index / len(english_words)
                caesura_variance = abs(hebrew_ratio - english_ratio)
                if caesura_variance > 0.20:
                    issues.append("MISPLACED_CAESURA_BOUNDARY")
        else:
            first_english, second_english = english, ""

        first_half = inspect_half(
            "first", first_english, profile["first_half"], profile["first_half_words"]
        )
        second_half = inspect_half(
            "second", second_english, profile["second_half"], profile["second_half_words"]
        )
        if first_half["shortfall"]:
            issues.append("INSUFFICIENT_ZAQEF_FIRST_HALF")
        if has_atnah and second_half["shortfall"]:
            issues.append("INSUFFICIENT_ZAQEF_SECOND_HALF")
        if not issues:
            continue

        display_book = book.replace("_", " ")
        queue.append({
            "priority": priority_for(issues, first_half, second_half),
            "verse": f"{display_book} {int(chapter)}:{int(verse)}",
            "book": display_book,
            "chapter": int(chapter),
            "verse_number": int(verse),
            "issues": issues,
            "max_shortfall": max(first_half["shortfall"], second_half["shortfall"]),
            "caesura_variance": caesura_variance,
            "first_half": first_half,
            "second_half": second_half,
            "english_text": english,
        })
    queue.sort(key=lambda row: (
        row["priority"], -row["max_shortfall"], row["book"],
        row["chapter"], row["verse_number"],
    ))
    return queue, evaluated, matched


def choose_output_paths():
    """Avoid replacing a queue currently open in a spreadsheet application."""
    try:
        with OUTPUT_CSV.open("a", encoding="utf-8"):
            pass
        return OUTPUT_CSV, OUTPUT_JSONL, OUTPUT_REPORT
    except PermissionError:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return (
            Path(f"zaqef_review_queue_{stamp}.csv"),
            Path(f"zaqef_review_queue_{stamp}.jsonl"),
            Path(f"zaqef_review_report_{stamp}.txt"),
        )


def write_outputs(queue, evaluated, matched, output_csv, output_jsonl, output_report):
    fields = [
        "priority", "verse", "issues", "max_shortfall", "first_expected",
        "first_found", "first_shortfall", "first_target_words", "second_expected",
        "second_found", "second_shortfall", "second_target_words",
        "caesura_variance", "english_text",
    ]
    with output_csv.open("w", newline="", encoding="utf-8-sig") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        for row in queue:
            writer.writerow({
                "priority": row["priority"], "verse": row["verse"],
                "issues": "; ".join(row["issues"]), "max_shortfall": row["max_shortfall"],
                "first_expected": row["first_half"]["expected"],
                "first_found": row["first_half"]["found"],
                "first_shortfall": row["first_half"]["shortfall"],
                "first_target_words": " | ".join(row["first_half"]["target_words"]),
                "second_expected": row["second_half"]["expected"],
                "second_found": row["second_half"]["found"],
                "second_shortfall": row["second_half"]["shortfall"],
                "second_target_words": " | ".join(row["second_half"]["target_words"]),
                "caesura_variance": "" if row["caesura_variance"] is None else f"{row['caesura_variance']:.3f}",
                "english_text": row["english_text"],
            })
    with output_jsonl.open("w", encoding="utf-8") as output:
        for row in queue:
            output.write(json.dumps(row, ensure_ascii=False) + "\n")
    with output_report.open("w", encoding="utf-8") as output:
        output.write("--- ZAQEF-QATAN REVIEW QUEUE ---\n")
        output.write(f"Non-poetry verses evaluated: {evaluated}\n")
        output.write(f"Verses matched to zaqef index: {matched}\n")
        output.write(f"Unique verses requiring review: {len(queue)}\n\n")
        for row in queue:
            output.write(f"[P{row['priority']}] {row['verse']} — {', '.join(row['issues'])}\n")
            for half in (row["first_half"], row["second_half"]):
                if half["expected"]:
                    output.write(
                        f"  {half['label'].title()} half: expected {half['expected']}; "
                        f"found {half['found']}; shortfall {half['shortfall']}. "
                        f"Targets: {' | '.join(half['target_words'])}\n"
                    )
            if row["caesura_variance"] is not None:
                output.write(f"  Caesura proportional variance: {row['caesura_variance']:.3f}\n")
            output.write(f"  Translation: {row['english_text']}\n\n")


if __name__ == "__main__":
    try:
        review_queue, evaluated_count, matched_count = build_review_queue()
        output_csv, output_jsonl, output_report = choose_output_paths()
        write_outputs(
            review_queue, evaluated_count, matched_count,
            output_csv, output_jsonl, output_report,
        )
        print(f"Created {len(review_queue)} unique review entries.")
        print(f"  {output_csv}")
        print(f"  {output_jsonl}")
        print(f"  {output_report}")
    except Exception as error:
        print(f"Execution failed: {error}")
        raise
