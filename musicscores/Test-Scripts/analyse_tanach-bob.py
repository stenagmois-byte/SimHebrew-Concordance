import json
import pandas as pd
import html

# Updated Senses reflecting prose/poetry tone
PROSE_DICT = {
    'E4': {'degree': 1, 'name': 'Tonic', 'sense': 'Home base / lower tessitura'},
    'F4': {'degree': 2, 'name': 'Supertonic', 'sense': 'Pending / leading to Mediant or Tonic E4'},
    'G4': {'degree': 3, 'name': 'Mediant', 'sense': 'Anticipation of cadence'},
    'G#4': {'degree': 3, 'name': 'Mediant', 'sense': 'Anticipation of cadence'},
    'A4': {'degree': 4, 'name': 'Subdominant', 'sense': 'Secure rest / confidence'},
    'B4': {'degree': 5, 'name': 'Dominant', 'sense': 'Proclamation / narrative engine'},
    'C5': {'degree': 6, 'name': 'Sixth Degree', 'sense': 'Heightened emotion / appeal'},
    'D4': {'degree': 7, 'name': 'Sub-Tonic', 'sense': 'Low preparation for a rising phrase'},
    'C4': {'degree': 6, 'name': 'Low Sixth', 'sense': 'Low preparation / structural drop'}
}

POETIC_DICT = {
    'E4': {'degree': 1, 'name': 'Tonic', 'sense': 'Home base / lower tessitura'},
    'F4': {'degree': 2, 'name': 'Supertonic', 'sense': 'Brief rest / pending tension'},
    'F#4': {'degree': 2, 'name': 'Supertonic Sharp', 'sense': 'Cadence if preceded by Ole'},
    'G4': {'degree': 3, 'name': 'Mediant', 'sense': 'Mid-range recitation / some intensity'},
    'A4': {'degree': 4, 'name': 'Subdominant', 'sense': 'Secure rest / confidence'},
    'B4': {'degree': 5, 'name': 'Dominant', 'sense': 'Proclamation / narrative engine)'},
    'C5': {'degree': 6, 'name': 'Sixth Degree', 'sense': 'Heightened emotion / appeal'},
    'D4': {'degree': 7, 'name': 'Sub-Tonic', 'sense': 'Low preparation boundary for a rising phrase'}
}

