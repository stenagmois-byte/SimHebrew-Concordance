import os
import json
import re
import pandas as pd
from collections import Counter

# ========================================================================
# USER NAVIGATION PARAMETERS (Target specific books or ranges)
# ========================================================================
TARGET_BOOK = "GENESIS"            # Matches any book ID containing this text
TARGET_CHAPTERS = [1]              # ALWAYS use numbers here (e.g. [1] or)
OUTPUT_PASSAGE_FILE = "PASSAGE_ARCHITECTURE_REPORT.txt"

# Dynamic Root Resolution: Stepped back to look up into the parent repository directory
ROOT_DIR = "../"  
# ========================================================================
# MUSICOLOGICAL CHAPTER ARCHITECTURE ROUTINE
# ========================================================================
def extract_chapter_refrains(chapter_df, book_id, chapter_id):
    """
    Analyzes a single chapter sequentially to find repeating musical refrains
    and structural choruses that tie the narrative together.
    """
    # Sort explicitly by verse to preserve the sequential story narrative
    chapter_df['VERSE_NUM'] = pd.to_numeric(chapter_df['VERSE_CD'], errors='coerce')
    chapter_df = chapter_df.sort_values('VERSE_NUM').reset_index(drop=True)
    
    is_poetic = book_id in ["PSALMS", "PROVERBS", "JOB"]
    system_type = "POETIC" if is_poetic else "PROSE"
    
    chapter_sequence = []
    post_atnah_pool = []
    full_vector_pool = []
    
    # First pass: Extract the structural components verse by verse
    for vs_num, verse_group in chapter_df.groupby('VERSE_NUM', sort=False):
        valid_rows = verse_group[~verse_group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        if valid_rows.empty:
            continue
            
        notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        
        atnah_indices = [i for i, note in enumerate(notes) if note == "A4"]
        
        # Build standard components
        if not atnah_indices:
            # Asymmetric right-wing layout
            right_wing = []
            for n in notes:
                if not right_wing or n != right_wing[-1]: 
                    right_wing.append(n)
            pre_str, post_str = "None", " -> ".join(right_wing)
        else:
            atnah_idx = atnah_indices[0]
            
            # Pre-Atnah path
            pre_notes = []
            for i in range(atnah_idx + 1):
                if not pre_notes or notes[i] != pre_notes[-1]: 
                    pre_notes.append(notes[i])
            pre_str = " -> ".join(pre_notes)
            
            # Post-Atnah path (Right-Wing)
            post_notes = notes[atnah_idx + 1:]
            post_syllables = syllables[atnah_idx + 1:]
            post_vector = []
            if post_notes:
                # Word-start continuity check
                first_post_syllable = post_syllables[0] if post_syllables else ""
                if post_notes[0] == "A4" and not first_post_syllable.startswith("-"):
                    post_vector.append("A4")
                for n in post_notes:
                    if not post_vector or n != post_vector[-1]: 
                        post_vector.append(n)
            post_str = " -> ".join(post_vector) if post_vector else "End"

        # Log to the chapter sequence
        chapter_sequence.append({
            "verse": vs_num,
            "pre": pre_str,
            "post": post_str
        })
        
        # Collect for refrain matching
        if post_str != "End": 
            post_atnah_pool.append(post_str)
        full_vector_pool.append(f"Pre: [{pre_str}] | Post: [{post_str}]")

    # Identify which phrases actually repeat within this single chapter context
    post_refrains = {k for k, v in Counter(post_atnah_pool).items() if v >= 2}
    full_refrains = {k for k, v in Counter(full_vector_pool).items() if v >= 2}
    
    # Assemble the sequential report string
    report_lines = [
        "========================================================================\n",
        f"📖 NARRATIVE ARCHITECTURE: {book_id[:4]} CHAPTER {chapter_id} ({system_type})\n",
        "========================================================================\n\n"
    ]
    
    report_lines.append("--- SEQUENTIAL VERSES & STRUCTURAL CHORUSES ---\n")
    for v_data in chapter_sequence:
        v_str = f"Pre: [{v_data['pre']}] | Post: [{v_data['post']}]"
        is_full_chorus = v_str in full_refrains
        is_post_chorus = v_data['post'] in post_refrains and not is_full_chorus
        
        # Tag the refrains dynamically as we read down the narrative
        marker = ""
        if is_full_chorus: 
            marker = " 🔥 [CHAPTER REFRAIN / FULL CHORUS]"
        elif v_data['post'] == "E4 -> F4 -> E4 -> G#4 -> F4 -> E4": 
            marker = " 🌅 [TEMPORAL REFRAIN DETECTED]"
        elif is_post_chorus: 
            marker = " 🔁 [RECURRING POST-ATNAH REFRAIN]"
        
        report_lines.append(f"  Verse {v_data['verse']:03d}: {v_str}{marker}\n")
        
    report_lines.append("\n" + "-"*75 + "\n\n")
    return "".join(report_lines)

# ========================================================================
# MAIN GEOMETRY DIRECTORY CRAWLER LOOP
# ========================================================================
success_count = 0
passage_report_blocks = []

print(f"🚀 Targeting Narrative Passage: {TARGET_BOOK} (Chapters: {TARGET_CHAPTERS if TARGET_CHAPTERS else 'ALL'})")

for current_dir, subfolders, files in os.walk(ROOT_DIR):
    if "analysis_scripts" in current_dir or "Test-Scripts" in current_dir:
        continue
        
        for file in files:
            if file.lower().endswith(".json"):
                base_name, _ = os.path.splitext(file)
                
                # --- STRIP EXTRA SYMBOLS TO STANDARDIZE THE BASE ---
                import re
                
                # Match a pattern that ends in digits (the chapter) preceded by a dot or underscore
                # e.g., '1_CHRONICLES_001' or 'PSALMS.078' or 'RUTH.004'
                match = re.search(r"^(.*?)[_.](\d+)$", base_name)
                
                if match:
                    book_id = match.group(1).upper()       # e.g., "1_CHRONICLES", "PSALMS", "RUTH"
                    chapter_id_str = match.group(2)        # e.g., "001", "078", "004"
                else:
                    # Fallback default if the filename lacks a clean trailing digit pattern
                    book_id = base_name.upper()
                    chapter_id_str = "001"
                
                # -----------------------------------------------------------------
                # NAVIGATION GEOMETRY FILTER (Matches 'GENE' against 'GENESIS', etc.)
                # -----------------------------------------------------------------
                if TARGET_BOOK.upper() not in book_id:
                    continue
                    
                try:
                    current_chapter_num = int(float(chapter_id_str))
                except ValueError:
                    current_chapter_num = 1
                    
                if TARGET_CHAPTERS is not None and current_chapter_num not in TARGET_CHAPTERS:
                    continue
                
                # Proceed directly to loading the file payload...
                json_path = os.path.join(current_dir, file)

            # 1. Filter out books that don't match the target
            if TARGET_BOOK.upper() not in book_id:
                continue
                
            # 2. Filter out chapters if target constraints are passed
            try:
                current_chapter_num = int(float(chapter_id_str))
            except ValueError:
                current_chapter_num = 1
                
            if TARGET_CHAPTERS is not None and current_chapter_num not in TARGET_CHAPTERS:
                continue
            
            json_path = os.path.join(current_dir, file)
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
                    continue
                    
                df = pd.DataFrame(items_list)
                df.columns = df.columns.str.upper()
                
                # Execute analysis and cache text block with its sorting tuple
                chapter_analysis_text = extract_chapter_refrains(df, book_id, chapter_id_str)
                passage_report_blocks.append({
                    "sort_key": (book_id, current_chapter_num),
                    "text": chapter_analysis_text
                })
                
                success_count += 1
                print(f"📊 Mapped sequential story component: {book_id} Chapter {current_chapter_num}")
                
            except Exception as e:
                print(f"❌ Exception processing target file '{file}': {str(e)}")

# ========================================================================
# WRITE EXPLICIT SEQUENTIAL REPORT FILE
# ========================================================================
if passage_report_blocks:
    # Keeps narrative flowing left to right (sorted chronologically)
    passage_report_blocks.sort(key=lambda x: x["sort_key"])
    
    with open(OUTPUT_PASSAGE_FILE, "w", encoding="utf-8") as out:
        out.write("========================================================================\n")
        out.write("         MACRO-REFRAIN & LITURGICAL CHORUS PASSAGE SCAN                  \n")
        out.write("========================================================================\n")
        out.write(f"Target Scope:  {TARGET_BOOK}\n")
        out.write(f"Mapped Files:  {success_count} Sequential Narrative Chapters\n\n")
        
        for block in passage_report_blocks:
            out.write(block["text"])
            
    print(f"\n🏭 PASSAGE SCAN COMPLETE -> File generated: {OUTPUT_PASSAGE_FILE}")
else:
    print("\n❌ Error: No valid JSON files matched your parameter target boundaries.")
