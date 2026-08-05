import os
import json
import html
from collections import defaultdict
def run_distribution_analysis():
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
    
    matrix = defaultdict(lambda: defaultdict(int))
    target_dirs = ["./musicscores"]
    search_index = defaultdict(lambda: defaultdict(list))
    
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
                                
                                # FIX: Navigate the specific "results" -> "items" structure
                                rows = []
                                if isinstance(data, dict) and 'results' in data:
                                    for res in data['results']:
                                        if 'items' in res:
                                            rows.extend(res['items'])
                                # Fallback to your original logic if other file formats exist
                                elif isinstance(data, list):
                                    rows = data
                                elif isinstance(data, dict):
                                    rows = data.get('rows', [data])
                                
                                # Loop through your flat json array rows natively
                                # 1. PRE-MAP VERSE TEXTS FOR THIS CHAPTER
                                # Native lowercase text key checks
                                chapter_verse_text_map = {}
                                for row in rows:
                                    if not isinstance(row, dict): continue
                                    
                                    c_cd = str(row.get('chapter_cd', '')).lstrip('0')
                                    v_cd = str(row.get('verse_cd', '')).lstrip('0')
                                    
                                    # Fallback chain checks lowercase first, then uppercase
                                    text_val = str(row.get('heb_text', row.get('HEB_TEXT', ''))).strip()
                                    
                                    if text_val and (c_cd, v_cd) not in chapter_verse_text_map:
                                        chapter_verse_text_map[(c_cd, v_cd)] = text_val

                                # 2. RUN NATIVE LOWERCASE ORNAMENT PROCESSING LOOP
                                for row in rows:
                                    if not isinstance(row, dict): continue
                                    
                                    # 🔄 FALLBACK CHAIN FOR THE ORNAMENT NAME CELL:
                                    # Checks lowercase 'ornament_name' first, then upper 'ORNAMENT_NAME'
                                    orn = row.get('ornament_name', row.get('ORNAMENT_NAME', ''))
                                    orn = str(orn).strip().lower()
                                    
                                    # Skip plain, un-ornamented syllables
                                    if orn == '0' or orn == '':
                                        continue
                                        
                                    # 🔄 FALLBACK CHAIN FOR SYLLABLE NOTES:
                                    # Checks lowercase 'syll_note' first, then upper 'SYLL_NOTE'
                                    raw_pitch = row.get('syll_note', row.get('SYLL_NOTE', ''))
                                    raw_pitch = str(raw_pitch).strip().upper()
                                    
                                    # Isolate ONLY the first character (e.g., 'F#4' -> 'F')
                                    base_letter = raw_pitch[0] if len(raw_pitch) > 0 else ''
                                    is_octave_5 = '5' in raw_pitch
                                    
                                    if base_letter in PITCH_KEYS:
                                        if base_letter == 'C':
                                            target_label = 'C' if is_octave_5 else 'c'
                                        else:
                                            # Groups F#4 under 'f', G#4 under 'g', etc.
                                            target_label = base_letter.lower() if base_letter not in ['A', 'B'] else base_letter
                                            
                                        # Record the counts in the central distribution table matrix
                                        matrix[orn][target_label] += 1
                                        
                                        # Standardize structural indicators
                                        book_seq = row.get('book_seq_no', 99)
                                        raw_book = row.get('book_cd', 'Unknown')
                                        book_name = raw_book.replace('_', ' ').title() 
                                        
                                        chapter_num = str(row.get('chapter_cd', '0')).lstrip('0') or '0'
                                        verse_num = str(row.get('verse_cd', '0')).lstrip('0') or '0'
                                        
                                        # Choose the smart fallback text vector
                                        hebrew_text = row.get('heb_text', row.get('HEB_TEXT', '')).strip()
                                        if not hebrew_text:
                                            hebrew_text = chapter_verse_text_map.get((chapter_num, verse_num), '')

                                        # Save the finalized, guaranteed-complete data payload
                                        record = {
                                            "s": int(book_seq),
                                            "b": book_name,
                                            "c": chapter_num,
                                            "v": verse_num,
                                            "t": hebrew_text
                                        }
                                        
                                        search_index[orn][target_label].append(record)

                        except Exception as e:
                            # Useful for debugging structural errors during setup
                            # print(f"Error processing {file}: {e}")
                            continue
            if found_any_files:
                break

    sorted_rows = []
    for orn, pitches in matrix.items():
        total = sum(pitches.values())
        pitch_counts = [pitches[lbl] for lbl in PITCH_LABELS]
        sorted_rows.append((total, orn, pitch_counts))
        
    sorted_rows.sort(key=lambda x: x[0], reverse=True) # Sort by total frequency ascending
    
    #return sorted_rows # Make sure to return your data to build the webpage!

    # Insert this loop block directly inside your html_output string variable where the table body goes:
    # 🗂️ TRANSFORM RAW MATRIX DATA INTO CLEAN HTML ROWS
    table_rows_html = ""
    for total, orn, pitch_counts in sorted_rows:
        table_rows_html += f"<tr>\n"
        # Display the ornament tag in uppercase for your Oxford layout aesthetic
        table_rows_html += f"  <td class='left-align'>{orn.upper()}</td>\n"
        table_rows_html += f"  <td class='total-cell'>{total}</td>\n"
        
        # Loop through each individual pitch label box (c, d, e, f, g, A, B, C)
        for idx, lbl in enumerate(PITCH_LABELS):
            count = pitch_counts[idx]
            if count == 0:
                table_rows_html += f"  <td class='zero-count'>0</td>\n"
            else:
                # Wrap each non-zero count in an interactive URL routing anchor link
                table_rows_html += f"""  <td>
                    <div>{count}</div>
                    <div style='margin-top: 4px; font-size: 0.75rem;'>
                        <a href='ornament_records.html?ornament={html.escape(orn)}&pitch={html.escape(lbl)}' 
                           style='color: #800000; text-decoration: none;' title='Explore instances'>🔍 explore</a>
                    </div>
                  </td>\n"""
        table_rows_html += f"</tr>\n"
    header_cells = ""
    for lbl in PITCH_LABELS:
        heb_name = PITCH_TO_HEBREW_NAME.get(lbl, lbl)
        header_cells += f"<th>{lbl}<br><span style='font-size: 0.75rem; font-weight: normal; text-transform: none; color: #555;'>{heb_name}</span></th>"

    # 🏛️ INJECT THE STRUCTURE INTO YOUR SITE HTML BODY
    # 1. INITIALIZE THE TOP SECTION OF THE HTML FILE
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
    </style>
