import os
import json
import html
from collections import defaultdict
def run_distribution_analysis():
    PITCH_KEYS = ['C', 'D', 'E', 'F', 'G', 'A', 'B']
    PITCH_LABELS = ['c', 'd', 'e', 'f', 'g', 'A', 'B', 'C']
    
    matrix = defaultdict(lambda: defaultdict(int))
    target_dirs = ["./musicscores", "musicscores", "."]
    
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
                                for row in rows:
                                    if not isinstance(row, dict): 
                                        continue
                                    
                                    # Safe case-insensitive lookups
                                    orn = row.get('ornament_name', row.get('ORNAMENT_NAME', ''))
                                    orn = str(orn).strip().lower()
                                    
                                    # FIX: Skip plain, un-ornamented syllables ('0')
                                    # We want to KEEP things that are NOT '0'
                                    if orn == '0' or orn == '':
                                        continue
                                        
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
                                            
                                        matrix[orn][target_label] += 1
                                    
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
        
    sorted_rows.sort(key=lambda x: x[0]) # Sort by total frequency ascending
    
    #return sorted_rows # Make sure to return your data to build the webpage!

    html_output = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="qstyles.css">
    <title>Ornament Usage by Recitation Pitch — Tanach Musical Concordance</title>
    <style>
        /* 🏛️ OXFORD ACADEMIC TYPOGRAPHY & LAYOUT RESET */
        body {{ 
            font-family: 'Georgia', serif; 
            margin: 40px auto; 
            max-width: 1050px; 
            color: #222222; 
            line-height: 1.65; 
            background-color: #fffcf4; 
            padding: 0 20px;
        }}
        
        .nav {{ 
            margin-bottom: 25px; 
            font-family: sans-serif; 
            font-size: 0.9rem; 
        }}
        .nav a {{ 
            color: #800000; 
            text-decoration: none; 
            font-weight: bold; 
        }}
        .nav a:hover {{ 
            text-decoration: underline; 
        }}

        h1 {{ 
            font-family: sans-serif; 
            color: #800000; 
            font-size: 2.2rem; 
            margin-bottom: 10px; 
            font-weight: normal;
        }}
        
        p {{ 
            text-align: justify; 
            font-size: 1.1rem; 
            color: #333; 
            margin-bottom: 25px; 
        }}

        /* 📊 OXFORD SCHOLASTIC CRITICAL APPARATUS TABLE STYLES */
        table {{ 
            width: 100%; 
            border-collapse: collapse; 
            font-family: sans-serif; 
            font-size: 0.95rem; 
            margin: 35px 0; 
            background-color: #ffffff; 
            box-shadow: 0 1px 4px rgba(0,0,0,0.05); 
            border-top: 2px solid #800000; 
            border-bottom: 2px solid #800000; 
        }}
        
        th {{ 
            background-color: #f3f0e8; 
            color: #800000; 
            font-weight: bold; 
            font-size: 0.85rem; 
            text-transform: uppercase; 
            letter-spacing: 0.5px; 
            padding: 12px 10px; 
            border-bottom: 1px solid #800000; 
            text-align: center; 
        }}
        
        th.left-align, td.left-align {{ 
            text-align: left; 
            font-weight: bold; 
            color: #222; 
            font-family: serif; 
            font-size: 1.1rem; 
            padding-left: 15px; 
        }}
        
        td {{ 
            padding: 10px; 
            border-bottom: 1px solid #eaeaea; 
            text-align: center; 
            color: #444; 
        }}
        
        tr:hover {{ 
            background-color: #fcfaf2; 
        }}
        
        .total-cell {{ 
            font-weight: bold; 
            color: #800000; 
            background-color: #fdfcf7; 
        }}
        
        /* Zero count styling to make active values pop out cleanly */
        .zero-count {{ 
            color: #ccc; 
            font-weight: 300; 
        }}

        /* 📜 CRITICAL COMMENTARY BAR POINTER */
        .footnote {{ 
            margin-top: 40px; 
            font-family: 'Georgia', serif; 
            font-size: 1.05rem; 
            border-top: 1px solid #800000; 
            padding-top: 20px; 
            color: #444; 
        }}
        .footnote p {{ 
            text-align: justify; 
            line-height: 1.6; 
        }}
    </style>
</head>
<body>

    <div class="nav">
        <a href="./musicscores/index.html">← Back to Volume Directory</a>
    </div>

    <h1>Ornament Usage by Recitation Pitch</h1>
    <p>The first characteristic of the deciphering key to the musical sense of the accents is the separation of the accents below the text from those above. Those below the text define the recitation pitch. Those above are ornamentation relative to that defined pitch. The usage of ornaments by pitch gives some insight into the music of a particular section of the text. The table below shows the usage of ornaments by recitation pitch. 
    We can see immediately which ornaments are rarely or frequently used and on which pitches.</p>

    <table>
        <thead>
            <tr>
                <th class="left-align" style="width: 25%;">Ornament / Pitch</th>
                <th style="width: 11%;">Total Footprint</th>
                {"".join(f'<th style="width: 8%;">{lbl}</th>' for lbl in PITCH_LABELS)}
            </tr>
        </thead>
        <tbody>
    """

    if not sorted_rows:
        html_output += """        <tr>
            <td colspan="10" style="padding: 40px; color: #800000; font-style: italic;">
                ❌ Verification Warning: Evaluated 0 valid ornament entries inside JSON data structures.
            </td>
        </tr>"""
    else:
        for total, orn, counts in sorted_rows:
            # Transform '0' values to use dimmed styling so real density points pop out visually
            counts_str = "".join(f"<td>{c}</td>" if c > 0 else '<td class="zero-count">0</td>' for c in counts)
            html_output += f"""        <tr>
                <td class="left-align">{html.escape(orn)}</td>
                <td class="total-cell">{total}</td>
                {counts_str}
            </tr>\n"""

    html_output += """        </tbody>
    </table>

    <div class="footnote">
    <p>We can see immediately which ornaments are rarely or frequently used and on which pitches. The first 13 rows are double accents on a single syllable. They are noted in the publications. They are all rare. Several are in the decalogues. Notice the sole tarsin on the low c in the table above. It is from 2 Chronicles 24:27 in the Leningrad Codex. It is not in the Aleppo codex online at mgketer.org. So in the terms of the deciphering key, no ornament ever occurs on a low c. In terms of traditional Hebrew names, no accent above the text ever occurs following a darga and before another accent under the text is encountered. The largest contributor to the musical corpus of the accents above the text is the zaqef-qatan. This is a significant division of the text into phrases, sometimes in surprising contexts where one would not expect to breathe. Each has to be looked at individually.
    </p>

    </div>

</body>
</html>
"""

    with open("ornament_usage_by_pitch.html", "w", encoding="utf-8") as out_f:
        out_f.write(html_output)
    print("📈 Success! 'ornament_usage_by_pitch.html' compiled via direct file list extraction.")

if __name__ == "__main__":
    run_distribution_analysis()
