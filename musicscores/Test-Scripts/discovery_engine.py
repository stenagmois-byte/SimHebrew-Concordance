import os
import json
import re
import pandas as pd
from collections import Counter

# ========================================================================
# USER PARAMETERS (Change this target path to analyze any chapter)
# ========================================================================
EXPLICIT_FILE_PATH = "../The Psalms/PSALMS_003.json"
OUTPUT_PASSAGE_FILE = "Psalms_003_ARCHITECTURE.txt"

# ========================================================================
# 🔍 UNBIASED DISCOVERY ENGINE & HYPOTHESIS TESTING MODULE
# ========================================================================

def run_passage_discovery_engine(chapter_df, book_id, chapter_id):
    """
    A dense, high-utility Critical Apparatus that strips away all verbal clutter.
    Outputs sequences separated by plain spaces, tags counts compactly (e.g., x4),
    and flags off-tonic entries/opening ornaments with a visual anchor (★).
    """
    chapter_df['VERSE_NUM'] = pd.to_numeric(chapter_df['VERSE_CD'], errors='coerce')
    chapter_df = chapter_df.sort_values('VERSE_NUM').reset_index(drop=True)
    
    chapter_data = []
    all_pre_motifs = []
    all_post_motifs = []
    
    # ---------------------------------------------------------
    # PASS 1: EXTRACT COMPRESSED SPACE-SEPARATED PHRASES
    # ---------------------------------------------------------
    for vs_num, verse_group in chapter_df.groupby('VERSE_NUM', sort=False):
        valid_rows = verse_group[~verse_group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        if valid_rows.empty: continue
            
        notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        
        # Locate primary caesura divider (A4 in SHV prose system)
        atnah_indices = [i for i, note in enumerate(notes) if note == "A4"]
        
        # Detect Opening Ornament in the first syllable text payload
        verse_df = chapter_df[chapter_df['VERSE_CD'].astype(str).str.strip() == str(vs_num)]
        valid_v_rows = verse_df[~verse_df['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        first_syllable_text = str(valid_v_rows['LYRIC_SYLL'].iloc[0]).lower() if not valid_v_rows.empty else ""
        
        ornament_keywords = ["pazer", "shalshelet", "tsinnor", "zarqa", "telisha", "legarmeh"]
        is_ornamented_entry = any(orn in first_syllable_text for orn in ornament_keywords)
        
        if not atnah_indices:
            # Asymmetric line structure
            right_wing = []
            for n in notes:
                if not right_wing or n != right_wing[-1]: right_wing.append(n)
            pre_str, post_str = "None", " ".join(right_wing)
        else:
            atnah_idx = atnah_indices[0]
            
            # Compress first half (Space separated)
            pre_notes = []
            for i in range(atnah_idx + 1):
                if not pre_notes or notes[i] != pre_notes[-1]: pre_notes.append(notes[i])
            pre_str = " ".join(pre_notes)
            
            # Compress second half (Space separated)
            post_notes = notes[atnah_idx + 1:]
            post_syllables = syllables[atnah_idx + 1:]
            post_vector = []
            if post_notes:
                # Word-boundary cross-caesura check
                first_post_syllable = post_syllables[0] if post_syllables else ""
                if post_notes[0] == "A4" and not first_post_syllable.startswith("-"):
                    post_vector.append("A4")
                for n in post_notes:
                    if not post_vector or n != post_vector[-1]: post_vector.append(n)
            post_str = " ".join(post_vector) if post_vector else "End"
            
        chapter_data.append({
            "verse": vs_num, 
            "pre": pre_str, 
            "post": post_str, 
            "raw_notes": notes,
            "is_ornamented": is_ornamented_entry
        })
        
        if pre_str != "None": all_pre_motifs.append(pre_str)
        if post_str != "End": all_post_motifs.append(post_str)

    # Global counter metrics for set-wide occurrence summaries
    pre_counts = Counter(all_pre_motifs)
    post_counts = Counter(all_post_motifs)
    total_fsharp_verses = sum(1 for v in chapter_data if "F#4" in v['raw_notes'])
    
    report = [f"--- APPARATUS: {book_id[:4]} {chapter_id} (F#4 Accents: {total_fsharp_verses}) ---\n"]
    
     
    # ---------------------------------------------------------
    # PASS 3: DENSE CRITICAL APPARATUS PRINT LOOP (SCHEMA ALIGNED)
    # ---------------------------------------------------------
    for v in chapter_data:
        first_note = v['raw_notes'][0] if v['raw_notes'] else "E4"
        is_off_tonic = (first_note != "E4")
        
        # 1. Establish the Off-Tonic Bridge Symbol (★)
        bridge_symbol = "★ " if is_off_tonic else ""
        
        # 2. Extract from the explicit ORNAMENT_NAME column instead of lyric syllables
        verse_df = chapter_df[pd.to_numeric(chapter_df['VERSE_CD'], errors='coerce') == v['verse']]
        valid_v_rows = verse_df[~verse_df['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        
        # FIXED: Look directly at the data field where your JSON stores the string "zarqa"
        first_ornament_text = str(valid_v_rows['ORNAMENT_NAME'].iloc[0]).lower() if not valid_v_rows.empty else ""
        
        # 3. Precision Accent Ornament Translation
        ornament_symbol = ""
        if any(orn in first_ornament_text for orn in ["zarqa", "tsinnor", "tsinnoret"]):
            ornament_symbol = "∾ "   # Lazy S/Inverted S for Zarqa / Tsinnoret (Psalm 3:8)
        elif "revia" in first_ornament_text:
            ornament_symbol = "◆ "   # Solid Diamond for Revia
        elif "telisha" in first_ornament_text:
            ornament_symbol = "⚲ "   # Geometric Hook for Telisha-Gadol
        elif any(orn in first_ornament_text for orn in ["pazer", "shalshelet", "legarmeh"]):
            ornament_symbol = "~ "   # Standard wave for other major openings
            
        # Shorthand counts: Only print x[Count] if the pattern repeats (x > 1)
        pre_count_suffix = f" x{pre_counts[v['pre']]}" if pre_counts[v['pre']] > 1 else ""
        post_count_suffix = f" x{post_counts[v['post']]}" if post_counts[v['post']] > 1 else ""
        
        # Package and append the compact score lines
        pre_display = f"[{bridge_symbol}{ornament_symbol}{v['pre']}{pre_count_suffix}]"
        post_display = f"[{v['post']}{post_count_suffix}]" if v['post'] != "End" else "[End]"
        
        accent_tag = " [Unique F#]" if ("F#5" in v['raw_notes'] and total_fsharp_verses == 1) else ""
        report.append(f"  {v['verse']}: {pre_display} | {post_display}{accent_tag}\n")
        
    return "".join(report)
# ========================================================================
# 🎬 THE EXPLICIT ENTRY POINT (MAINTAINING PARAMETER FLUIDITY)
# ========================================================================
if __name__ == '__main__':
    if not os.path.exists(EXPLICIT_FILE_PATH):
        print(f"❌ Error: Could not find file at absolute target path: {EXPLICIT_FILE_PATH}")
    else:
        print(f"🚀 File locked successfully: {EXPLICIT_FILE_PATH}")
        
        file_base = os.path.basename(EXPLICIT_FILE_PATH)
        name_only, _ = os.path.splitext(file_base)
        
        match = re.search(r"^(.*?)[_.](\d+)$", name_only)
        if match:
            reflected_book = match.group(1).upper()
            reflected_chapter = match.group(2)
        else:
            reflected_book = name_only.upper()
            reflected_chapter = "001"
            
        try:
            with open(EXPLICIT_FILE_PATH, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                
            items_list = None
            if isinstance(raw_data, dict) and "results" in raw_data:
                res_data = raw_data["results"]
                if isinstance(res_data, list) and len(res_data) > 0:
                    first_res = res_data[0]
                    if isinstance(first_res, dict):
                        items_list = first_res.get("items")
                elif isinstance(res_data, dict):
                    items_list = res_data.get("items")
                    
            if items_list is None and isinstance(raw_data, dict):
                items_list = raw_data.get("items")

            if items_list is not None:
                df = pd.DataFrame(items_list)
                df.columns = df.columns.str.upper()
                
                # Execute engine with self-parsed, dynamic variables
                analysis_output = run_passage_discovery_engine(df, reflected_book, reflected_chapter)
                
                print("\n" + analysis_output)
                with open(OUTPUT_PASSAGE_FILE, "w", encoding="utf-8") as out:
                    out.write(analysis_output)
                    
                print(f"🏭 Discovery profile generated successfully: {OUTPUT_PASSAGE_FILE}")
            else:
                print("❌ Error: Could not extract 'items' array payload container.")
        except Exception as e:
            print(f"❌ Execution Exception: {str(e)}")
