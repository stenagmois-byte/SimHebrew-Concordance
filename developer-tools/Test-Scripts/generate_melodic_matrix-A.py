import os
import json
import html
import pandas as pd

# Define a distinct, vibrant color palette for each scale degree (Tonic E4 = 1)
COLOR_PALETTE = {
    "C4":  "#4A4A4A",  # Low Sixth (Dark Grey)
    "D4":  "#FF851B",  # Sub-tonic / Springboard Vault (Coral)
    "E4":  "#4A90E2",  # Tonic Baseline (Blue)
    "F4":  "#F5A623",  # Prose Supertonic (Orange)
    "F#4": "#D0021B",  # Poetic Supertonic / Sharp variant (Red)
    "G4":  "#7ED321",  # Poetic Mediant / Recitation (Green)
    "G#4": "#B8E986",  # Prose Mediant (Light Green)
    "A4":  "#9B51E0",  # Subdominant / Caesura / Pivot (Purple)
    "B4":  "#F8E71C",  # Dominant / Proclamation (Yellow)
    "C5":  "#50E3C2",  # High Sixth / Appeal / Explosion (Teal)
    "None": "#EEEEEE", # Empty / Spacer (Light Grey)
    "UNKNOWN": "#FFFFFF"
}

def generate_html_matrix(passage_df, book_id, chapter_id, output_html="matrix_visualization.html"):
    """
    Generates an HTML matrix that splits and aligns rows right AFTER the 
    subdominant (A4). Strips leading zeros from the chapter ID for a clean title display.
    """
    # Convert chapter_id to an integer to cleanly strip high-order zeros (e.g., "001" -> 1)
    clean_chapter_num = int(chapter_id)
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{book_id} {clean_chapter_num} Music Shape</title>
    <style>

        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #fdfdfd; color: #333; margin: 30px; }}
        h1 {{ border-bottom: 2px solid #ccc; padding-bottom: 10px; }}
        .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; background: #f5f5f5; padding: 15px; border-radius: 6px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 13px; font-weight: bold; }}
        .color-box {{ width: 20px; height: 20px; border-radius: 4px; border: 1px solid #999; }}
        
        /* Structural Alignment Grid Layout */
        /* Replace these three CSS rules to fix the window cut-off */
        .matrix-table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        .verse-row {{ border-bottom: 1px solid #ddd; display: table-row; }}
        .verse-label {{ width: 90px; font-weight: bold; font-size: 14px; padding: 12px 10px; background: #eaeaea; text-align: center; border-right: 2px solid #bbb; display: table-cell; vertical-align: middle; }}
        .text-label {{ width: 250px; font-size: 13px; padding: 10px; background: #fafdff; border-right: 2px solid #bbb; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; direction: rtl; display: table-cell; vertical-align: middle; }}
        
        /* The Alignment Containers */
        .grid-cell {{ display: table-cell; vertical-align: middle; padding: 5px 10px; }}
        .left-wing {{ display: flex; gap: 4px; justify-content: flex-end; min-width: 250px; border-right: 3px dashed #9B51E0; padding-right: 12px; }}
        .right-wing {{ display: flex; gap: 4px; justify-content: flex-start; padding-left: 12px; align-items: center; width: auto; overflow: visible; }}
        
        .pitch-cell {{ padding: 6px 10px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 12px; text-shadow: 1px 1px 1px rgba(0,0,0,0.4); border: 1px solid rgba(0,0,0,0.1); text-align: center; min-width: 35px; flex-shrink: 0; }}
        .pivot-marker {{ border: 2px solid #000; box-shadow: 0 0 5px rgba(155, 81, 224, 0.6); }}
        .tuba-badge {{ background: #000; color: #fff; font-size: 10px; padding: 2px 5px; border-radius: 3px; margin-left: 20px; font-family: monospace; flex-shrink: 0; }}
    </style>
</head>
<body>
    <h1>🎼 SHV Aligned Melodic Matrix: {book_id} (Chapter {clean_chapter_num})</h1>
    <p><i>Rows are structurally aligned directly to the right of the first Subdominant (A4) phrase boundary. The vertical dashed line marks the hemistich divide.</i></p>
    
    <h3>🎨 Color Mapping Legend (Tonic E4 = 1)</h3>
    <div class="legend">
    """
    
    for pitch, color in COLOR_PALETTE.items():
        if pitch not in ["UNKNOWN", "None"]:
            html_content += f'<div class="legend-item"><div class="color-box" style="background:{color};"></div><span>{pitch}</span></div>'
    
    html_content += """
    </div>
    <table class="matrix-table">
    """
    
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        group = group.reset_index(drop=True)
        if group.empty: continue
        
        # 1. Cleanly pull chronological data rows while filtering empty filler notes
        valid_rows = group[group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan']) == False].reset_index(drop=True)
        if valid_rows.empty: continue
        
        raw_notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        ornaments_raw = valid_rows['ORNAMENT_NAME'].astype(str).str.lower().str.strip().tolist()
        
        # GLOBAL PRE-SCAN: Establish structural capabilities before reading lines
        has_global_atnah = "A4" in raw_notes
        has_global_ole = any("ole" in str(orn) for orn in ornaments_raw)
        
        pause_raw_idx = -1
        pivot_pitch = None
        
        # 2. MATCH AND CALCULATE PRECISE CADENCE PIVOT BOUNDARIES
        if has_global_atnah:
            pivot_pitch = "A4"
            first_target_idx = raw_notes.index("A4")
            pause_raw_idx = first_target_idx
            for idx in range(first_target_idx, len(syllables)):
                pause_raw_idx = idx
                if not syllables[idx].endswith('-'):
                    break
                    
        elif has_global_ole and "F#4" in raw_notes:
            ole_marker_idx = -1
            for idx in range(len(ornaments_raw)):
                if "ole" in ornaments_raw[idx]:
                    ole_marker_idx = idx
                    break
            
            target_fsharp_idx = -1
            if ole_marker_idx != -1:
                for idx in range(ole_marker_idx, len(raw_notes)):
                    if raw_notes[idx] == "F#4":
                        target_fsharp_idx = idx
                        break
            
            if target_fsharp_idx != -1:
                pivot_pitch = "F#4"
                pause_raw_idx = target_fsharp_idx
                for idx in range(target_fsharp_idx, len(syllables)):
                    pause_raw_idx = idx
                    if not syllables[idx].endswith('-'):
                        break
        
        # 3. PARTITION MATRIX CONTAINERS (Unchanged from prior structural build)
        left_raw = []
        right_raw = []
        left_ornaments = []
        right_ornaments = []
        
        if pause_raw_idx != -1:
            left_raw = raw_notes[:pause_raw_idx + 1]
            right_raw = raw_notes[pause_raw_idx + 1:]
            left_ornaments = ornaments_raw[:pause_raw_idx + 1]
            right_ornaments = ornaments_raw[pause_raw_idx + 1:]
        else:
            left_raw = []
            right_raw = raw_notes
            left_ornaments = []
            right_ornaments = ornaments_raw
            
        # 4. GENRE-SPECIFIC ORNAMENT COMPRESSION (HARDENED STRING SCANNER)
        left_notes = []
        left_has_ole = []
        left_has_zaqef = []
        
        for i, note in enumerate(left_raw):
            # Clean and normalize the ornament string to catch formatting variations
            orn_clean = str(left_ornaments[i]).lower().strip()
            
            # Catch 'zaqef', 'qaton', 'zaq', or 'qat' anywhere in the tag
            is_zaqef = 'zaq' in orn_clean or 'qat' in orn_clean
            is_ole = 'ole' in orn_clean if not has_global_atnah else False
            
            if not left_notes or left_notes[-1] != note:
                # Fresh pitch block initialization
                left_notes.append(note)
                left_has_ole.append(is_ole)
                left_has_zaqef.append(is_zaqef)
            else:
                # Continuation syllable scan
                if is_ole:
                    left_has_ole[-1] = True
                if is_zaqef:
                    left_has_zaqef[-1] = True
                
        right_notes = []
        right_has_zaqef = []
        
        for i, note in enumerate(right_raw):
            orn_clean_right = str(right_ornaments[i]).lower().strip()
            is_right_zaqef = 'zaq' in orn_clean_right or 'qat' in orn_clean_right
            
            if not right_notes or right_notes[-1] != note:
                right_notes.append(note)
                right_has_zaqef.append(is_right_zaqef)
            else:
                if is_right_zaqef:
                    right_has_zaqef[-1] = True

        # 5. Check for Tuba (Geresh lookahead sequence)
        ornaments = group['ORNAMENT_NAME'].astype(str).str.lower().str.strip().tolist()
        tuba_pitch = None
        for idx in range(len(ornaments)):
            if ornaments[idx] == 'geresh':
                lookahead_limit = min(idx + 4, len(ornaments))
                for next_idx in range(idx + 1, lookahead_limit):
                    if ornaments[next_idx] == 'revia':
                        group_notes = [str(n).strip() for n in group['SYLL_NOTE'].tolist()]
                        # Pad check to prevent index out of bounds on raw arrays
                        if next_idx < len(group_notes):
                            tuba_pitch = group_notes[next_idx]
                        break
                if tuba_pitch: break

        # 6. Handle Hebrew Text Snippet Safely
        heb = ""
        if 'HEB_TEXT' in group.columns:
            valid_heb = group['HEB_TEXT'].dropna()
            if not valid_heb.empty:
                # Target the raw string at index 0 explicitly
                heb = html.unescape(str(valid_heb.iloc[0])).replace('\n', ' ').strip()
                # Truncate text cleanly so it acts as a neat scannable label
                heb = (heb[:35] + '...') if len(heb) > 35 else heb

        # 7. Generate HTML Table Row Structure
        tuba_str = f'<span class="tuba-badge">📯 TUBA ({tuba_pitch})</span>' if tuba_pitch else ''
        
        html_content += f"""
        <tr class="verse-row">
            <td class="verse-label">Verse {vs}</td>
            <td class="text-label" title="{heb}">{heb}</td>
            <td class="grid-cell">
                <div class="left-wing">
        """
        
        # Draw Left Wing cells (Notes leading up to and including the pivot)
        if not left_notes:
            # Force empty space recognition if the line has no cadence
            html_content += '<div class="pitch-cell" style="background: transparent; border: none; color: transparent; visibility: hidden;">&nbsp;</div>'
        else:
            for i, pitch in enumerate(left_notes):
                bg_color = COLOR_PALETTE.get(pitch, "#FFFFFF")
                text_color = "#333" if pitch in ["B4", "G#4"] else "#fff"
                is_edge = " pivot-marker" if i == len(left_notes) - 1 and pitch == pivot_pitch else ""
                
                # --- ADD THESE TWO LINES BACK IN ---
                ole_symbol = "<sup>&lt;</sup>" if left_has_ole[i] else ""
                zaqef_symbol = "<sup>:</sup>" if left_has_zaqef[i] else ""
                
                # --- UPDATE THIS STRING TO INCLUDE {zaqef_symbol} ---
                html_content += f'<div class="pitch-cell{is_edge}" style="background:{bg_color}; color:{text_color};">{pitch}{ole_symbol}{zaqef_symbol}</div>'
            
        html_content += """
                </div>
            </td>
            <td class="grid-cell" style="width: 100%;">
                <div class="right-wing">
        """
        
        # Draw Right Wing cells safely
        for i, pitch in enumerate(right_notes):
            bg_color = COLOR_PALETTE.get(pitch, "#FFFFFF")
            text_color = "#333" if pitch in ["B4", "G#4"] else "#fff"
            
            # Right wing only renders prose zaqef-qaton markers; ole is omitted entirely
            zaqef_symbol = "<sup>:</sup>" if right_has_zaqef[i] else ""
            
            html_content += f'<div class="pitch-cell" style="background:{bg_color}; color:{text_color};">{pitch}{zaqef_symbol}</div>'
           
        html_content += f"""
                    {tuba_str}
                </div>
            </td>
        </tr>
        """
        
    html_content += """
    </table>
</body>
</html>
"""
    with open(output_html, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"📊 Aligned Visual Matrix Dashboard saved to: {os.path.abspath(output_html)}")


if __name__ == "__main__":
    # --- VARIABLE INPUT SECTION ---
    TARGET_BOOK = "ISAIAH"        # Change to "PSALMS", "GENESIS", "PROVERBS", etc.
    TARGET_CHAPTER = "039"         # Always ensure 3 digits ("001", "015", "136")
    
    # 1. Standardise the filename based on your export pattern (BOOK_CHAP.json)
    file_name = f"{TARGET_BOOK}_{TARGET_CHAPTER.zfill(3)}.json"
    
    # 2. DYNAMIC PATH RESOLUTION:
    # Looks directly into a parallel folder matching the EXACT name of the target book
    json_path = os.path.join("..", TARGET_BOOK, file_name)
    
    # --- SPECIAL FOLDER NAME MAPPING (IF APPLICABLE) ---
    # If your local directory name uses spaces (like "The Psalms"), map it here:
    if TARGET_BOOK == "PSALMS":
        json_path = os.path.join("..", "The Psalms", file_name)
        
    output_html_file = f"{TARGET_BOOK}_{TARGET_CHAPTER}_matrix.html"
    
    print(f"Targeting directory: {TARGET_BOOK}")
    print(f"Searching for file payload at: {json_path}")
    
    if not os.path.exists(json_path):
        print(f"❌ Error: File not found at {json_path}")
        print("Please check your parallel directory spelling and capitalization exactly.")
    else:
        with open(json_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            
        items_list = None
        working_data = raw_data if not isinstance(raw_data, list) else raw_data[0]
            
        if isinstance(working_data, dict):
            if "results" in working_data and isinstance(working_data["results"], dict):
                items_list = working_data["results"].get("items")
            elif "results" in working_data and isinstance(working_data["results"], list):
                if len(working_data["results"]) > 0 and "items" in working_data["results"][0]:
                    items_list = working_data["results"][0]["items"]
            else:
                items_list = working_data.get("items")

        if items_list is None:
            print("❌ Error: Could not locate 'items' inside JSON wrapper.")
        else:
            print(f"Found data payload! Unpacking {len(items_list)} rows...")
            selected_passage = pd.DataFrame(items_list)
            selected_passage.columns = selected_passage.columns.str.upper()
            generate_html_matrix(selected_passage, TARGET_BOOK, TARGET_CHAPTER, output_html=output_html_file)
