#!/usr/bin/env python3
"""
check_zaqef_atnah.py (Version 25 - Single Missing Comma & Tail Noise Fix)

Audits concordant translation files (translation.json / translation.txt) against
Masoretic Hebrew cantillation accents (interlin.json / interlin.txt):
  1. Atnah (\u0591 / &#1425;): Verifies presence of caesura linefeed (&#119059; / 𝄓 / \n),
     EXCEPT when Atnah occurs on the last word of the verse.
  2. Zaqef-Qatan (\u0594 / &#1428;): Verifies pause punctuation (, . ; : ? !) on every
     Zaqef-Qatan target word in English First & Second Halves.

Key updates:
  - Strips trailing boundary punctuation before counting internal breaks.
  - Correctly identifies expected = 1, found = 0 single missing comma cases (e.g., Lev 27:11).
  - Automatically inserts commas after ALL unpunctuated Zaqef target words in suggested_english.
  - Outputs a 6-column CSV (verse, issue, expected, found, original_english, suggested_english).
"""

import csv
import json
import html
import re
import sys
from pathlib import Path

ATNAH_UNICODE = "\u0591"      # ֑
ZAQEF_UNICODE = "\u0594"     # ֔

OUTPUT_CSV = Path("zaqef_atnah_review_queue.csv")

DEFAULT_BOOK_MAP = {
    "GENESIS": "01", "EXODUS": "02", "LEVITICUS": "03", "NUMBERS": "04", "DEUTERONOMY": "05",
    "JOSHUA": "06", "JUDGES": "07", "1_SAMUEL": "08", "2_SAMUEL": "09", "1_KINGS": "10",
    "2_KINGS": "11", "ISAIAH": "12", "JEREMIAH": "13", "EZEKIEL": "14", "HOSEA": "15",
    "JOEL": "16", "AMOS": "17", "OBADIAH": "18", "JONAH": "19", "MICAH": "20",
    "NAHUM": "21", "HABAKKUK": "22", "ZEPHANIAH": "23", "HAGGAI": "24", "ZECHARIAH": "25",
    "MALACHI": "26", "PSALMS": "27", "PROVERBS": "28", "JOB": "29", "SONG": "30",
    "RUTH": "31", "LAMENTATIONS": "32", "QOHELET": "33", "ESTHER": "34", "DANIEL": "35",
    "EZRA": "36", "NEHEMIAH": "37", "1_CHRONICLES": "38", "2_CHRONICLES": "39",
    "1 SAMUEL": "08", "2 SAMUEL": "09", "1 KINGS": "10", "2 KINGS": "11",
    "1 CHRONICLES": "38", "2 CHRONICLES": "39"
}


def unescape_and_clean(text):
    return html.unescape(text) if text else ""


def clean_gloss(e):
    return re.sub(r"[^\w\s\']", "", e).strip()


def clean_tail_noise(text):
    """Strips trailing boundary punctuation (, . ; : ? !) and caesura entities."""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"&#119059;|𝄓|\\n|\n|<br\s*/?>", "", t).strip()
    return re.sub(r"[,.;:?!\"'\s]+$", "", t).strip()


def count_internal_breaks(text):
    """Counts internal pause punctuation (, . ; : ? !) after stripping tail noise."""
    clean_text = clean_tail_noise(text)
    return sum(clean_text.count(p) for p in [",", ".", ";", ":", "?", "!"])


def extract_items(data):
    """Safely extracts items array from Oracle ORDS, plain dict, or list structures."""
    if not data:
        return []
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            return data["items"]
        if "results" in data:
            res = data["results"]
            if isinstance(res, list) and len(res) > 0:
                items = []
                for r in res:
                    if isinstance(r, dict) and "items" in r:
                        items.extend(r["items"])
                    elif isinstance(r, dict):
                        items.append(r)
                return items if items else res
            elif isinstance(res, dict):
                if "items" in res:
                    return res["items"]
                return [res]
    elif isinstance(data, list):
        items = []
        for x in data:
            if isinstance(x, dict):
                if "items" in x:
                    items.extend(x["items"])
                elif any(k in x for k in ["k", "eng_text", "h", "book_cd", "b", "BOOK_CD"]):
                    items.append(x)
        return items if items else data
    return []


def load_book_sequence_map():
    """Dynamically loads book sequence mappings from bookseq.json or bookseq.txt."""
    for filename in ["bookseq.json", "bookseq.txt"]:
        path = Path(filename)
        if path.exists():
            try:
                with path.open("r", encoding="utf-8-sig", errors="ignore") as f:
                    data = json.load(f)
                items = extract_items(data)
                seq_map = {}
                for item in items:
                    cd = item.get("book_cd") or item.get("BOOK_CD") or item.get("b") or item.get("book")
                    seq = item.get("book_seq_no") or item.get("BOOK_SEQ_NO") or item.get("seq")
                    if cd and seq is not None:
                        norm_cd = str(cd).strip().upper().replace(" ", "_")
                        seq_map[norm_cd] = f"{int(seq):02d}"
                        seq_map[str(cd).strip().upper()] = f"{int(seq):02d}"
                if seq_map:
                    print(f"📖 Loaded {len(seq_map)} book sequence mappings from {filename}.")
                    return seq_map
            except Exception as e:
                print(f"Warning: Could not parse {filename}: {e}")
    print("📖 Using default 39-book sequence mapping.")
    return DEFAULT_BOOK_MAP


