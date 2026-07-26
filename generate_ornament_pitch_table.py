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
    <title>Ornament Usage by Recitation Pitch</title>
    <style>
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 40px; color: #333; line-height: 1.6; background-color: #fdfdfb; }}
        h1 {{ color: #8A6D3B; border-bottom: 2px solid #8A6D3B; padding-bottom: 10px; }}
        p {{ max-width: 850px; text-align: justify; }}
        table {{ border-collapse: collapse; margin-top: 30px; width: 100%; max-width: 950px; border: 2px solid #8A6D3B; background-color: white; }}
        th {{ background-color: #8A6D3B; color: white; font-weight: 600; padding: 12px 14px; border: 1px solid #70582F; text-align: center; }}
        th.left-align, td.left-align {{ text-align: left; font-weight: bold; background-color: #fdfaf2; border-right: 2px solid #8A6D3B; }}
        td {{ padding: 10px 14px; border: 1px solid #ddd; text-align: center; }}
        tr:nth-child(even) {{ background-color: #fcfbfa; }}
        tr:hover {{ background-color: #f5efe3; }}
        .total-cell {{ background-color: #fdfaf2; font-weight: bold; border-right: 1px solid #8A6D3B; }}
        .footnote {{ margin-top: 40px; font-size: 0.98em; max-width: 850px; border-left: 5px solid #8A6D3B; padding-left: 20px; font-style: italic; text-align: justify; }}
    </style>
</head>
<body>

    <h1>Ornament Usage by Recitation Pitch</h1>
    <p>The first characteristic of the deciphering key to the musical sense of the accents is the separation of the 
    accents below the text from those above. Those below the text define the recitation pitch. Those above are 
    ornamentation relative to that defined pitch. The usage of ornaments by pitch gives some insight into the 
    music of a particular section of the text. The table below shows the usage of ornaments by recitation pitch. 
    We can see immediately which ornaments are rarely or frequently used and on which pitches.</p>

    <table>
        <thead>
            <tr>
                <th class="left-align">Ornament / Pitch</th>
                <th>Total</th>
                {"".join(f"<th>{lbl}</th>" for lbl in PITCH_LABELS)}
            </tr>
        </thead>
        <tbody>
    """

    if not sorted_rows:
        html_output += """        <tr>
            <td colspan="10" style="padding: 30px; color: red; font-weight: bold;">
                ❌ Verification Warning: Evaluated 0 valid ornament entries inside JSON data structures.
            </td>
        </tr>"""
    else:
        for total, orn, counts in sorted_rows:
            counts_str = "".join(f"<td>{c if c > 0 else '0'}</td>" for c in counts)
            html_output += f"""        <tr>
                <td class="left-align">{html.escape(orn)}</td>
                <td class="total-cell">{total}</td>
                {counts_str}
            </tr>\n"""

    html_output += """        </tbody>
    </table>

    <div class="footnote">
        <p>The first two on the list are two ornaments on a single syllable. The first is unique in the Bible. It occurs in 
        Genesis 35:22 on the word בִּבְכֹ֥ות (bar 221 in the image below). The second occurs 4 times in the Bible. 
        Double pashta is frequent on two consecutive syllables, but it is rare to have two on the same syllable. This 
        happens also in Exodus 20, Deuteronomy 5 and Isaiah 23:8.</p>
    </div>

</body>
</html>
"""

    with open("ornament_usage_by_pitch.html", "w", encoding="utf-8") as out_f:
        out_f.write(html_output)
    print("📈 Success! 'ornament_usage_by_pitch.html' compiled via direct file list extraction.")

if __name__ == "__main__":
    run_distribution_analysis()
