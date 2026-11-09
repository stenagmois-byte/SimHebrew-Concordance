import os
import json
import html
import sys
from collections import defaultdict

def run_distribution_analysis(chapter_index_only=False, pretty_json=False):
    PITCH_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    PITCH_LABELS = ['c', 'd', 'e', 'f', 'g', 'A', 'B', 'C']
    
    # 🏛️ TRADITIONAL HEBREW PITCH NAMES MAPPING
    PITCH_TO_HEBREW_NAME = {
        "c": "Darga",
        "d": "Tevir/Galgal",
        "e": "Silluq",
        "f": "Mercha",
        "g": "Tifha/D'khi",
        "A": "Atnah",
        "B": "Munach",
        "C": "Mahpach/Yetiv"
    }

    # 📜 HEBREW ORNAMENT GLYPH MAPPING (Superlinear accents on carrier Aleph)
    ORNAMENT_GLYPHS = {
        "zaqef-qatan": "&#x05D0;&#x0594;",
        "pashta": "&#x05D0;&#x0599;",
        "revia": "&#x05D0;&#x0597;",
        "qadma": "&#x05D0;&#x0598;",
        "azla": "&#x05D0;&#x059C;",
        "geresh": "&#x05D0;&#x0597;",
        "telisha-qetana": "&#x05D0;&#x05A9;",
        "tarsin": "&#x05D0;&#x059E;",
        "zaqef-gadol": "&#x05D0;&#x0595;",
        "tsinnor": "&#x05D0;&#x05AE;",
        "telisha-gedola": "&#x05D0;&#x05A0;",
        "segol": "&#x05D0;&#x0596;",
        "pazer": "&#x05D0;&#x05A1;",
        "ole": "&#x05D0;&#x05AB;",
        "revia-mugrash": "&#x05D0;&#x059D;&#x0597;",
        "zarqa": "&#x05D0;&#x0598;",
        "illuy": "&#x05D0;&#x05AC;",
        "shalshelet": "&#x05D0;&#x0593;",
        "qarne-farah": "&#x05D0;&#x059F;",
        "pashta pashta": "&#x05D0;&#x0599;&#x0599;",
        "z-qatan pazer": "&#x05D0;&#x0594;&#x05A1;",
        "z-qatan tsinnor": "&#x05D0;&#x0594;&#x05AE;",
        "pazer z-qatan": "&#x05D0;&#x05A1;&#x0594;",
        "azla z-qatan": "&#x05D0;&#x059C;&#x0594;",
        "tarsin revia": "&#x05D0;&#x059E;&#x0597;",
        "azla t-qetana": "&#x05D0;&#x059C;&#x05A9;",
        "revia z-qatan": "&#x05D0;&#x0597;&#x0594;",
        "z-qatan azla": "&#x05D0;&#x0594;&#x059C;",
        "pazer azla": "&#x05D0;&#x05A1;&#x059C;",
        "azla pashta": "&#x05D0;&#x059C;&#x0599;",
        "z-gadol pashta": "&#x05D0;&#x0595;&#x0599;",
        "telisha-gedola azla": "&#x05D0;&#x05A0;&#x059C;"
    }

    # 🏷️ DISPLAY NAME OVERRIDES FOR ELEGANT TYPOGRAPHY
    ORNAMENT_DISPLAY_NAMES = {
        "zaqef-qatan": "Zaqef-Qatan",
        "pashta": "Pashta",
        "revia": "Revia",
        "qadma": "Qadma",
        "azla": "Azla",
        "geresh": "Geresh",
        "telisha-qetana": "Telisha Qetana",
        "tarsin": "Tarsin / Gershaim",
        "zaqef-gadol": "Zaqef-Gadol",
        "tsinnor": "Tsinnor",
        "telisha-gedola": "Telisha-Gedola",
        "segol": "Segol",
        "pazer": "Pazer",
        "ole": "Ole",
        "revia-mugrash": "Revia-Mugrash",
        "zarqa": "Tsinnorit (poetic Zarqa)",
        "illuy": "Illuy",
        "shalshelet": "Shalshalet",
        "qarne-farah": "Qarne-Farah",
        "pashta pashta": "Pashta Pashta",
        "z-qatan pazer": "Z-Qatan Pazer",
        "z-qatan tsinnor": "Z-Qatan Tsinnor",
        "pazer z-qatan": "Pazer Z-Qatan",
        "azla z-qatan": "Azla Z-Qatan",
        "tarsin revia": "Tarsin Revia",
        "azla t-qetana": "Azla T-Qetana",
        "revia z-qatan": "Revia Z-Qatan",
        "z-qatan azla": "Z-Qatan Azla",
        "pazer azla": "Pazer Azla",
        "azla pashta": "Azla Pashta",
        "z-gadol pashta": "Z-Gadol Pashta",
        "telisha-gedola azla": "T-Gedola Azla"
    }

    matrix = defaultdict(lambda: defaultdict(int))
    target_dirs = ["./musicscores"]
    search_index = defaultdict(lambda: defaultdict(list))
    chapter_index = {}

    found_any_files = False
    for t_dir in target_dirs:
        if os.path.exists(t_dir):
            for root, dirs, files in os.walk(t_dir):
                for file in files:
                    if file.endswith('.json') and not file.startswith('.'):
                        found_any_files = True
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                rows = []
                                if isinstance(data, dict) and 'results' in data:
                                    for res in data['results']:
                                        if 'items' in res:
                                            rows.extend(res['items'])
                                elif isinstance(data, list):
                                    rows = data
                                elif isinstance(data, dict):
                                    rows = data.get('rows', [data])
                                
                                # 1. PRE-MAP VERSE TEXTS FOR THIS CHAPTER
                                chapter_verse_text_map = {}
                                for row in rows:
                                    if not isinstance(row, dict): continue
                                    
                                    c_cd = str(row.get('chapter_cd', '')).lstrip('0')
                                    v_cd = str(row.get('verse_cd', '')).lstrip('0')
                                    text_val = str(row.get('heb_text', row.get('HEB_TEXT', ''))).strip()
                                    
                                    if text_val and (c_cd, v_cd) not in chapter_verse_text_map:
                                        chapter_verse_text_map[(c_cd, v_cd)] = text_val

                                    raw_book_for_chapter = str(row.get('book_cd', row.get('BOOK_CD', ''))).strip()
                                    if text_val and raw_book_for_chapter and c_cd and v_cd:
                                        display_book = raw_book_for_chapter.replace('_', ' ').title()
                                        chapter_key = f"{display_book}|{c_cd}"
                                        chapter_entry = chapter_index.setdefault(chapter_key, {
                                            "s": int(row.get('book_seq_no', 99)),
                                            "b": display_book,
                                            "c": c_cd,
                                            "verses": {}
                                        })
                                        chapter_entry["verses"].setdefault(v_cd, {
                                            "v": v_cd,
                                            "t": text_val,
                                            "ornaments": []
                                        })

                                # 2. RUN ORNAMENT PROCESSING LOOP
                                for row in rows:
                                    if not isinstance(row, dict): continue
                                    
                                    orn = row.get('ornament_name', row.get('ORNAMENT_NAME', ''))
                                    orn = str(orn).strip().lower()
                                    
                                    if orn == '0' or orn == '':
                                        continue
                                        
                                    raw_pitch = row.get('syll_note', row.get('SYLL_NOTE', ''))
                                    raw_pitch = str(raw_pitch).strip().upper()
                                    
                                    # 🎯 FIX: Isolate ONLY the first character (e.g. 'F4' -> 'F')
                                    base_letter = raw_pitch[0] if len(raw_pitch) > 0 else ''
                                    is_octave_5 = '5' in raw_pitch
                                    
                                    if base_letter in PITCH_KEYS:
                                        if base_letter == 'C':
                                            target_label = 'C' if is_octave_5 else 'c'
                                        else:
                                            target_label = base_letter.lower() if base_letter not in ['A', 'B'] else base_letter
                                            
                                        matrix[orn][target_label] += 1
                                        
                                        book_seq = row.get('book_seq_no', 99)
                                        raw_book = row.get('book_cd', 'Unknown')
                                        book_name = raw_book.replace('_', ' ').title() 
                                        
                                        chapter_num = str(row.get('chapter_cd', '0')).lstrip('0') or '0'
                                        verse_num = str(row.get('verse_cd', '0')).lstrip('0') or '0'
                                        
                                        hebrew_text = row.get('heb_text', row.get('HEB_TEXT', '')).strip()
                                        if not hebrew_text:
                                            hebrew_text = chapter_verse_text_map.get((chapter_num, verse_num), '')

                                        record = {
                                            "s": int(book_seq),
                                            "b": book_name,
                                            "c": chapter_num,
                                            "v": verse_num,
                                            "t": hebrew_text
                                        }
                                        
                                        search_index[orn][target_label].append(record)

                                        chapter_key = f"{book_name}|{chapter_num}"
                                        chapter_entry = chapter_index.setdefault(chapter_key, {
                                            "s": int(book_seq), "b": book_name,
                                            "c": chapter_num, "verses": {}
                                        })
                                        verse_entry = chapter_entry["verses"].setdefault(verse_num, {
                                            "v": verse_num, "t": hebrew_text,
                                            "ornaments": []
                                        })
                                        if not verse_entry["t"] and hebrew_text:
                                            verse_entry["t"] = hebrew_text
                                        verse_entry["ornaments"].append({
                                            "n": orn, "p": target_label
                                        })

                        except Exception as e:
                            continue
            if found_any_files:
                break

    sorted_rows = []
    for orn, pitches in matrix.items():
        total = sum(pitches.values())
        pitch_counts = [pitches[lbl] for lbl in PITCH_LABELS]
        sorted_rows.append((total, orn, pitch_counts))
        
    sorted_rows.sort(key=lambda x: x[0], reverse=True)

    # 🏛️ HTML OUTPUT TEMPLATE
    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="qstyles.css">
    <title>Ornament Usage by Recitation Pitch — Tanach Musical Concordance</title>
    <style>
        body {{ font-family: 'Georgia', serif; margin: 40px auto; max-width: 1050px; color: #222222; line-height: 1.65; background-color: #fffcf4; padding: 0 20px; }}
        .nav {{ margin-bottom: 25px; font-family: sans-serif; font-size: 0.9rem; }}
        .nav a {{ color: #800000; text-decoration: none; font-weight: bold; }}
        .nav a:hover {{ text-decoration: underline; }}
        h1 {{ font-family: sans-serif; color: #800000; font-size: 2.2rem; margin-bottom: 10px; font-weight: normal; }}
        p {{ text-align: justify; font-size: 1.1rem; color: #333; margin-bottom: 25px; }}
        table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.95rem; margin: 35px 0; background-color: #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.05); border-top: 2px solid #800000; border-bottom: 2px solid #800000; }}
        th {{ background-color: #f3f0e8; color: #800000; font-weight: bold; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 10px; border-bottom: 1px solid #800000; text-align: center; }}
        th.left-align, td.left-align {{ text-align: left; font-weight: bold; color: #222; font-family: serif; font-size: 1.1rem; padding-left: 15px; }}
        td {{ padding: 10px; border-bottom: 1px solid #eaeaea; text-align: center; color: #444; }}
        tr:hover {{ background-color: #fcfaf2; }}
        .total-cell {{ font-weight: bold; color: #800000; background-color: #fdfcf7; }}
        .zero-count {{ color: #ccc; font-weight: 300; }}
        .footnote {{ margin-top: 40px; font-family: 'Georgia', serif; font-size: 1.05rem; border-top: 1px solid #800000; padding-top: 20px; color: #444; }}
        .footnote p {{ text-align: justify; line-height: 1.6; }}
        .glyph-cell {{
            font-family: "SBL Hebrew", "Ezra SIL", "Times New Roman", serif;
            font-size: 1.75rem;
            line-height: 1;
            text-align: center;
            color: #800000;
            width: 48px;
        }}
        .heb-carrier {{
            font-family: "SBL Hebrew", "Ezra SIL", "Times New Roman", serif;
            font-size: 1.6rem;
            line-height: normal;
            font-weight: normal !important;
            color: #800000;
            display: inline;
            margin: 0 3px;
            text-rendering: optimizeLegibility;
            -webkit-font-smoothing: antialiased;
        }}
    </style>
    <script src="./menu.js" defer></script>
</head>
<body>

    <h1>Ornament Usage by Recitation Pitch</h1>
    <p>The deciphering key reveals relationships that have been hidden since antiquity, specifically, the relationship of the accents above the text (ornaments) with the accent below the text that immediately precedes them, and which defines the recitation pitch that governs them. The music of these pages and scores is the demonstration.</p>

    <form id="chapter-explorer-form" style="margin: 25px 0; padding: 18px; background: #f3f0e8; border-left: 4px solid #800000; font-family: sans-serif;">
        <strong style="color: #800000;">Trope for a chapter</strong>
        <label style="margin-left: 18px;">Book
            <select id="chapter-book" required style="margin-left: 6px; padding: 5px;"></select>
        </label>
        <label style="margin-left: 12px;">Chapter
            <input id="chapter-number" type="number" min="1" required style="width: 4.5rem; margin-left: 6px; padding: 5px;">
        </label>
        <button type="submit" style="margin-left: 12px; padding: 6px 12px; color: white; background: #800000; border: 0; border-radius: 3px; cursor: pointer;">Show chapter</button>
    </form>

    <table>
        <thead>
            <tr>
                <th colspan="2" rowspan="2" class="left-align" style="vertical-align: middle;">Ornament &amp; Name</th>
                <th rowspan="3" class="total-cell" style="vertical-align: middle;">Total</th>
                <th>c</th>
                <th>d</th>
                <th>e</th>
                <th>f</th>
                <th>g</th>
                <th>A</th>
                <th>B</th>
                <th>C</th>
            </tr>
            <tr>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Darga</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Tevir/Galgal</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Silluq</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Mercha</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Tifha/D'khi</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Atnah</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Munach</span></th>
                <th><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>Mahpach/Yetiv</span></th>
            </tr>
            <tr>
                <th style="font-size: 0.75rem; font-weight: normal; text-transform: none; width: 48px;">Ornament</th>
                <th class="left-align" style="font-size: 0.75rem; font-weight: normal; text-transform: none;">Name</th>
                <th><span class="heb-carrier" title="Darga">&#x05D0;&#x05A7;</span></th>
                <th>
                    <span class="heb-carrier" title="Tevir (prose)">&#x05D0;&#x059B;</span>
                    <span class="heb-carrier" title="Galgal / Yerah (poetry)">&#x05D0;&#x05AA;</span>
                </th>
                <th><span class="heb-carrier" title="Silluq">&#x05D0;&#x05BD;</span></th>
                <th><span class="heb-carrier" title="Mercha">&#x05D0;&#x05A5;</span></th>
                <th>
                    <span class="heb-carrier" title="Tifha">&#x05D0;&#x0596;</span>
                    <span class="heb-carrier" title="D'khi">&#x05D0;&#x05AD;</span>
                </th>
                <th><span class="heb-carrier" title="Atnah">&#x05D0;&#x0591;</span></th>
                <th><span class="heb-carrier" title="Munach">&#x05D0;&#x05A3;</span></th>
                <th>
                    <span class="heb-carrier" title="Mahpach">&#x05D0;&#x05A4;</span>
                    <span class="heb-carrier" title="Yetiv">&#x05D0;&#x059A;</span>
                </th>
            </tr>
        </thead>
        <tbody>
"""

    if not sorted_rows:
        html_output += """        <tr>
            <td colspan="11" style="padding: 40px; color: #800000; font-style: italic;">
                ❌ Verification Warning: Evaluated 0 valid ornament entries inside JSON data structures.
            </td>
        </tr>"""
    else:
        for total, orn, counts in sorted_rows:
            display_name = ORNAMENT_DISPLAY_NAMES.get(orn, orn.title())
            glyph = ORNAMENT_GLYPHS.get(orn, "&#x05D0;")

            counts_str = ""
            for idx, c in enumerate(counts):
                lbl = PITCH_LABELS[idx]
                if c == 0:
                    counts_str += '<td class="zero-count">0</td>'
                else:
                    counts_str += f"""<td>
                        <div>{c}</div>
                        <div style='margin-top: 4px; font-size: 0.72rem;'>
                            <a href='ornament_records.html?ornament={html.escape(orn)}&pitch={html.escape(lbl)}' 
                               style='color: #800000; text-decoration: none;' title='Explore records'>🔍 explore</a>
                        </div>
                    </td>"""
            
            html_output += f"""        <tr>
                <td class="glyph-cell">{glyph}</td>
                <td class="left-align">{html.escape(display_name)}</td>
                <td class="total-cell">{total}</td>
                {counts_str}
            </tr>\n"""

    html_output += """        </tbody>
    </table>

    <div class="footnote">
        <p>We can see immediately which ornaments are rarely or frequently used and on which pitches. The last 13 rows are the rare double accents on a single syllable. Notice the sole tarsin on the low c in the table above. It is from 2 Chronicles 24:27 in the Leningrad Codex. It is not in the Aleppo codex online at mgketer.org. So using the terms of the deciphering key, no <i>ornament</i> ever occurs on a low c. In the language of traditional Hebrew names, no accent <i>above the text</i> ever occurs following a darga and before another accent under the text is encountered.</p>
        <p>The largest contributor to the musical corpus of the accents above the text is the zaqef-qatan. This is a significant division of the text into phrases, sometimes in surprising contexts where one would not expect a pause in the recitation.</p>
    </div>

<script>
const chapterBooks = ["Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua", "Judges", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings", "Isaiah", "Jeremiah", "Ezekiel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah", "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Psalms", "Proverbs", "Job", "Song", "Ruth", "Lamentations", "Qohelet", "Esther", "Daniel", "Ezra", "Nehemiah", "1 Chronicles", "2 Chronicles"];
const chapterBookSelect = document.getElementById("chapter-book");
chapterBooks.forEach(book => chapterBookSelect.add(new Option(book, book)));
document.getElementById("chapter-explorer-form").addEventListener("submit", event => {
    event.preventDefault();
    const book = chapterBookSelect.value;
    const chapter = document.getElementById("chapter-number").value;
    window.location.href = `ornament_chapter.html?book=${encodeURIComponent(book)}&chapter=${encodeURIComponent(chapter)}`;
});
</script>
</body>
</html>"""

    chapter_output = {"chapters": []}
    for chapter in sorted(chapter_index.values(), key=lambda item: (item["s"], int(item["c"]))):
        chapter["verses"] = [
            chapter["verses"][key]
            for key in sorted(chapter["verses"], key=lambda value: int(value))
        ]
        chapter_output["chapters"].append(chapter)
    
    # Save ornament_chapters.json
    dump_kwargs = {"ensure_ascii": False}
    if pretty_json:
        dump_kwargs["indent"] = 2
    else:
        dump_kwargs["separators"] = (",", ":")

    with open("ornament_chapters.json", "w", encoding="utf-8") as chapter_f:
        json.dump(chapter_output, chapter_f, **dump_kwargs)
    print("Chapter-first index 'ornament_chapters.json' compiled successfully!")

    if not chapter_index_only:
        with open("ornament_usage_by_pitch.html", "w", encoding="utf-8") as out_f:
            out_f.write(html_output)
        print("📈 Success! 'ornament_usage_by_pitch.html' compiled via direct file list extraction.")
        
        with open("./ornament_index.json", "w", encoding="utf-8") as index_f:
            json.dump(search_index, index_f, **dump_kwargs)
        print("📁 Master database file 'ornament_index.json' compiled successfully!")

if __name__ == "__main__":
    run_distribution_analysis(
        chapter_index_only="--chapter-index-only" in sys.argv,
        pretty_json="--pretty" in sys.argv
    )