def resolve_non_empty_file(base_name, explicit_arg=None):
    """Locates and verifies non-empty .json or .txt dataset in working directory."""
    if explicit_arg:
        p = Path(explicit_arg)
        if p.exists() and p.stat().st_size > 5:
            return p

    candidates = [
        Path(f"{base_name}.json"),
        Path(f"{base_name}.txt"),
        Path(f"{base_name.upper()}.json"),
        Path(f"{base_name.upper()}.txt"),
    ]

    for p in candidates:
        if p.exists() and p.stat().st_size > 10:
            try:
                with p.open("r", encoding="utf-8-sig", errors="ignore") as f:
                    data = json.load(f)
                    items = extract_items(data)
                    if items:
                        return p
            except Exception:
                pass

    for p in candidates:
        if p.exists():
            return p
    return None


def parse_verse_record(t, book_map):
    """Extracts verse key and English text from translation.json record."""
    raw_b = t.get("book_cd") or t.get("BOOK_CD") or t.get("book_seq_no") or t.get("BOOK_SEQ_NO") or t.get("book") or t.get("b") or t.get("b_seq") or "1"
    
    if isinstance(raw_b, (int, float)):
        raw_b_str = f"{int(raw_b):02d}"
    else:
        raw_b_str = str(raw_b).strip().upper().replace(" ", "_")

    if raw_b_str.isdigit():
        b_seq = f"{int(raw_b_str):02d}"
    else:
        b_seq = book_map.get(raw_b_str, book_map.get(str(raw_b).strip().upper(), "01"))
        if not str(b_seq).isdigit():
            b_seq = "01"

    raw_c = t.get("chapter_cd") or t.get("CHAPTER_CD") or t.get("chapter") or t.get("c") or 1
    c_num = int(str(raw_c).strip()) if str(raw_c).strip().isdigit() else 1

    raw_v = t.get("verse_cd") or t.get("VERSE_CD") or t.get("verse") or t.get("v") or 1
    v_num = int(str(raw_v).strip()) if str(raw_v).strip().isdigit() else 1

    v_key = f"{b_seq}_{c_num:03d}_{v_num:03d}"
    eng = t.get("eng_text") or t.get("ENG_TEXT") or t.get("english") or t.get("text") or t.get("e") or ""
    return v_key, eng


def suggest_half_commas_all(half_text, half_words):
    """Inserts commas after ALL Zaqef-Qatan target words lacking punctuation in a half-verse."""
    modified = half_text
    zaqef_words = [w for w in half_words if ZAQEF_UNICODE in w["h"]]
    for zw in zaqef_words:
        ze = clean_gloss(zw["e"])
        if ze:
            pattern = re.compile(r"\b(" + re.escape(ze) + r")(?![\s]*[,.;:?!])\b", re.IGNORECASE)
            if pattern.search(modified):
                modified = pattern.sub(r"\1,", modified, count=1)
    return re.sub(r"\s+", " ", modified).strip()


