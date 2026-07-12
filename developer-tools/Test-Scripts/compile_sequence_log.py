import os
import json
import html
from collections import Counter
import pandas as pd

from collections import Counter

from collections import Counter

def extract_haik_vantoura_vector(verse_group, book_id):
    """
    Separates a verse into Pre-Atnah and Post-Atnah structural sections.
    - Captures intentional asymmetry when Atnah is omitted.
    - Tracks the Poetic Tuba (Revia-Mugrash/Revia/Geresh) as the explicit 
      signal heralding the return route to the tonic (E4).
    """
    valid_rows = verse_group[~verse_group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
    if valid_rows.empty: 
        return None, None, None

    notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
    syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
    
    is_poetic = book_id in ["PSALMS", "PROVERBS", "JOB"]
    system_type = "POETIC_SYSTEM" if is_poetic else "PROSE_SYSTEM"
    
    # Locate the Atnah Cadence Point (A4)
    atnah_indices = [i for i, note in enumerate(notes) if note == "A4"]
    
    # ---------------------------------------------------------
    # CASE 1: INTENTIONAL OMISSION (Missing Mid-Point Rest)
    # ---------------------------------------------------------
    if not atnah_indices:
        right_wing_notes = []
        for note in notes:
            if not right_wing_notes or note != right_wing_notes[-1]:
                right_wing_notes.append(note)
        post_str = " -> ".join(right_wing_notes) if right_wing_notes else "End"
        
        final_vector = f"Pre: [None] | Post: [{post_str}]"
        return "ASYMMETRIC", final_vector, system_type
        
    # ---------------------------------------------------------
    # CASE 2: STANDARD MID-VERSE CADENCE
    # ---------------------------------------------------------
    atnah_idx = atnah_indices[0]
    atnah_note = notes[atnah_idx]
    
    # Pre-Atnah Melodic Vector
    pre_atnah_notes = []
    for i in range(atnah_idx + 1):
        note = notes[i]
        if not pre_atnah_notes or note != pre_atnah_notes[-1]:
            pre_atnah_notes.append(note)
    pre_str = " -> ".join(pre_atnah_notes)

    # Post-Atnah Phrase (The Right Wing)
    post_notes = notes[atnah_idx + 1:]
    post_syllables = syllables[atnah_idx + 1:]
    
    post_vector_notes = []
    if post_notes:
        first_post_syllable = post_syllables[0] if post_syllables else ""
        is_word_start = not first_post_syllable.startswith("-")
        
        # Continuation rule across the caesura word boundary
        if post_notes[0] == atnah_note and is_word_start:
            post_vector_notes.append(atnah_note)
            
        for note in post_notes:
            if not post_vector_notes or note != post_vector_notes[-1]:
                post_vector_notes.append(note)

    post_str = " -> ".join(post_vector_notes) if post_vector_notes else "End"
    
    # --- POETIC TUBA IDENTIFICATION ---
    if is_poetic and post_notes:
        revia_idx, geresh_idx, mugrash_idx = -1, -1, -1
        for idx, sy in enumerate(post_syllables):
            sy_clean = sy.lower()
            if "revia" in sy_clean: revia_idx = idx
            if "geresh" in sy_clean: geresh_idx = idx
            if "mugrash" in sy_clean: mugrash_idx = idx
        
        # Map the Tuba directly to its physical pitch marker
        if revia_idx != -1 and mugrash_idx != -1:
            tuba_str = f"{post_notes[revia_idx]} (Revia-Mugrash)"
        elif revia_idx != -1 and geresh_idx != -1:
            tuba_str = f"{post_notes[revia_idx]} (Revia+Geresh)"
        elif revia_idx != -1:
            tuba_str = f"{post_notes[revia_idx]} (Revia)"
        else:
            tuba_str = "None"
            
        final_vector = f"Pre: [{pre_str}] | Post: [{post_str}] | Tuba: [{tuba_str}]"
    else:
        # Prose System correctly bypasses the Tuba definition entirely
        final_vector = f"Pre: [{pre_str}] | Post: [{post_str}]"
    
    return "VALID_LINE", final_vector, system_type

def is_true_cadence_anchor(syllable_token, is_poetic):
    """
    Identifies the exact JSON strings indicating an Atnah or Ole-Veyored.
    """
    token_clean = syllable_token.lower()
    if "atnah" in token_clean:
        return True
    if is_poetic and "ole" in token_clean: # Ole + Merkha cadence
        return True
    return False

if __name__ == "__main__":
    # --- AUTOMATED ABSOLUTE PATH RESOLUTION ---
    # Locates the exact directory where this script file lives right now
    script_directory = os.path.dirname(os.path.abspath(__file__))
    
    # Safely walks up exactly one directory level to lock onto your true musicscores root
    ROOT_DIR = os.path.abspath(os.path.join(script_directory, ".."))
    OUTPUT_LOG_FILE = os.path.join(script_directory, "tanach_atnah_approaches_log.txt")
    
    print(f"🚀 INITIALIZING BACKEND SEQUENCE LOG COMPILER")
    print(f"Targeting Absolute Base: {ROOT_DIR}")
    print(f"Executing Second-Pass Deep Scan across repository tree...\n")
    
    master_log_records = []
    success_count = 0
    
    # Using your proven recursive directory crawler
    for current_dir, subfolders, files in os.walk(ROOT_DIR):
        if "analysis_scripts" in current_dir or "Test-Scripts" in current_dir:
            continue
            
        for file in files:
            if file.lower().endswith(".json"):
                json_path = os.path.join(current_dir, file)
                
                base_name, _ = os.path.splitext(file)
                name_parts = base_name.split("_")
                
                if len(name_parts) >= 2:
                    chapter_id = name_parts[-1]
                    book_id = "_".join(name_parts[:-1]).upper()
                else:
                    book_id = base_name.upper()
                    chapter_id = "001"
                
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                    
                    # --- RESTORING YOUR WORKING PRODUCTION PAYLOAD LOADER ---
                    items_list = None
                    working_data = raw_data
                    
                    if isinstance(working_data, dict):
                        if "results" in working_data and isinstance(working_data["results"], dict):
                            items_list = working_data["results"].get("items")
                        elif "results" in working_data and isinstance(working_data["results"], list):
                            if len(working_data["results"]) > 0 and "items" in working_data["results"][0]:
                                items_list = working_data["results"][0]["items"]
                        else:
                            items_list = working_data.get("items")
                    elif isinstance(working_data, list) and len(working_data) > 0:
                        first_item = working_data[0]
                        if isinstance(first_item, dict):
                            if "results" in first_item and isinstance(first_item["results"], dict):
                                items_list = first_item["results"].get("items")
                            elif "results" in first_item and isinstance(first_item["results"], list):
                                if len(first_item["results"]) > 0 and "items" in first_item["results"][0]:
                                    items_list = first_item["results"][0]["items"]
                            else:
                                items_list = first_item.get("items")
                                
                    if items_list is None and isinstance(raw_data, dict) and "items" in raw_data:
                        items_list = raw_data["items"]
                        
                    if items_list is None:
                        print(f"🔍 Trace: Skipped file '{file}'. Could not locate 'items' payload container.")
                        continue
                        
                    df = pd.DataFrame(items_list)
                    df.columns = df.columns.str.upper()
                    
                    # Column Validation
                    required_cols = ['CHAPTER_CD', 'VERSE_CD', 'SYLL_NOTE', 'LYRIC_SYLL']
                    missing_cols = [c for c in required_cols if c not in df.columns]
                    if missing_cols:
                        print(f"🔍 Trace: File '{file}' matches layout but lacks structural columns: {missing_cols}")
                        continue
                    
                    # Data Type Hardening
                    df['CHAPTER_CD'] = df['CHAPTER_CD'].astype(str).str.strip()
                    df['VERSE_CD'] = df['VERSE_CD'].astype(str).str.strip()
                    
                    file_verses_logged = 0
                    for (ch, vs), group in df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
                        # NEW INTEGRATION CODE
                        line_type, approach_vector, system_label = extract_haik_vantoura_vector(group, book_id)

                        if approach_vector:
                            try:
                                display_chapter = int(float(ch))
                                display_verse = int(float(vs))
                            except ValueError:
                                display_chapter = ch
                                display_verse = vs

                            master_log_records.append({
                                "book": book_id,
                                "chapter": display_chapter,
                                "verse": display_verse,
                                "type": line_type,        # STANDARD_SPLIT vs PARAGRAPH_SUMMARY_CODA
                                "vector": approach_vector,  # The actual note string: E4 -> F4 -> A4...
                                "system": system_label     # PROSE_SYSTEM vs POETIC_SYSTEM
                            })
                            file_verses_logged += 1
                    
                    success_count += 1
                    if success_count % 50 == 0:
                        print(f"📊 Trace: Successfully mapped file #{success_count} ({file}) -> Logged {file_verses_logged} verses.")
                    
                except Exception as e:
                    print(f"❌ Trace Exception on file '{file}': {str(e)}")

    # --- WRITE OUT THE GLOBAL STRUCTURAL LOG REPORT ---
    if master_log_records:
        analysis_df = pd.DataFrame(master_log_records)
        valid_vectors_df = analysis_df[analysis_df["vector"].notna()]
        total_atnah_verses = len(valid_vectors_df)
        
        with open(OUTPUT_LOG_FILE, "w", encoding="utf-8") as out:
            out.write("========================================================================\n")
            out.write("         GLOBAL TANACH SEQUENCE MATRIX: APPROACHES TO ATNAH            \n")
            out.write("========================================================================\n\n")
            out.write(f"Processed Files:           {success_count} JSON Chapters\n")
            out.write(f"Total Atnah Cadences Found: {total_atnah_verses} Verses\n\n")
            
            vector_counts = Counter(zip(valid_vectors_df["vector"], valid_vectors_df["system"]))
            
            out.write("--- RANKED CADENCE PATTERNS & STRUCTURAL BEHAVIOR ---\n\n")
            
            for (formula, system), count in vector_counts.most_common():
                percentage = (count / total_atnah_verses) * 100 if total_atnah_verses > 0 else 0
                
                formula_verses = valid_vectors_df[(valid_vectors_df["vector"] == formula) & (valid_vectors_df["system"] == system)]
                
                out.write(f"🎵 [{system}] | Vector: [ {formula} ]\n")
                out.write(f"   Occurrences: {count} times ({percentage:.1f}%)\n")
                
                # --- CLEAN, CONDITIONAL STRUCTURE PHRASING ---
                
                # Truncate book names to 4 characters for clean presentation
                sample_rows = formula_verses.head(5)
                samples_list = []
                for _, row in sample_rows.iterrows():
                    short_book = str(row['book'])[:4].upper()
                    samples_list.append(f"{short_book} {row['chapter']}:{row['verse']}")
                    
                out.write(f"   Samples:     {', '.join(samples_list)}\n")
                out.write("-" * 75 + "\n")
                
                # Truncate book names to 4 characters for clean, punchy references
                sample_rows = formula_verses.head(5)
                samples_list = []
                for _, row in sample_rows.iterrows():
                    short_book = str(row['book'])[:4].upper()
                    samples_list.append(f"{short_book} {row['chapter']}:{row['verse']}")
                    
                out.write(f"   Samples:     {', '.join(samples_list)}\n")
                out.write("-" * 75 + "\n")
                
        print(f"🏭 BACKGROUND ANALYSIS SCAN COMPLETE")
        print(f"✅ Generated master structural log file: {OUTPUT_LOG_FILE}")
    else:
        print("❌ Error: No valid musical sequence logs could be assembled.")
