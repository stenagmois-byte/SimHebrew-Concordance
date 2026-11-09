import os
import json
import html
from collections import defaultdict

# 🏛️ Exact 18 Volume Subdirectories mapped to standard Book Codes
BOOK_VOLUME_MAP = {
    "GENESIS": "Genesis",
    "EXODUS": "Exodus",
    "LEVITICUS": "Leviticus",
    "NUMBERS": "Numbers",
    "DEUTERONOMY": "Deuteronomy",
    "JOSHUA": "Joshua-Judges",
    "JUDGES": "Joshua-Judges",
    "1_SAMUEL": "Samuel",
    "2_SAMUEL": "Samuel",
    "1_KINGS": "Kings",
    "2_KINGS": "Kings",
    "ISAIAH": "Isaiah",
    "JEREMIAH": "Jeremiah",
    "EZEKIEL": "Ezekiel",
    "HOSEA": "The Twelve",
    "JOEL": "The Twelve",
    "AMOS": "The Twelve",
    "OBADIAH": "The Twelve",
    "JONAH": "The Twelve",
    "MICAH": "The Twelve",
    "NAHUM": "The Twelve",
    "HABAKKUK": "The Twelve",
    "ZEPHANIAH": "The Twelve",
    "HAGGAI": "The Twelve",
    "ZECHARIAH": "The Twelve",
    "MALACHI": "The Twelve",
    "PSALMS": "The Psalms",
    "PROVERBS": "Proverbs",
    "JOB": "Job",
    "SONG": "The Five Scrolls",
    "RUTH": "The Five Scrolls",
    "LAMENTATIONS": "The Five Scrolls",
    "QOHELET": "The Five Scrolls",
    "ESTHER": "The Five Scrolls",
    "DANIEL": "Daniel-Ezra-Nehemiah",
    "EZRA": "Daniel-Ezra-Nehemiah",
    "NEHEMIAH": "Daniel-Ezra-Nehemiah",
    "1_CHRONICLES": "Chronicles",
    "2_CHRONICLES": "Chronicles"
}

def split_master_syllables(master_file="syllables_master.json", output_base_dir="musicscores"):
    if not os.path.exists(master_file):
        print(f"❌ Error: Master export file '{master_file}' not found.")
        return

    print(f"📂 Loading master 720k syllable export from '{master_file}'...")
    with open(master_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)

    columns_def = None
    items = []

    if isinstance(raw_data, dict) and "results" in raw_data:
        res_list = raw_data["results"]
        if isinstance(res_list, list) and len(res_list) > 0:
            columns_def = res_list[0].get("columns")
            items = res_list[0].get("items", [])
    elif isinstance(raw_data, list):
        items = raw_data

    # Fallback to standard 12-column Oracle definition if header is missing
    if not columns_def:
        columns_def = [
            {"name":"BOOK_CD","type":"VARCHAR2"}, {"name":"BOOK_SEQ_NO","type":"NUMBER"},
            {"name":"CHAPTER_CD","type":"VARCHAR2"}, {"name":"VERSE_CD","type":"VARCHAR2"},
            {"name":"MEASURE_NO","type":"NUMBER"}, {"name":"XML_SEQ","type":"NUMBER"},
            {"name":"LYRIC_SYLL","type":"VARCHAR2"}, {"name":"SYLL_NOTE","type":"VARCHAR2"},
            {"name":"ORNAMENT_NAME","type":"VARCHAR2"}, {"name":"ORNAMENT","type":"VARCHAR2"},
            {"name":"POETRY","type":"VARCHAR2"}, {"name":"HEB_TEXT","type":"VARCHAR2"}
        ]

    print(f"📊 Loaded {len(items)} syllable records.")

    # 1. UNESCAPE HEBREW ENTITIES IN HEB_TEXT
    converted_count = 0
    for row in items:
        if isinstance(row, dict):
            heb_key = 'heb_text' if 'heb_text' in row else ('HEB_TEXT' if 'HEB_TEXT' in row else None)
            if heb_key and row[heb_key]:
                row[heb_key] = html.unescape(str(row[heb_key]))
                converted_count += 1

    print(f"✨ Converted Hebrew entities across {converted_count} records.")

    # 2. GROUP RECORDS BY (BOOK_CODE, CHAPTER)
    grouped = defaultdict(list)
    for row in items:
        if not isinstance(row, dict): continue
        
        raw_b_cd = str(row.get('book_cd', row.get('BOOK_CD', ''))).strip().upper()
        clean_b_cd = raw_b_cd.replace(' ', '_')  # e.g., '1 SAMUEL' -> '1_SAMUEL'
        
        c_cd = str(row.get('chapter_cd', row.get('CHAPTER_CD', ''))).strip()
        if c_cd.isdigit(): 
            c_cd = c_cd.zfill(3)

        if clean_b_cd and c_cd:
            grouped[(clean_b_cd, c_cd)].append(row)

    print(f"📦 Grouped into {len(grouped)} chapter files.")

    # 3. WRITE OUT INDIVIDUAL CHAPTER FILES TO THEIR VOLUME DIRECTORIES
    files_created = 0
    for (clean_b_cd, c_cd), chap_items in sorted(grouped.items()):
        volume_dir = BOOK_VOLUME_MAP.get(clean_b_cd, clean_b_cd.title())
        target_dir = os.path.join(output_base_dir, volume_dir)
        os.makedirs(target_dir, exist_ok=True)

        filename = f"{clean_b_cd}_{c_cd}.json"
        filepath = os.path.join(target_dir, filename)

        payload = {
            "results": [
                {
                    "columns": columns_def,
                    "items": chap_items
                }
            ]
        }

        with open(filepath, 'w', encoding='utf-8') as out_f:
            json.dump(payload, out_f, ensure_ascii=False, indent=2)

        files_created += 1

    print(f"\n🎉 Success! Created {files_created} formatted chapter score files in '{output_base_dir}/'.")

if __name__ == "__main__":
    split_master_syllables("syllables_master.json", "musicscores")