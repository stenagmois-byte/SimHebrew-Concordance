import json
import pandas as pd
import html

# --------------------------------------------------------------------------------
# 0. CORE MUSICOLOGICAL DICTIONARIES
# --------------------------------------------------------------------------------
PROSE_DICT = {'E4': 1, 'F4': 2, 'G4': 3, 'G#4': 3, 'A4': 4, 'B4': 5, 'C5': 6, 'D4': 7, 'C4': 6}
POETIC_DICT = {'E4': 1, 'F4': 2, 'F#4': 2, 'G4': 3, 'A4': 4, 'B4': 5, 'C5': 6, 'D4': 7}

def load_and_clean_data(file_path):
    """Safely ingests, sorts, and structures the master JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    items = raw_data.get('results', [])
    if isinstance(items, list) and len(items) > 0:
        items = items[0].get('items', [])
    elif isinstance(items, dict):
        items = items.get('items', [])
    else:
        items = []
        
    df = pd.DataFrame(items)
    df.columns = [col.upper() for col in df.columns]
    
    # Clean explicit pitch names and fill implied tones with E4
    df['SYLL_NOTE'] = df['SYLL_NOTE'].str.replace('F4#4', 'F#4').replace('G4#4', 'G#4')
    df['SYLL_NOTE'] = df['SYLL_NOTE'].apply(lambda x: str(x).strip() if (pd.notna(x) and str(x).strip() != "") else "E4")
    
    # Enforce strict numeric data types for canonical timeline alignment
    df['BOOK_SEQ_NO'] = pd.to_numeric(df['BOOK_SEQ_NO'], errors='coerce')
    df['XML_SEQ'] = pd.to_numeric(df['XML_SEQ'], errors='coerce')
    df['CHAPTER_CD'] = pd.to_numeric(df['CHAPTER_CD'], errors='coerce')
    df['VERSE_CD'] = pd.to_numeric(df['VERSE_CD'], errors='coerce')
    
    return df.sort_values(by=['BOOK_SEQ_NO', 'CHAPTER_CD', 'VERSE_CD', 'XML_SEQ']).reset_index(drop=True)

# --------------------------------------------------------------------------------
# ROUTINE 1: THE MASTER GEOGRAPHIC FILTER
# --------------------------------------------------------------------------------
def filter_passage(df, book, ch_from, vs_from, ch_to, vs_to):
    """Filters data precisely across multiple chapters and verses."""
    book_df = df[df['BOOK_CD'].str.upper() == book.upper()]
    
    # Construct a linear numeric location identifier: (Chapter * 1000) + Verse
    # This prevents cross-chapter slice bleeding (e.g., catching unwanted verses in middle chapters)
    loc_start = (ch_from * 1000) + vs_from
    loc_end = (ch_to * 1000) + vs_to
    
    book_df = book_df.copy()
    book_df['LOCATION_ID'] = (book_df['CHAPTER_CD'] * 1000) + book_df['VERSE_CD']
    
    return book_df[(book_df['LOCATION_ID'] >= loc_start) & (book_df['LOCATION_ID'] <= loc_end)].reset_index(drop=True)

# --------------------------------------------------------------------------------
# ROUTINE 2: STROPHE BOUNDARY & HIGH C INITIAL EXPLOSION FINDER
# --------------------------------------------------------------------------------
def detect_strophe_boundaries(passage_df, genre="POETRY"):
    """Finds verses that launch immediately into C5, acting like an upbeat."""
    print("\n=== ROUTINE 2: STROPHE BOUNDARY EXPLOSION DETECTION ===")
    
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        group = group.reset_index(drop=True)
        if len(group) < 2: continue
        
        note_1 = group['SYLL_NOTE'].iloc[0]
        note_2 = group['SYLL_NOTE'].iloc[1]
        note_3 = group['SYLL_NOTE'].iloc[2] if len(group) > 2 else None
        
        # Scenario A: First syllable strikes High C5 instantly
        # Scenario B: First syllable is a brief E4 tonic placeholder, instantly rocketed to C5 on syllable 2
        is_immediate_c5 = (note_1 == 'C5')
        is_upbeat_rocket = (note_1 == 'E4' and note_2 == 'C5')
        
        if is_immediate_c5 or is_upbeat_rocket:
            heb = html.unescape(group['HEB_TEXT'].dropna().iloc[0].replace('\n', ' ')) if 'HEB_TEXT' in group.columns and not group['HEB_TEXT'].dropna().empty else ""
            print(f"📍 Possible Strophe Break at Verse {ch}:{vs}")
            print(f"   Contours: {note_1} -> {note_2} -> {note_3}")
            print(f"   Hebrew: {heb}")
            print(f"   Impact: The text shatters previous pacing, launching directly into a high-register thematic block.\n")

# --------------------------------------------------------------------------------
# ROUTINE 3: THE "REVERSE COLON" NON-TONIC COMMENCEMENT TRACER
# --------------------------------------------------------------------------------
def trace_non_tonic_beginnings(passage_df):
    """Flags verses that do not start on E4, linking them as a structural bridge to the past."""
    print("\n=== ROUTINE 3: NON-TONIC STRUCTURAL COMMENCEMENT ('REVERSE COLON') ===")
    
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        group = group.reset_index(drop=True)
        first_note = group['SYLL_NOTE'].iloc[0]
        
        if first_note != 'E4':
            heb = html.unescape(group['HEB_TEXT'].dropna().iloc[0].replace('\n', ' ')) if 'HEB_TEXT' in group.columns and not group['HEB_TEXT'].dropna().empty else ""
            print(f"🔗 Verse {ch}:{vs} starts non-tonically on: {first_note} (Syllable: '{group['LYRIC_SYLL'].iloc[0]}')")
            print(f"   Hebrew: {heb}")
            print(f"   Exegetical Function: Acts like a reverse colon. It refuses a fresh musical restart, forcing the singer")
            print(f"   to acoustically bind this verse directly onto the resolution or tension of the preceding text.\n")

# --------------------------------------------------------------------------------
# ROUTINE 4: REVIA-MUGRASH POETIC RECITATION COMPILER
# --------------------------------------------------------------------------------
def analyze_revia_mugrash(passage_df):
    """Maps the presence and the precise reciting pitches paired with the revia-mugrash."""
    print("\n=== ROUTINE 4: REVIA-MUGRASH RECITAION ANALYSIS ===")
    
    if 'ORNAMENT_NAME' not in passage_df.columns:
        print("Error: ORNAMENT_NAME column missing from source data.")
        return
        
    for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
        group = group.reset_index(drop=True)
        
        # Scan for lowercase 'revia-mugrash' or variations in your string tags
        rm_mask = group['ORNAMENT_NAME'].astype(str).str.lower().str.contains('revia-mugrash|mugrash')
        
        if rm_mask.any():
            rm_indices = group[rm_mask].index
            for idx in rm_indices:
                reciting_note = group['SYLL_NOTE'].iloc[idx]
                syllable = group['LYRIC_SYLL'].iloc[idx]
                print(f"🎭 Verse {ch}:{vs} contains a Revia-Mugrash on syllable '{syllable}'")
                print(f"   Locked Reciting Pitch: {reciting_note} (Scale Degree: {POETIC_DICT.get(reciting_note, {}).get('degree', 'Unknown')})")
                print(f"   Trajectory: Look at how this pitch functions as a specialized technical runway launching back to the tonic baseline.\n")

# --------------------------------------------------------------------------------
# ROUTINE 5: ORNAMENT UNDERSCORE FREQUENCY & IDEATIONAL REPETITION INDEX
# --------------------------------------------------------------------------------
def map_ornament_ideational_underscores(passage_df):
    """Finds repeated musical accents across a section, highlighting structural keywords."""
    print("\n=== ROUTINE 5: ORNAMENT UNDERSCORE & IDEATIONAL REPETITION ===")
    
    if 'ORNAMENT_NAME' not in passage_df.columns:
        return
        
    ornament_word_map = {}
    
    # Loop over every row to tie non-zero ornaments directly to their word syllables
    for idx, row in passage_df.iterrows():
        orn = str(row['ORNAMENT_NAME']).strip().lower()
        if orn != '0' and orn != 'none' and orn != 'nan' and pd.notna(row['ORNAMENT_NAME']):
            ch = row['CHAPTER_CD']
            vs = row['VERSE_CD']
            syll = row['LYRIC_SYLL']
            pitch = row['SYLL_NOTE']
            
            if orn not in ornament_word_map:
                ornament_word_map[orn] = []
            ornament_word_map[orn].append(f"{ch}:{vs}({syll}/{pitch})")
            
    # Print out ornaments that hit multiple times in the slice, acting as a thematic motif
    for orn, instances in ornament_word_map.items():
        if len(instances) >= 2:
            print(f"🔁 Ideational Underscore Motif: '{orn}' hits {len(instances)} times in this passage:")
            print(f"   Locations: {', '.join(instances[:6])}...")
            print(f"   Exegetical Value: This repeated musical signature binds these phrases together under a unified acoustic color.\n")


# ================================================================================
# EXECUTION CONTROLLER: Run this block against your live export file
# ================================================================================
if __name__ == "__main__":
    # 1. Load the massive master dataset
    master_file = "complete_tanakh.json" 
    
    try:
        master_df = load_and_clean_data(master_file)
        
        # 2. Configure your precise evaluation coordinates using Routine 1
        # Example: Let's extract exactly Psalm 29 from verse 1 to verse 11
        selected_passage = filter_passage(
            df=master_df, 
            book="PSALMS", 
            ch_from=29, vs_from=1, 
            ch_to=29, vs_to=11
        )
        
        print(f"\nSuccessfully loaded and isolated {len(selected_passage)} rows for analysis.")
        
        # 3. Fire up the independent evaluation engines on our slice
        detect_strophe_boundaries(selected_passage, genre="POETRY")
        trace_non_tonic_beginnings(selected_passage)
        analyze_revia_mugrash(selected_passage)
        map_ornament_ideational_underscores(selected_passage)
        
    except FileNotFoundError:
        print(f"Could not open '{master_file}'. Make sure your Oracle export is placed in this script's directory.")