def audit_pipeline():
    arg_i = sys.argv[1] if len(sys.argv) > 1 else None
    arg_t = sys.argv[2] if len(sys.argv) > 2 else None

    book_map = load_book_sequence_map()
    rev_book_map = {v: k.replace("_", " ") for k, v in book_map.items()}

    interlin_path = resolve_non_empty_file("interlin", arg_i)
    trans_path = resolve_non_empty_file("translation", arg_t)

    if not interlin_path:
        print("❌ Error: Could not find non-empty interlin.json or interlin.txt.")
        return

    print(f"📖 Loading interlinear Hebrew accents from: {interlin_path.name}")
    with interlin_path.open("r", encoding="utf-8-sig", errors="ignore") as f:
        interlin_raw = json.load(f)

    i_items = extract_items(interlin_raw)

    interlin_verses = {}
    for item in i_items:
        k = item.get("k") or item.get("K") or item.get("key") or ""
        if not k:
            continue
        parts = k.split("_")
        if len(parts) < 3:
            continue

        raw_b = parts[0]
        if raw_b.isdigit():
            b_seq = f"{int(raw_b):02d}"
        else:
            b_seq = book_map.get(raw_b.upper(), "01")

        c_num = int(parts[1]) if parts[1].isdigit() else 1
        v_num = int(parts[2]) if parts[2].isdigit() else 1
        w_seq = int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0

        v_key = f"{b_seq}_{c_num:03d}_{v_num:03d}"

        if v_key not in interlin_verses:
            interlin_verses[v_key] = {
                "book_seq": b_seq,
                "chapter": c_num,
                "verse": v_num,
                "words": []
            }
        interlin_verses[v_key]["words"].append({
            "w_seq": w_seq,
            "h": unescape_and_clean(item.get("h", "")),
            "e": item.get("e", "").strip()
        })

    print(f"   -> Loaded {len(i_items)} word entries across {len(interlin_verses)} verses.")

    translations = {}
    if trans_path:
        print(f"📖 Loading verse translations from: {trans_path.name}")
        with trans_path.open("r", encoding="utf-8-sig", errors="ignore") as f:
            trans_raw = json.load(f)

        t_items = extract_items(trans_raw)

        for t in t_items:
            vk, eng = parse_verse_record(t, book_map)
            translations[vk] = eng

        print(f"   -> Loaded {len(translations)} verse translation lines.")
        matched_count = sum(1 for vk in interlin_verses if vk in translations)
        print(f"   -> Successfully matched {matched_count} verses between interlinear and translation files.")

    flagged_rows = []

    for v_key, v_data in interlin_verses.items():
        c_num = v_data["chapter"]
        v_num = v_data["verse"]
        b_seq = v_data["book_seq"]
        b_name = rev_book_map.get(b_seq, f"Book_{b_seq}")
        verse_label = f"{b_name} {c_num}:{v_num}"

        words = sorted(v_data["words"], key=lambda x: x["w_seq"])
        eng_verse_raw = translations.get(v_key)

        if not eng_verse_raw:
            continue

        eng_clean = unescape_and_clean(eng_verse_raw)

        # Detect Atnah in Hebrew words
        atnah_idx = next((i for i, w in enumerate(words) if ATNAH_UNICODE in w["h"]), -1)
        has_atnah = (atnah_idx != -1)
        is_atnah_on_last_word = (has_atnah and atnah_idx == len(words) - 1)

        # Detect caesura / linefeed in English translation (handles &#119059;, 𝄓, \n, <br>)
        has_linefeed = any(m in eng_verse_raw or m in eng_clean for m in ["&#119059;", "𝄓", "\\n", "\n", "<br>"])

        # 1. ATNAH LINEFEED AUDIT (Skip if Atnah is on the last word)
        if has_atnah and not is_atnah_on_last_word and not has_linefeed:
            flagged_rows.append({
                "verse": verse_label,
                "issue": "MISSING_ATNAH_LINEFEED",
                "E": 1,
                "F": 0,
                "original_english": eng_clean,
                "suggested_english": eng_clean
            })

        # Split English verse at caesura symbol (&#119059; / 𝄓 / \n)
        if has_linefeed:
            parts_e = re.split(r"&#119059;|𝄓|\\n|\n|<br\s*/?>", eng_clean)
            eng_h1 = parts_e[0].strip() if len(parts_e) > 0 else eng_clean.strip()
            eng_h2 = parts_e[1].strip() if len(parts_e) > 1 else ""
        else:
            eng_h1 = eng_clean.strip()
            eng_h2 = ""

        # 2. HALF-VERSE ZAQEF-QATAN COMMA/PAUSE AUDIT
        first_half_heb = words[:atnah_idx + 1] if has_atnah else words
        second_half_heb = words[atnah_idx + 1:] if (has_atnah and not is_atnah_on_last_word) else []

        z1_count = sum(1 for w in first_half_heb if ZAQEF_UNICODE in w["h"])
        z2_count = sum(1 for w in second_half_heb if ZAQEF_UNICODE in w["h"])

        p1_count = count_internal_breaks(eng_h1)
        p2_count = count_internal_breaks(eng_h2) if eng_h2 else 0

        # STRICT CONDITION: Only flag if found < expected (p_count < z_count)
        if z1_count > 0 and p1_count < z1_count:
            sugg_h1 = suggest_half_commas_all(eng_h1, first_half_heb)
            flagged_rows.append({
                "verse": verse_label,
                "issue": "FIRST_HALF",
                "E": z1_count,
                "F": p1_count,
#                "original_english": eng_h1,
                "suggested_english": sugg_h1
            })

        if z2_count > 0 and eng_h2 and p2_count < z2_count:
            sugg_h2 = suggest_half_commas_all(eng_h2, second_half_heb)
            flagged_rows.append({
                "verse": verse_label,
                "issue": "SECOND_HALF",
                "E": z2_count,
                "F": p2_count,
#                "original_english": eng_h2,
                "suggested_english": sugg_h2
            })

    print(f"\n📊 Audit Complete!")
    print(f"   - Total verses scanned: {len(interlin_verses)}")
    print(f"   - Total flagged issue records: {len(flagged_rows)}")

    # Write minimal CSV report
    with OUTPUT_CSV.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["verse", "issue", "E", "F", "suggested_english"])
        writer.writeheader()
        for row in flagged_rows:
            writer.writerow(row)

    print(f"\nOutput written to: {OUTPUT_CSV}")


if __name__ == "__main__":
    audit_pipeline()
