"""Build a compact verse-level accent sequence index from chapter interlinear files."""

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CHAPTERS = ROOT / "chapters"
DICTIONARY_PATH = ROOT / "hebrew_accent_dictionary.json"
OUTPUT_PATH = ROOT / "accent_sequence_index.json"
BOOK_NUMBERS = {
    "GENESIS": 1, "EXODUS": 2, "LEVITICUS": 3, "NUMBERS": 4,
    "DEUTERONOMY": 5, "JOSHUA": 6, "JUDGES": 7, "1_SAMUEL": 8,
    "2_SAMUEL": 9, "1_KINGS": 10, "2_KINGS": 11, "ISAIAH": 12,
    "JEREMIAH": 13, "EZEKIEL": 14, "HOSEA": 15, "JOEL": 16,
    "AMOS": 17, "OBADIAH": 18, "JONAH": 19, "MICAH": 20,
    "NAHUM": 21, "HABAKKUK": 22, "ZEPHANIAH": 23, "HAGGAI": 24,
    "ZECHARIAH": 25, "MALACHI": 26, "PSALMS": 27, "PROVERBS": 28,
    "JOB": 29, "SONG": 30, "RUTH": 31, "LAMENTATIONS": 32,
    "QOHELET": 33, "ESTHER": 34, "DANIEL": 35, "EZRA": 36,
    "NEHEMIAH": 37, "1_CHRONICLES": 38, "2_CHRONICLES": 39,
}
ACCENT_RANGE = range(0x0591, 0x05B0)


def items_from_file(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "results" in data:
            return [item for result in data["results"] for item in result.get("items", [])]
        return data.get("items", data.get("rows", []))
    return []


def main():
    dictionary = json.loads(DICTIONARY_PATH.read_text(encoding="utf-8"))
    accents = {}
    for entry in dictionary.values():
        decimal = int(entry.get("decimal", 0))
        if decimal in ACCENT_RANGE and entry.get("name_translit"):
            accents[str(decimal)] = {
                "n": entry["name_translit"],
                "h": entry.get("name_hebrew", ""),
                "c": entry.get("category", ""),
            }

    verses = {}
    for path in sorted(CHAPTERS.glob("*/*.json")):
        book_code = path.parent.name
        book_number = BOOK_NUMBERS.get(book_code)
        if not book_number:
            continue
        for row in items_from_file(path):
            key = str(row.get("k", row.get("K", "")))
            match = re.fullmatch(r"(\d+)_(\d+)_(\d+)_(\d+)", key)
            if not match:
                continue
            book, chapter, verse, word = map(int, match.groups())
            if book != book_number:
                continue
            hebrew = html.unescape(str(row.get("h", row.get("H", ""))))
            marks = [str(ord(char)) for char in hebrew if ord(char) in ACCENT_RANGE and str(ord(char)) in accents]
            if not marks:
                continue
            verse_key = (book, chapter, verse)
            verses.setdefault(verse_key, []).append([word, hebrew, marks])

    records = []
    for (book, chapter, verse), words in sorted(verses.items()):
        words.sort(key=lambda item: item[0])
        records.append([book, chapter, verse, words])

    index = {"books": {str(number): name.replace("_", " ").title() for name, number in BOOK_NUMBERS.items()},
             "accents": accents, "verses": records}
    OUTPUT_PATH.write_text(json.dumps(index, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"Wrote {len(records):,} verses with accent sequences to {OUTPUT_PATH.name} ({OUTPUT_PATH.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