</head>
<body>

    <div class="nav">
        <a href="./musicscores/index.html">← Back to Volume Directory</a>
    </div>

    <h1>Ornament Usage by Recitation Pitch</h1>
    <p>This concordance matrix outlines the distribution frequency of accents above the text aligned against the accent below the text that immediately precedes them defining the recitation pitch that governs the ornaments.</p>

    <table>
        <thead>
            <tr>
                <th class='left-align'>Ornament Name</th>
                <th class='total-cell'>Total</th>
                {header_cells}
            </tr>
        </thead>
        <tbody>
"""

    # 2. APPEND THE ACTIVE DYNAMIC ROWS LAYER IN THE CORRECT SLOT
    if not sorted_rows:
        html_output += """        <tr>
            <td colspan="10" style="padding: 40px; color: #800000; font-style: italic;">
                ❌ Verification Warning: Evaluated 0 valid ornament entries inside JSON data structures.
            </td>
        </tr>"""
    else:
        for total, orn, counts in sorted_rows:
            # Transform '0' values to use dimmed styling, and attach interactive explorer search routing links to active cells
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
                <td class="left-align">{html.escape(orn.upper())}</td>
                <td class="total-cell">{total}</td>
                {counts_str}
            </tr>\n"""

    # 3. CLOSE THE TABLE AND APPEND THE SCHOLARLY FOOTNOTE CRITIQUE AT THE END
    html_output += """        </tbody>
    </table>

    <div class="footnote">
    <p>We can see immediately which ornaments are rarely or frequently used and on which pitches. The last 13 rows are double accents on a single syllable. They are noted in the publications. They are all rare. Several are in the decalogues. Notice the sole tarsin on the low c in the table above. It is from 2 Chronicles 24:27 in the Leningrad Codex. It is not in the Aleppo codex online at mgketer.org. So in the terms of the deciphering key, no ornament ever occurs on a low c. In terms of traditional Hebrew names, no accent above the text ever occurs following a darga and before another accent under the text is encountered. The largest contributor to the musical corpus of the accents above the text is the zaqef-qatan. This is a significant division of the text into phrases, sometimes in surprising contexts where one would not expect to breathe. Each has to be looked at individually.
    </p>
    </div>

</body>
</html>"""

    with open("ornament_usage_by_pitch.html", "w", encoding="utf-8") as out_f:
        out_f.write(html_output)
    print("📈 Success! 'ornament_usage_by_pitch.html' compiled via direct file list extraction.")
    with open("./ornament_index.json", "w", encoding="utf-8") as index_f:
        json.dump(search_index, index_f, ensure_ascii=False)
        
    print("📁 Master database file 'ornament_index.json' compiled successfully!")
if __name__ == "__main__":
    run_distribution_analysis()
