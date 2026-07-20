import os
import json
import html
import pandas as pd
from collections import Counter

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

def generate_html_matrix_payload(passage_df, book_id, chapter_id, max_chapter):
    """
    Processes the DataFrame and returns a string of HTML content.
    """

    w_col1 = "3%"   # Compressed number space
    w_col2 = "40%"  # Maximum space for full Hebrew lines
    w_col3 = "32%"  # Snug Left-Wing grid path
    w_col4 = "25%"  # Snug Right-Wing grid path
    is_poetry_flag = "0"
    clean_book = str(book_id).upper().strip()
    if clean_book in ["PSALMS", "PROVERBS"]:
        is_poetry_flag = "1"
            
    elif clean_book == "JOB":
        try:
            ch_num = int(chapter_id)
            # Job chapters 3 through 41 are the poetic core
            if 3 <= ch_num <= 41:
                is_poetry_flag = "1"
        except ValueError:
            pass

    # --- DYNAMIC FLUID GRID PERCENTAGE MAPPER ---
    if is_poetry_flag == "1":
        # Poetic Canvas: Give the expanded Hebrew text plenty of room, balancing the wings
        w_col1 = "5%"   # Verse number
        w_col2 = "30%"  # Expanded Hebrew text (Breathing room for full lines)
        w_col3 = "35%"  # Left-Wing Musical Grid
        w_col4 = "30%"  # Right-Wing Musical Grid
    try:
        current_ch = int(chapter_id)
    except ValueError:
        current_ch = 1
        
    # Calculate previous and next filenames matching your naming convention
    prev_ch_str = f"{current_ch - 1:03d}"
    next_ch_str = f"{current_ch + 1:03d}"
    
    prev_file = f"{book_id}_{prev_ch_str}_matrix.html"
    next_file = f"{book_id}_{next_ch_str}_matrix.html"
    
    # HTML Button Assembly (Now including the Index Home Link)
    prev_button = f'<a href="{prev_file}" class="nav-btn">◀ Prev</a>' if current_ch > 1 else '<span class="nav-btn disabled">◀ Prev</span>'
    home_button = '<a href="../index.html" class="nav-btn home-btn">📁 Index</a>'
    next_button = f'<a href="{next_file}" class="nav-btn">Next ▶</a>' if current_ch < max_chapter else '<span class="nav-btn disabled">Next ▶</span>'

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{book_id} {current_ch:03d} Music Shape</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #fdfdfd; color: #333; margin: 30px; padding-top: 50px; }}
        
        /* Sticky Top Navigation Bar Styles */
        .nav-bar {{ position: fixed; top: 0; left: 0; width: 100%; background: #ffffff; border-bottom: 2px solid #eaeaea; display: flex; justify-content: space-between; align-items: center; padding: 10px 30px; box-sizing: border-box; z-index: 1000; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }}
        .nav-title {{ font-weight: bold; font-size: 16px; color: #4A4A4A; }}
        .nav-cluster {{ display: flex; gap: 15px; }}
        .nav-btn {{ display: inline-block; padding: 6px 14px; background: #4A90E2; color: white; text-decoration: none; border-radius: 4px; font-size: 13px; font-weight: bold; transition: background 0.2s; }}
        .nav-btn:hover {{ background: #357ABD; }}
        .nav-btn.disabled {{ background: #dddddd; color: #888888; cursor: not-allowed; pointer-events: none; }}
        
        h1 {{ border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-top: 20px; }}
        .legend {{ display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 30px; background: #f5f5f5; padding: 15px; border-radius: 6px; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; font-size: 13px; font-weight: bold; }}
        .color-box {{ width: 20px; height: 20px; border-radius: 4px; border: 1px solid #999; }}
        .matrix-table {{ width: 100%; border-collapse: collapse; margin-top: 20px;}}
        .verse-row {{ border-bottom: 1px solid #ddd; display: table-row; }}
        .verse-label {{ font-weight: bold; font-size: 14px; padding: 12px 5px; background: #eaeaea; text-align: center; border-right: 2px solid #bbb; display: table-cell; vertical-align: middle; }}
        .text-label {{ font-size: 14px; font-weight: bold; padding: 10px; background: #fafdff; border-right: 2px solid #bbb; overflow: hidden; white-space: normal; direction: rtl; display: table-cell; vertical-align: middle; }}
        /* 📱 RESPONSIVE TABLET ENGINE: Triggers on iPad screen widths and below */
        @media (max-width: 1024px) {{
            .text-label {{
                max-width: 250px;           /* Clamp the width window */
                white-space: nowrap;        /* Force text to stay on a single row */
                overflow: hidden;           /* Hide the overflow text characters */
                text-overflow: ellipsis;    /* Append clean three-dot ... marking */
            }}
        }}
        /* Highlighting for Hebrew characters carrying te'amim above the text */
        .text-label span.ornamented-word {{
            font-size: 13pt;
            font-weight: bold;
            background-color: rgba(245, 166, 35, 0.15); /* Soft transparent orange tint */
            border-bottom: 2px dotted #F5A623;          /* Elegant dotted underline below text */
            padding: 0 2px;
            border-radius: 3px;
            transition: all 0.2s ease;
        }}
        
        /* Optional: Add a subtle text accent shift when the mouse hovers over it */
        .text-label span.ornamented-word:hover {{
            background-color: rgba(245, 166, 35, 0.3);
            cursor: help;
        }}

        .grid-cell {{ display: table-cell; vertical-align: middle; padding: 5px 0px; }}
        /* Assign explicit, fixed widths to the two musical columns to hold the straight vertical axis */
        /* --- PROVEN 3-DIGIT HIGH-DENSITY COLUMN MATH --- */
        /* Column 1: Accommodates up to verse 176 on a single line safely */
        td.grid-cell:nth-of-type(1), td.verse-label {{ 
            width: {w_col1}; 
        }}
        
        /* Column 2: Hebrew Text - Safe, wide allocation to prevent overwrite */
        td.grid-cell:nth-of-type(2), td.text-label {{ 
            width: {w_col2}; 
        }}
        
        /* Column 3: Left-Wing Musical Grid (Locks the center axis) */
        td.grid-cell:nth-of-type(3) {{ 
            width: {w_col3}; 
        }}
        
        /* Column 4: Right-Wing Musical Grid (Locks the center axis) */
        td.grid-cell:nth-of-type(4) {{ 
            width: {w_col4}; 
        }}
        .left-wing {{ display: flex; gap: 4px; justify-content: flex-end; min-width: 250px; border-right: 3px dashed #9B51E0; padding-right: 12px; }}
        .right-wing {{ display: flex; gap: 4px; justify-content: flex-start; padding-left: 12px; align-items: center; width: auto; overflow: visible; }}
        .pitch-cell {{ position: relative; padding: 4px 6px; border-radius: 4px; color: #fff; font-weight: bold; font-size: 11px; text-shadow: 1px 1px 1px rgba(0,0,0,0.4); border: 1px solid rgba(0,0,0,0.1); text-align: center; min-width: 28px; flex-shrink: 0; }}
        
        /* Interactive Highlight Enclosures */
        .half-verse-container {{ cursor: pointer; display: block; border-radius: 6px; padding: 4px; transition: all 0.15s ease; }}
        .half-verse-container:hover {{ background-color: rgba(0, 0, 0, 0.04); }} 
        .half-verse-container.highlighted-verse {{ background-color: #fff176 !important; box-shadow: 0 0 0 2px #fbc02d; }}
        .pitch-cell sup {{ 
            position: absolute;  /* Takes the symbol completely out of the normal layout flow */
            top: -2px;          /* Slides the symbol up right to the top inside edge of the box */
            right: 2px;         /* Tucks it cleanly into the top-right corner */
            font-size: 8px;     /* Keeps the ancient accent mark tiny and non-intrusive */
            line-height: 1; 
            vertical-align: baseline; /* Cancels out the browser's native text-shifting math */
        }}        .pivot-marker {{ border: 2px solid #000; box-shadow: 0 0 5px rgba(155, 81, 224, 0.6); }}
        .tuba-badge {{ background: #000; color: #fff; font-size: 10px; padding: 2px 5px; border-radius: 3px; margin-left: 20px; font-family: monospace; flex-shrink: 0; }}
        .nav-btn.home-btn {{ background: #4A4A4A; }}
        .nav-btn.home-btn:hover {{ background: #333333; }}    </style>
</head>
<body>
    <!-- Sticky Header Navigation -->
    <div class="nav-bar">
        <div class="nav-title">📖 {book_id.replace('_', ' ')} — Chapter {current_ch}</div>
        <div class="nav-cluster">
            {prev_button}
            {home_button}
            {next_button}
        </div>
    </div>

    <h1>🎼 SHV Aligned Melodic Matrix: {book_id} {current_ch}</h1>
    <p><i>Rows are aligned directly after the main structural cadence.</i></p>
    <h3>🎨 Color Mapping Legend (Tonic E4)</h3>
    <div class="legend">
    """
    for pitch, color in COLOR_PALETTE.items():
        if pitch not in ["UNKNOWN", "None"]:
            html_content += f'<div class="legend-item"><div class="color-box" style="background:{color};"></div><span>{pitch}</span></div>'
    
    html_content += """</div><table class="matrix-table">"""
    
    # -----------------------------------------------------------------
    # PRE-COMPUTE CHAPTER-WIDE MOTIF FREQUENCIES FOR DIGITAL APPARATUS
    # -----------------------------------------------------------------
    left_chapter_pool = []
    right_chapter_pool = []
    
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        v_rows = group[~group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        if v_rows.empty: continue
        r_notes = v_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        s_tokens = v_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        
        # Locate your critical baseline Atnah marker
        p_idx = r_notes.index("A4") if "A4" in r_notes else -1
        
        if p_idx != -1:
            # --- CATEGORIES 1 & 2: VERSE CONTAINS AN ATNAH ---
            for idx in range(p_idx, len(s_tokens)):
                p_idx = idx
                if not s_tokens[idx].endswith('-'): break
                
            l_str = " ".join([r_notes[x] for x in range(p_idx + 1) if x == 0 or r_notes[x] != r_notes[x-1]])
            r_str = " ".join([r_notes[x] for x in range(p_idx + 1, len(r_notes)) if x == p_idx + 1 or r_notes[x] != r_notes[x-1]])
            
            # Keep your original individual chapter printing lines exactly as they are
            if l_str: left_chapter_pool.append(l_str)
            if r_str: right_chapter_pool.append(r_str)
            
            # PINPOINT MASTER LOG ENTRY: Track left and right segments separately with your poetry flag
            if l_str:
                master_sequence_log.append({
                    "book": book_id, "chapter": int(chapter_id), "verse": int(vs),
                    "sequence_pattern": l_str,
                    "type": "Left Approach",
                    "is_poetry": is_poetry_flag
                })
            if r_str:
                master_sequence_log.append({
                    "book": book_id, "chapter": int(chapter_id), "verse": int(vs),
                    "sequence_pattern": r_str,
                    "type": "Right Resolution",
                    "is_poetry": is_poetry_flag
                })
        else:
            # --- CATEGORY 3: VERSE HAS NO ATNAH ---
            # Collapse the entire verse down to its true melodic skeleton
            no_atnah_notes = [r_notes[x] for x in range(len(r_notes)) if x == 0 or r_notes[x] != r_notes[x-1]]
            no_atnah_str = " ".join(no_atnah_notes)
            
            if no_atnah_str:
                master_sequence_log.append({
                    "book": book_id, "chapter": int(chapter_id), "verse": int(vs),
                    "sequence_pattern": no_atnah_str,
                    "type": "No Atnah",
                    "is_poetry": is_poetry_flag
                })
            
    left_global_counts = Counter(left_chapter_pool)
    right_global_counts = Counter(right_chapter_pool)
    poetic_fsharp4_total = 0

    # -----------------------------------------------------------------
    # SEQUENTIAL CHRONOLOGICAL ROW RENDERING
    # -----------------------------------------------------------------
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        group = group.reset_index(drop=True)
        if group.empty: continue
        
        valid_rows = group[group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan']) == False].reset_index(drop=True)
        if valid_rows.empty: continue
        
        raw_notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        ornaments_raw = valid_rows['ORNAMENT_NAME'].astype(str).str.lower().str.strip().tolist()
        
        has_global_atnah = "A4" in raw_notes
        has_global_ole = any("ole" in str(orn) for orn in ornaments_raw)
        
        left_raw, right_raw, left_ornaments, right_ornaments = [], [], [], []
        
        pause_raw_idx = -1
        pivot_pitch = None
        
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
            
        #if "F#4" in left_raw or "F#4" in right_raw:
            #poetic_fsharp4_total += 1

        left_notes, left_has_ole, left_has_zaqef = [], [], []
        left_has_zarqa, left_has_revia, left_has_telisha, left_has_pazer = [], [], [], []
        
        for i, note in enumerate(left_raw):
            orn_clean = str(left_ornaments[i]).lower().strip()
            is_zaqef = 'zaq' in orn_clean or 'qat' in orn_clean
            is_ole = 'ole' in orn_clean if not has_global_atnah else False
            is_zarqa = 'zar' in orn_clean or 'tsi' in orn_clean
            is_revia = 'rev' in orn_clean
            is_telisha = 'tel' in orn_clean
            is_pazer = 'paz' in orn_clean
            
            if not left_notes or left_notes[-1] != note:
                left_notes.append(note)
                left_has_ole.append(is_ole)
                left_has_zaqef.append(is_zaqef)
                left_has_zarqa.append(is_zarqa)
                left_has_revia.append(is_revia)
                left_has_telisha.append(is_telisha)
                left_has_pazer.append(is_pazer)
            else:
                if is_ole: left_has_ole[-1] = True
                if is_zaqef: left_has_zaqef[-1] = True
                if is_zarqa: left_has_zarqa[-1] = True
                if is_revia: left_has_revia[-1] = True
                if is_telisha: left_has_telisha[-1] = True
                if is_pazer: left_has_pazer[-1] = True
        right_notes, right_has_zaqef = [], []
        right_has_zarqa, right_has_revia, right_has_telisha, right_has_pazer = [], [], [], []
        
        for i, note in enumerate(right_raw):
            orn_clean_right = str(right_ornaments[i]).lower().strip()
            is_right_zaqef = 'zaq' in orn_clean_right or 'qat' in orn_clean_right
            is_right_zarqa = 'zar' in orn_clean_right or 'tsi' in orn_clean_right
            is_right_revia = 'rev' in orn_clean_right
            is_right_telisha = 'tel' in orn_clean_right
            is_right_pazer = 'paz' in orn_clean_right
            
            if not right_notes or right_notes[-1] != note:
                right_notes.append(note)
                right_has_zaqef.append(is_right_zaqef)
                right_has_zarqa.append(is_right_zarqa)
                right_has_revia.append(is_right_revia)
                right_has_telisha.append(is_right_telisha)
                right_has_pazer.append(is_right_pazer)
            else:
                if is_right_zaqef: right_has_zaqef[-1] = True
                if is_right_zarqa: right_has_zarqa[-1] = True
                if is_right_revia: right_has_revia[-1] = True
                if is_right_telisha: right_has_telisha[-1] = True
                if is_right_pazer: right_has_pazer[-1] = True

        tuba_pitch = None
        for idx in range(len(ornaments_raw)):
            if ornaments_raw[idx] == 'geresh':
                lookahead_limit = min(idx + 4, len(ornaments_raw))
                for next_idx in range(idx + 1, lookahead_limit):
                    if ornaments_raw[next_idx] == 'revia':
                        tuba_pitch = raw_notes[next_idx]
                        break
                if tuba_pitch: break
        
        # --- DYNAMIC TEXT EXTRACTION & POETRY ADJUSTMENT ---
        
        if len(name_parts) >= 2:
            chapter_id = name_parts[-1]       
            book_id = "_".join(name_parts[:-1]) 
        else:
            book_id = base_name
            chapter_id = "001"
        
        heb_clean_text = ""
        heb = ""
        if 'HEB_TEXT' in group.columns:
            valid_heb = group['HEB_TEXT'].dropna()
            if not valid_heb.empty:
                # 1. Pull the 100% clean, original text value directly out of the row cell
                raw_heb_string = html.unescape(str(valid_heb.iloc[0])).replace('\n', ' ').strip()
                
                # 2. Define the absolute Unicode character for the Atnah (Etnachta) accent mark
                ATNAH_CHAR = "\u0591"
                
                # 3. Dynamic Semantic Split: Look for the accent marker natively inside the Hebrew words
                if ATNAH_CHAR in raw_heb_string:
                    heb_words = raw_heb_string.split()
                    split_index = -1
                    
                    # Search through the words to locate exactly where the wishbone mark rests
                    for idx, word in enumerate(heb_words):
                        if ATNAH_CHAR in word:
                            split_index = idx + 1 # Set the cut boundary exactly after this word ends
                            break
                    
                    if split_index != -1 and split_index < len(heb_words):
                        left_part = " ".join(heb_words[:split_index])
                        right_part = " ".join(heb_words[split_index:])
                        heb = f"{left_part}<br>{right_part}"
                    else:
                        heb = raw_heb_string
                else:
                    # Safe fallback: If a verse has no Atnah mark, keep it intact on a single line
                    heb = raw_heb_string
                        
                # Master set matching your exact database names
                VALID_ORNAMENTS = {
                    'pashta', 'geresh', 'azla', 'tarsin', 'pazer', 'zaqef-qatan',
                    'zaqef-gadol', 'qadma', 'segol', 'z-qatan tsinnor', 'zarqa',
                    'tsinnor', 'revia z-qatan', 'telisha-qetana', 'telisha-gedola',
                    'qarne-farah', 'shalshelet', 'revia', 'ole', 'revia-mugrash',
                    'illuy', 'z-gadol pashta', 'pashta pashta', 'pazer azla',
                    'pazer z-qatan', 'z-qatan azla', 'azla pashta', 'azla t-qatana',
                    'revia pazer', 'azla z-qatan', 'tarsin revia', 'geresh t-gedola'
                }

                # 2. Extract true ornament names directly from your database row list
                #ornamented_tokens_set = set()
                #for r_idx, row in valid_rows.iterrows():
                #    o_name = str(row.get('ORNAMENT_NAME', '')).lower().strip()
                #    lyric_syll = str(row.get('LYRIC_SYLL', '')).strip().lower().replace('-', '')
                    
                #    if o_name in VALID_ORNAMENTS and lyric_syll:
                #       ornamented_tokens_set.add(lyric_syll)

                # 3. Assemble text spans by safely inspecting ornament matches

                # 4. BALANCED SPLIT MECHANISM: Bypasses LTR/RTL token drift safely
                # heb = " ".join(span_words)



        tuba_str = f'<span class="tuba-badge">📯 TUBA ({tuba_pitch})</span>' if tuba_pitch else ''
        
        left_key = " ".join(left_notes)
        right_key = " ".join(right_notes)
        l_cnt = left_global_counts[left_key]
        r_cnt = right_global_counts[right_key]
        
        left_badge = f'<span class="motif-count-badge">x{l_cnt}</span>' if l_cnt > 1 else ''
        right_badge = f'<span class="motif-count-badge">x{r_cnt}</span>' if r_cnt > 1 else ''
        
        clean_verse_display = int(float(vs))
        first_pitch = left_notes[0] if left_notes else (right_notes[0] if right_notes else "E4")
        bridge_marker = '<span class="entry-glyph-anchor">★</span>' if first_pitch != "E4" else ''
        
        # Calculate distinct sequence identifiers based on note combinations
        left_id_signature = "-".join(left_notes) if left_notes else "empty-left"
        right_id_signature = "-".join(right_notes) if right_notes else "empty-right"
                        
        html_content += f"""
        <tr class="verse-row">
            <td class="verse-label">{clean_verse_display}</td>
            <td class="text-label" title="{heb_clean_text}">{heb}</td>
            <td class="grid-cell">
                <div class="half-verse-container" data-half-verse-id="{left_id_signature}">
                    <div class="left-wing">
                        {bridge_marker}{left_badge}
        """
        
        if not left_notes:
            html_content += '<div class="pitch-cell" style="background: transparent; border: none; color: transparent; visibility: hidden;">&nbsp;</div>'
        else:
            for i, pitch in enumerate(left_notes):
                bg_color = COLOR_PALETTE.get(pitch, "#FFFFFF")
                text_color = "#333" if pitch in ["B4", "G#4"] else "#fff"
                is_edge = " pivot-marker" if i == len(left_notes) - 1 and pitch == pivot_pitch else ""
                
                ole_symbol = "<sup>&lt;</sup>" if left_has_ole[i] else ""
                zaqef_symbol = "<sup>:</sup>" if left_has_zaqef[i] else ""
                zarqa_symbol = "<sup>&#x223E;</sup>" if left_has_zarqa[i] else ""
                revia_symbol = "<sup>&#x25C6;</sup>" if left_has_revia[i] else ""
                telisha_symbol = "<sup>&#x26B2;</sup>" if left_has_telisha[i] else ""
                pazer_symbol = "<sup>~</sup>" if left_has_pazer[i] else ""
                
                ornament_string = f"{zarqa_symbol}{revia_symbol}{telisha_symbol}{pazer_symbol}" if i == 0 else ""
                    
                html_content += f'<div class="pitch-cell{is_edge}" style="background:{bg_color}; color:{text_color};">{ornament_string}{ole_symbol}{zaqef_symbol}{pitch}</div>'
            
        html_content += f"""
                    </div>
                </div>
            </td>
            <td class="grid-cell">
                <div class="half-verse-container" data-half-verse-id="{right_id_signature}">
                    <div class="right-wing">"""
        
        for i, pitch in enumerate(right_notes):
            bg_color = COLOR_PALETTE.get(pitch, "#FFFFFF")
            text_color = "#333" if pitch in ["B4", "G#4"] else "#fff"
            
            zaqef_symbol = "<sup>:</sup>" if right_has_zaqef[i] else ""
            zarqa_symbol = "<sup>&#x223E;</sup>" if right_has_zarqa[i] else ""
            revia_symbol = "<sup>&#x25C6;</sup>" if right_has_revia[i] else ""
            telisha_symbol = "<sup>&#x26B2;</sup>" if right_has_telisha[i] else ""
            pazer_symbol = "<sup>~</sup>" if right_has_pazer[i] else ""
            
            right_ornament_string = f"{zarqa_symbol}{revia_symbol}{telisha_symbol}{pazer_symbol}" if i == 0 else ""
                
            html_content += f'<div class="pitch-cell" style="background:{bg_color}; color:{text_color};">{right_ornament_string}{zaqef_symbol}{pitch}</div>'
            
        # FIX: Added </div> right after right_badge to safely close the half-verse container wrapper
        html_content += f"{tuba_str}{right_badge}</div></div></td></tr>"
        
    footer_tally_str = f'<div class="poetic-footer-tally">Poetic Structural Summary: {poetic_fsharp4_total} verses carry F#4 accents in this score.</div>' if poetic_fsharp4_total > 0 else ''
    
    html_content += """
    </table>
    
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const structuralBlocks = document.querySelectorAll('.half-verse-container');
        structuralBlocks.forEach(element => {
            element.addEventListener('click', (event) => {
                const identifier = element.getAttribute('data-half-verse-id');
                if(identifier === "empty-left" || identifier === "empty-right") return;
                
                const isAlreadySelected = element.classList.contains('highlighted-verse');
                structuralBlocks.forEach(el => el.classList.remove('highlighted-verse'));
                
                if(!isAlreadySelected) {
                    // TRIPLE UP the braces so Python leaves the JavaScript variable intact
                    const structuralMatches = document.querySelectorAll(`[data-half-verse-id="${identifier}"]`);
                    structuralMatches.forEach(el => el.classList.add('highlighted-verse'));
                }
            });
        });
    });
    </script>
</body>
</html>"""
    return html_content
    


if __name__ == "__main__":
    ROOT_DIR = ".." 
    
    print(f"🚀 STARTING SYSTEM-WIDE MASS PRODUCTION GRID COMPILER")
    print(f"Scanning from root base: {os.path.abspath(ROOT_DIR)}\n")
    
    success_count = 0
    error_count = 0
    master_sequence_log = []  # Caches structural records across all 929 chapters
    
    STOP_AFTER_FIRST_FILE = False  # Toggle to False when ready for mass production
            
    # --- DYNAMIC CHAPTER MAPPER ---
    # Tracks the highest chapter number found for each book in the directory
    book_max_chapters = {}
    
    for current_dir, subfolders, files in os.walk(ROOT_DIR):
        if "analysis_scripts" in current_dir or "Test-Scripts" in current_dir:
            continue
        for file in files:
            if file.upper().endswith(".JSON"):
                base_name, _ = os.path.splitext(file)
                name_parts = base_name.split("_")
                if len(name_parts) >= 2:
                    try:
                        ch_num = int(name_parts[-1])
                        b_id = "_".join(name_parts[:-1])
                        # Keep track of the highest integer chapter seen for this book
                        if b_id not in book_max_chapters or ch_num > book_max_chapters[b_id]:
                            book_max_chapters[b_id] = ch_num
                    except ValueError:
                        pass

        # Flag to signal the outer directory loop to stop
        break_outer_loop = False
        for file in files:
            if file.upper().endswith(".JSON"):
                json_path = os.path.join(current_dir, file)
                
                base_name, _ = os.path.splitext(file)
                name_parts = base_name.split("_")
                
                # --- MUSICOLOGICAL STRING RE-ENGINEERING ---
                # Safe allocation for numerical prefix books like 1_CHRONICLES or 2_SAMUEL
                if len(name_parts) >= 2:
                    chapter_id = name_parts[-1]       # Always pluck the absolute last element as the chapter
                    book_id = "_".join(name_parts[:-1]) # Join all preceding fragments as the book identity
                else:
                    book_id = base_name
                    chapter_id = "001"
                
                output_html_name = f"{base_name}_matrix.html"
                output_html_path = os.path.join(current_dir, output_html_name)
                
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                    
                    # --- HARDEED PAYLOAD LOCATOR ENGINE ---
                    items_list = None
                    
                    # Strategy A: Broad recursive-style fallback scanning
                    if isinstance(raw_data, dict):
                        if "items" in raw_data:
                            items_list = raw_data["items"]
                        elif "results" in raw_data:
                            if isinstance(raw_data["results"], dict) and "items" in raw_data["results"]:
                                items_list = raw_data["results"]["items"]
                            elif isinstance(raw_data["results"], list) and len(raw_data["results"]) > 0:
                                if isinstance(raw_data["results"][0], dict) and "items" in raw_data["results"][0]:
                                    items_list = raw_data["results"][0]["items"]
                                    
                    elif isinstance(raw_data, list) and len(raw_data) > 0:
                        # Strategy B: If Oracle wrapped the root object in an outer array wrapper
                        first_item = raw_data[0]
                        if isinstance(first_item, dict):
                            if "items" in first_item:
                                items_list = first_item["items"]
                            elif "results" in first_item:
                                if isinstance(first_item["results"], dict) and "items" in first_item["results"]:
                                    items_list = first_item["results"]["items"]
                                elif isinstance(first_item["results"], list) and len(first_item["results"]) > 0:
                                    if "items" in first_item["results"][0]:
                                        items_list = first_item["results"][0]["items"]

                    # Strategy C: Absolute emergency fallback for key-flattened arrays
                    if items_list is None and isinstance(raw_data, dict):
                        for value in raw_data.values():
                            if isinstance(value, dict) and "items" in value:
                                items_list = value["items"]
                                break
                    
                    if items_list is None:
                        # Log the filename clearly so you can identify rogue non-concordance configurations
                        print(f"⚠️  Skipping non-matrix file: {file}")
                        continue
                        
                    # Create Pandas Dataframe and execute matrix building engine
                    df = pd.DataFrame(items_list)
                    df.columns = df.columns.str.upper()
                    
                    # Determine the maximum chapter for this book (default to 150 if not found)
                    max_chapter = book_max_chapters.get(book_id, 150)

                    # Generate the page layout content via backend matrix engine
                    page_html = generate_html_matrix_payload(df, book_id, chapter_id, max_chapter)
                    
                    # Loop through the parsed verses in the active dataframe to steal the compiled vectors
                    for (ch, vs), group in df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
                        # Extract the exact same clean notes your loop just processed
                        v_notes = [str(n).strip() for n in group['SYLL_NOTE'].tolist() if str(n).strip() not in ['None', '', 'nan']]
                        if v_notes:
                            # Reconstruct the text-painting approach directly to the Atnah if it exists
                            if "A4" in v_notes:
                                # 1. Collapse the verse down to its true melodic skeleton
                                compressed_melody = []
                                for note in v_notes:
                                    if not compressed_melody or compressed_melody[-1] != note:
                                        compressed_melody.append(note)
                                
                    # Save HTML file directly into the same subdirectory as the JSON source
                    with open(output_html_path, "w", encoding="utf-8") as out_f:
                        out_f.write(page_html)
                        
                    print(f"✅ Compiled: {os.path.basename(current_dir)} -> {output_html_name}")
                    success_count += 1

                except Exception as e:
                    print(f"❌ Error processing file {file}: {str(e)}")
                    error_count += 1

                # --- ADD THIS EXIT CHECK AT THE END OF THE FILE PROCESS ---
                if STOP_AFTER_FIRST_FILE and success_count >= 1:
                    print("\n🛑 Test Mode Active: Halting processing after the first successful file.")
                    break_outer_loop = True
                    break  # This breaks the inner 'files' loop
                    
        # Check if the inner loop signaled an exit to break the outer directory crawler
        if break_outer_loop:
            break                    

    print(f"\n=======================================================")
    print(f"🏭 MASS PRODUCTION BUILD COMPLETE")
    print(f"   Successfully compiled: {success_count} HTML Matrices")
    print(f"   Errors encountered:    {error_count}")
    print(f"=======================================================")
    # --- MASTER SEQUENCE EXTRACER WRITER ---
    if master_sequence_log:
        from collections import Counter
        sequence_report_path = "global_approaches.txt"
        analysis_df = pd.DataFrame(master_sequence_log)
        
        with open(sequence_report_path, "w", encoding="utf-8") as rep_f:
            rep_f.write("========================================================================\n")
            rep_f.write("          TANACH CALIBRATED MELODIC STRUCTURAL REPORT                   \n")
            rep_f.write("========================================================================\n\n")
            rep_f.write(f"Total Structural Cadence Elements Logged: {len(analysis_df)}\n\n")
            
            # --- SECTION 1: POETIC SYSTEM (is_poetry_flag == "1") ---
            rep_f.write("=== [ SECTION I: POETIC ACCENT SYSTEM (Job, Proverbs, Psalms) ] ===\n\n")
            poet_df = analysis_df[analysis_df["is_poetry"] == "1"]
            
            for sub_type in ["Left Approach", "Right Resolution", "No Atnah"]:
                sub_df = poet_df[poet_df["type"] == sub_type]
                counts = Counter(sub_df["sequence_pattern"])
                rep_f.write(f"--- Ranked Patterns: Poetic {sub_type} (Total: {len(sub_df)}) ---\n")
                
                for pattern, count in counts.most_common(15): # Displays top 15 trends
                    pct = (count / len(sub_df)) * 100 if len(sub_df) > 0 else 0
                    rep_f.write(f" 🎵 [ {pattern} ] -> Used {count} times ({pct:.1f}%)\n")
                rep_f.write("\n")
                
            rep_f.write("\n" + "="*72 + "\n\n")
            
            # --- SECTION 2: PROSE SYSTEM (is_poetry_flag == "0") ---
            rep_f.write("=== [ SECTION II: PROSE ACCENT SYSTEM (The 21 Books) ] ===\n\n")
            prose_df = analysis_df[analysis_df["is_poetry"] == "0"]
            
            for sub_type in ["Left Approach", "Right Resolution", "No Atnah"]:
                sub_df = prose_df[prose_df["type"] == sub_type]
                counts = Counter(sub_df["sequence_pattern"])
                rep_f.write(f"--- Ranked Patterns: Prose {sub_type} (Total: {len(sub_df)}) ---\n")
                
                for pattern, count in counts.most_common(15):
                    pct = (count / len(sub_df)) * 100 if len(sub_df) > 0 else 0
                    rep_f.write(f" 📖 [ {pattern} ] -> Used {count} times ({pct:.1f}%)\n")
                rep_f.write("\n")
                
        print(f"📊 Success! Detailed structural report saved to: {sequence_report_path}")
        # --- THIS IS THE CALL TO YOUR NEW DASHBOARD MATRIX ---
        # Import your standalone visualization engine file
        import generate_reconciliation_matrix as grm
        
        # Execute the HTML builder by passing it your master log array
        grm.build_reconciliation_matrix(master_sequence_log)