def analyze_complete_tanakh(file_path):
    print("Loading master database into memory...")
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    results = raw_data.get('results', [])
    if isinstance(results, list) and len(results) > 0:
        items = results[0].get('items', []) if isinstance(results[0], dict) else []
    elif isinstance(results, dict):
        items = results.get('items', [])
    else:
        items = []
    
    if not items:
        print("Error: No data records found.")
        return
        
    df = pd.DataFrame(items)
    df.columns = [col.upper() for col in df.columns]
    
    # 1. Enforce strict numerical data types so text-sorting doesn't mangle digits
    # (Prevents sequence 10 from coming before sequence 2)
    df['BOOK_SEQ_NO'] = pd.to_numeric(df['BOOK_SEQ_NO'], errors='coerce')
    df['XML_SEQ'] = pd.to_numeric(df['XML_SEQ'], errors='coerce')
    
    # Keep chapter and verse codes as padded text, but we ensure they handle formatting
    df['CHAPTER_CD'] = df['CHAPTER_CD'].astype(str).str.zfill(3)
    df['VERSE_CD'] = df['VERSE_CD'].astype(str).str.zfill(3)
    
    print("Sorting syllables into canonical order...")
    # This correctly lines up Genesis (1), 1 Chronicles (13), Ezra (15), etc.
    df = df.sort_values(by=['BOOK_SEQ_NO', 'CHAPTER_CD', 'VERSE_CD', 'XML_SEQ']).reset_index(drop=True)
    
    output_lines = []
    def log(text=""): output_lines.append(text)

    print("Analyzing all verses across the narrative map...")
    for (seq_no, book_cd, ch_cd, vs_cd), group in df.groupby(
        ['BOOK_SEQ_NO', 'BOOK_CD', 'CHAPTER_CD', 'VERSE_CD'], 
        sort=False
    ):        
        group_reset = group.reset_index(drop=True)
        
        # Pull the Hebrew Text safely from the first syllable
        # Extract Hebrew Text safely
        heb_text = "No Hebrew text attached"
        if 'HEB_TEXT' in group_reset.columns:
            valid_heb = group_reset['HEB_TEXT'].dropna()
            if not valid_heb.empty:
                heb_text = html.unescape(valid_heb.iloc[0].replace('\n', ' '))

        log("\n" + "="*90)
        log(f"ANALYSIS FOR: {book_cd} {int(ch_cd)}:{int(vs_cd)}")
        log(f"HEBREW: {heb_text}")
        log("="*90)
        
        # Determine Dialect Scale
        unique_pitches = set(group_reset['SYLL_NOTE'].dropna().unique())
        has_prose_marker = 'G#4' in unique_pitches or 'C4' in unique_pitches
        has_poetic_marker = 'F#4' in unique_pitches
        is_explicit_poetry = 'POETRY' in group_reset.columns and str(group_reset['POETRY'].iloc[0]) == '1'
        
        if has_prose_marker:
            detected_genre = "PROSE"
            mapping_dict = PROSE_DICT
        elif has_poetic_marker or is_explicit_poetry:
            detected_genre = "POETRY"
            mapping_dict = POETIC_DICT
        else:
            detected_genre = "PROSE"
            mapping_dict = PROSE_DICT
            
        log(f"SYSTEM GENRE CLASSIFICATION: {detected_genre}")
        
        group_reset['DEGREE'] = group_reset['SYLL_NOTE'].map(lambda x: mapping_dict.get(x, {}).get('degree', 0))
        group_reset['SENSE'] = group_reset['SYLL_NOTE'].map(lambda x: mapping_dict.get(x, {}).get('sense', 'Unknown'))
        
        # Calculate Note Runs/Plateaus (With Implied E4 Correction)
        note_runs = []
        current_note, count, start_idx = None, 0, 0
        for idx, row in group_reset.iterrows():
            val = row['SYLL_NOTE']
            # Implicit Tonic Correction: If null or empty, it defaults to E4
            note_str = str(val).strip() if (pd.notna(val) and str(val).strip() != "") else "E4"
            
            if note_str == current_note: 
                count += 1
            else:
                if current_note is not None: 
                    note_runs.append((current_note, count, start_idx, idx-1))
                current_note = note_str
                count = 1
                start_idx = idx
        if current_note is not None: 
            note_runs.append((current_note, count, start_idx, len(group_reset)-1))
            
        contour_elements = [f"[{str(n)}x{c}_PLATEAU]" if c >= 4 else str(n) for n, c, _, _ in note_runs]
        log(f"COMPRESSED MELODIC OUTLINE: {' -> '.join(map(str, contour_elements))}")
        
        # Run Pattern Recognition Detectors
        discoveries = []
        if detected_genre == "POETRY":
            # Test 1: The Minor Seventh Rocket (D4 springboard straight to High C5)
            for i in range(len(note_runs) - 1):
                if note_runs[i][0] == 'D4' and note_runs[i+1][0] == 'C5':
                    discoveries.append("[MINOR SEVENTH ROCKET OF JOY/APPEAL] (Sudden vault from sub-tonic D4 springboard straight to high C5)")
            
            # Test 2: Intense Mediant Recitation
            for note, cnt, s_idx, e_idx in note_runs:
                if note == 'G4' and cnt >= 5:
                    words = "".join([str(t) for t in group_reset['LYRIC_SYLL'].loc[s_idx:e_idx]])
                    discoveries.append(f"[INTENSE MEDIANT RECITATION] (G4 held for {cnt} syllables on: '{words}')")
            
            # Test 3: Poetic Cadence Check on F#4 via Ole
            for note, cnt, s_idx, e_idx in note_runs:
                if note == 'F#4':
                    # Scan the ornaments column within this specific note run
                    ornaments_in_run = set(group_reset['ORNAMENT_NAME'].loc[s_idx:e_idx].dropna().str.upper())
                    if 'OLE' in ornaments_in_run or 'OLEH' in ornaments_in_run:
                        discoveries.append(f"[FORMAL POETIC F#4 CADENCE] (F#4 confirmed as a true structural cadence via preceding Ole ornament)")

        elif detected_genre == "PROSE":
            # Test 4: Cosmic Creation Blueprint Check (e -> g# -> B -> A)
            if len(note_runs) >= 4:
                unique_degrees = [PROSE_DICT.get(p[0], {}).get('degree', 0) for p in note_runs[:4]]
                if tuple(unique_degrees) == (1, 3, 5, 4):
                    discoveries.append("[NEW CREATION MOTIF] (Initial phrase mirrors Genesis 1:1 contour e -> g# -> B -> A)")
                
            # Test 5: The Minor Seventh Rocket (D4 springboard straight to High C5)
            for i in range(len(note_runs) - 1):
                if note_runs[i][0] == 'D4' and note_runs[i+1][0] == 'C5':
                    discoveries.append("[MINOR SEVENTH ROCKET OF JOY/APPEAL] (Sudden vault from sub-tonic D4 springboard straight to high C5)")
            
            # Test 6: The Octave Leap (C4 springboard straight to High C5)
            for i in range(len(note_runs) - 1):
                if note_runs[i][0] == 'C4' and note_runs[i+1][0] == 'C5':
                    discoveries.append("[OCTAVE LEAP UP OF JOY/APPEAL] (Sudden vault from sub-tonic D4 springboard straight to high C5)")
            
        if discoveries:
            log("\nSTRUCTURAL DISCOVERIES:")
            for item in discoveries: log(f"  * {item}")
                
        log("\nSyllable-by-Syllable Music Map:")
        log(group_reset[['LYRIC_SYLL', 'SYLL_NOTE', 'DEGREE', 'SENSE', 'ORNAMENT_NAME']].to_string(index=False))

    output_filename = "complete_tanach_analysis.txt"
    print(f"Writing complete analytical masterfile to disk...")
    with open(output_filename, 'w', encoding='utf-8') as out_file:
        out_file.write("\n".join(output_lines))
    print(f"Success! Master report generated seamlessly: {output_filename}")

# Run the single-file pipeline execution
analyze_complete_tanakh("complete_tanach.json")
