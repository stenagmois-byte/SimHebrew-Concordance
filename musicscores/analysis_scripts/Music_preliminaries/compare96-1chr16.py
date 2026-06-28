import os
import pandas as pd
from collections import Counter

def run_ornament_comparison():
    print("=" * 95)
    print("CANONICAL STRUCTURAL ORNAMENT EXPLORER: SUBSTRING CADENCE ENGINE")
    print("=" * 95)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    matrix_file_path = os.path.join(parent_dir, "MUSICSTATS.xlsx")
    
    if not os.path.exists(matrix_file_path):
        print(f"[Critical Error] MUSICSTATS.xlsx not found at: {matrix_file_path}")
        return
        
    try:
        print("Loading master musicological database...")
        df = pd.read_excel(matrix_file_path, header=None)
    except Exception as e:
        print(f"[Error] Failed to read Excel dataset: {e}")
        return

    prose_ornaments = []
    poetry_ornaments = []
    
    prose_lines = 0
    poetry_lines = 0

    for idx, row in df.iterrows():
        book = str(row[3]).strip().upper()
        
        try:
            chapter = int(float(str(row[4]).strip()))
        except ValueError:
            continue

        raw_music_string = str(row[0]).strip()
        tokens = raw_music_string.split()
        
        # --- ULTIMATE FLEXIBLE FILTER ---
        # If a token contains a comma, an Atnah '^', or the word 'ole', we isolate the ornament segment!
        ornaments_in_verse = []
        for t in tokens:
            if ',' in t or '^' in t or 'ole' in t.lower():
                # If an ornament is blended (like 'z-q,g#'), split it at the comma to count the ornament cleanly
                if ',' in t:
                    base_ornament = t.split(',')[0] + ','
                    ornaments_in_verse.append(base_ornament)
                else:
                    ornaments_in_verse.append(t)

        # --- SELECTION A: 1 Chronicles 16:23-33 (Prose Reporting) ---
        if "CHRONICLES" in book and "1" in book and chapter == 16:
            try:
                verse = int(float(str(row[5]).strip()))
                if 23 <= verse <= 33:
                    prose_ornaments.extend(ornaments_in_verse)
                    prose_lines += 1
            except ValueError:
                pass

        # --- SELECTION B: Psalm 96 (Poetic Singing) ---
        if "PSALM" in book and chapter == 96:
            poetry_ornaments.extend(ornaments_in_verse)
            poetry_lines += 1

    print(f"\n[Success] Scanned {prose_lines} prose verses and {poetry_lines} poetic verses.")

    # 2. Render Statistical Distribution
    print("\n" + "-" * 60)
    print("PROSE SYSTEM: 1 CHRONICLES 16:23-33 ORNAMENT MAP")
    print("-" * 60)
    prose_counts = Counter(prose_ornaments)
    if prose_counts:
        for ornament, count in prose_counts.most_common():
            print(f"  Ornament: {ornament:<12} Found: {count} times")
    else:
        print("  No text ornaments isolated in selection.")

    print("\n" + "-" * 60)
    print("POETIC SYSTEM: PSALM 96 ORNAMENT MAP")
    print("-" * 60)
    poetry_counts = Counter(poetry_ornaments)
    if poetry_counts:
        for ornament, count in poetry_counts.most_common():
            print(f"  Ornament: {ornament:<12} Found: {count} times")
    else:
        print("  No text ornaments isolated in selection.")

    # 3. Direct Substitution Analysis Summary
    print("\n" + "-" * 60)
    print("CADENCE AND SUSTAINED BREATH COMPARATIVE MATRIX")
    print("-" * 60)
    
    # Simple loop to sum up anything containing the target tags
    prose_zq = sum(c for o, c in prose_counts.items() if 'z-q' in o.lower())
    poetry_atnah = sum(c for o, c in poetry_counts.items() if '^' in o)
    poetry_ole = sum(c for o, c in poetry_counts.items() if 'ole' in o.lower())
    
    print(f" Prose 'Zaquef-Qaton' (z-q,) count  : {prose_zq}")
    print(f" Poetry 'Atnah' (has ^) count      : {poetry_atnah}")
    print(f" Poetry 'Ole' (ole,) count         : {poetry_ole}")
    print("\n" + "=" * 95)

if __name__ == "__main__":
    run_ornament_comparison()
