import os
import pandas as pd
from collections import defaultdict
import argparse

def find_data_file(filename="MUSICSTATS.xlsx"):
    """
    Dynamically hunts down the spreadsheet relative to where the user is executing the code,
    ensuring full compatibility across different local environments and GitHub clones.
    """
    if os.path.exists(filename):
        return filename
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_neighbor = os.path.join(script_dir, filename)
    if os.path.exists(script_neighbor):
        return script_neighbor
    parent_dir = os.path.dirname(script_dir)
    parent_neighbor = os.path.join(parent_dir, filename)
    if os.path.exists(parent_neighbor):
        return parent_neighbor
    for root, dirs, files in os.walk(parent_dir if parent_dir else "."):
        if filename in files:
            return os.path.join(root, filename)
    return None

def run_local_repo_analysis(phrase_length, target_book, target_chapter, max_results):
    matrix_file_path = find_data_file("MUSICSTATS.xlsx")
    
    # Establish text flags for the console printout
    book_flag = "ALL BOOKS" if target_book == "ALL" else target_book
    chap_flag = "ALL CHAPTERS" if target_chapter == 0 else f"CHAPTER {target_chapter}"
    
    print("=" * 110)
    print(f"MASTER TANAKH MUSIC ENGINE: RUNNING ANALYSIS ON [{book_flag}] [{chap_flag}] ({phrase_length}-PULSE WINDOW)")
    
    if not matrix_file_path:
        print(f"[Critical Error] MUSICSTATS.xlsx could not be located anywhere in this repository branch!")
        print("=" * 110)
        return
        
    print(f"Data source resolved at: {os.path.abspath(matrix_file_path)}")
    print("=" * 110)
        
    try:
        print("Loading corpus database matrix sheet...")
        df = pd.read_excel(matrix_file_path, header=None)
    except Exception as e:
        print(f"[Error] Failed to read Excel file: {e}")
        return

    clean_notes_tracker = defaultdict(list)
    full_music_tracker = defaultdict(list)
    verse_counter = 0

    for idx, row in df.iterrows():
        # Extracted parameters normalized from Row Data
        row_book = str(row[3]).strip().upper()
        row_chapter_str = str(row[4]).strip()
        
        # Guard clause: clean up chapter string formatting safely
        try:
            row_chapter = int(float(row_chapter_str)) if row_chapter_str.replace('.','',1).isdigit() else 0
        except ValueError:
            row_chapter = 0

        # Dynamic Scope Logic:
        # Match if target_book is 'ALL' OR matches row exactly
        book_matches = (target_book == "ALL") or (row_book == target_book)
        # Match if target_chapter is 0 (all chapters) OR matches row exactly
        chapter_matches = (target_chapter == 0) or (row_chapter == target_chapter)

        if book_matches and chapter_matches:
            verse_counter += 1
            
            # Format standard notation location stamp
            verse_num = str(row[5]).strip() if pd.notna(row[5]) else f"v{verse_counter}"
            location_label = f"{row_book} {row_chapter}:{verse_num}"
            
            # --- Parse Clean Equivalent Notes (Col 7 / H) ---
            clean_notes_str = str(row[7]).strip()
            clean_notes = [note for note in clean_notes_str.split() if note]
            for i in range(len(clean_notes) - phrase_length + 1):
                window = tuple(clean_notes[i : i + phrase_length])
                clean_notes_tracker[window].append(location_label)

            # --- Parse Full Accent Strings (Col 0 / A) ---
            raw_music_str = str(row[0]).strip()
            pure_music_notes = [token for token in raw_music_str.split() if not token.endswith(',')]
            for i in range(len(pure_music_notes) - phrase_length + 1):
                window = tuple(pure_music_notes[i : i + phrase_length])
                full_music_tracker[window].append(location_label)

    print(f"Successfully evaluated {verse_counter} total verses across chosen constraints.")

    # Sort trackers based on maximum frequency match lists
    sorted_clean = sorted(clean_notes_tracker.items(), key=lambda x: len(x[1]), reverse=True)
    sorted_full = sorted(full_music_tracker.items(), key=lambda x: len(x[1]), reverse=True)

    print("\n" + "-" * 110)
    print(f"TOP REPEATING PHRASES IN CLEAN EQUIVALENT NOTES (Col H) WITH LOCATIONS")
    print("-" * 110)
    for phrase, locations in sorted_clean[:max_results]:
        if len(locations) > 1:
            print(f" [{' -> '.join(phrase):<24}] Matches: {len(locations):<3} | Locations: {', '.join(locations)}")

    print("\n" + "-" * 110)
    print(f"TOP REPEATING PHRASES WITH TRUE ACCIDENTALS (Col A) WITH LOCATIONS")
    print("-" * 110)
    for phrase, locations in sorted_full[:max_results]:
        if len(locations) > 1:
            print(f" [{' -> '.join(phrase):<24}] Matches: {len(locations):<3} | Locations: {', '.join(locations)}")
        
    print("\n" + "=" * 110)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze Hebrew Music Score Note Sequences dynamically across the entire Tanakh.")
    parser.add_argument("--pulses", type=int, default=5, help="Length of sliding window")
    parser.add_argument("--book", type=str, default="MICAH", help="Target book name in uppercase (Use 'ALL' to search everything)")
    parser.add_argument("--chapter", type=int, default=5, help="Target chapter number (Use '0' to search all chapters in the book)")
    parser.add_argument("--limit", type=int, default=10, help="Number of top repeating sequences to display in output logs")
    
    args = parser.parse_args()
    run_local_repo_analysis(args.pulses, args.book.upper(), args.chapter, args.limit)
