import os
import pandas as pd
from collections import Counter

# =====================================================================
# CONFIGURATION
# This script automatically finds MUSICSTATS.xlsx in the parent folder.
# Change PHRASE_LENGTH to look for longer or shorter musical segments.
# =====================================================================
PHRASE_LENGTH = 7  
TARGET_BOOK = "PSALMS"
TARGET_CHAPTER = 78
# =====================================================================

def run_local_repo_analysis():
    print("=" * 80)
    print(f"LOCAL REPOSITORY ENGINE: RUNNING ANALYSIS ON {TARGET_BOOK} {TARGET_CHAPTER}")
    print("=" * 80)
    
    # Dynamically find MUSICSTATS.xlsx relative to where this script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    matrix_file_path = os.path.join(parent_dir, "MUSICSTATS.xlsx")
    
    print(f"Looking for data source at: {matrix_file_path}")
    
    if not os.path.exists(matrix_file_path):
        print(f"[Critical Error] MUSICSTATS.xlsx not found at target location!")
        print("Make sure this script is running inside a subfolder of 'musicscores'.")
        return
        
    try:
        print("Reading data sheet into memory workspace...")
        df = pd.read_excel(matrix_file_path, header=None)
    except Exception as e:
        print(f"[Error] Failed to read Excel file: {e}")
        return

    clean_notes_phrases = []
    full_music_phrases = []
    verse_counter = 0

    for idx, row in df.iterrows():
        # Match Book (Col 3 / D) and Chapter (Col 4 / E)
        row_book = str(row[3]).strip().upper()
        row_chapter = str(row[4]).strip()
        
        if row_book == TARGET_BOOK and (row_chapter == str(TARGET_CHAPTER) or row_chapter.lstrip('0') == str(TARGET_CHAPTER)):
            verse_counter += 1
            
            # --- Parse Clean Equivalent Notes (Col 7 / H) ---
            clean_notes_str = str(row[7]).strip()
            clean_notes = [note for note in clean_notes_str.split() if note]
            for i in range(len(clean_notes) - PHRASE_LENGTH + 1):
                window = tuple(clean_notes[i : i + PHRASE_LENGTH])
                clean_notes_phrases.append(window)

            # --- Parse Full Accent Strings (Col 0 / A) ---
            raw_music_str = str(row[0]).strip()
            pure_music_notes = [token for token in raw_music_str.split() if not token.endswith(',')]
            for i in range(len(pure_music_notes) - PHRASE_LENGTH + 1):
                window = tuple(pure_music_notes[i : i + PHRASE_LENGTH])
                full_music_phrases.append(window)

    print(f"Successfully processed {verse_counter} verses.")

    # Display Top Patterns Found
    print("\n" + "-" * 60)
    print(f"TOP 10 REPEATING PHRASES IN CLEAN EQUIVALENT NOTES (Col H)")
    print("-" * 60)
    for phrase, count in Counter(clean_notes_phrases).most_common(10):
        print(f" [{' -> '.join(phrase):<22}] Count: {count} matches")

    print("\n" + "-" * 60)
    print(f"TOP 10 REPEATING PHRASES WITH TRUE ACCIDENTALS (Col A)")
    print("-" * 60)
    for phrase, count in Counter(full_music_phrases).most_common(10):
        print(f" [{' -> '.join(phrase):<22}] Count: {count} matches")
        
    print("\n" + "=" * 80)

if __name__ == "__main__":
    run_local_repo_analysis()

