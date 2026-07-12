import os
import json
import pandas as pd
from collections import Counter

# Direct absolute path to the target file from inside your Test-Scripts folder
EXPLICIT_FILE_PATH = "../The Psalms/PSALMS_096.json"
OUTPUT_PASSAGE_FILE = "Psalms-96-arch.txt"

# If your filename uses a hyphen instead of an underscore, toggle this line:
if not os.path.exists(EXPLICIT_FILE_PATH):
    EXPLICIT_FILE_PATH = "../Genesis/GENESIS-001.json"

import os
import json
import pandas as pd
from collections import Counter

def run_passage_discovery_engine(chapter_df, book_id, chapter_id):
    """
    A true discovery engine that maps sequential verse syntax, uncovers 
    unanticipated recurring melodic motifs, and tests catalyst hypotheses.
    """
    chapter_df['VERSE_NUM'] = pd.to_numeric(chapter_df['VERSE_CD'], errors='coerce')
    chapter_df = chapter_df.sort_values('VERSE_NUM').reset_index(drop=True)
    
    chapter_data = []
    all_pre_motifs = []
    all_post_motifs = []
    
    # ---------------------------------------------------------
    # PASS 1: EXTRACT THE NATURAL, UNBIASED MELODIC CONTOURS
    # ---------------------------------------------------------
    for vs_num, verse_group in chapter_df.groupby('VERSE_NUM', sort=False):
        valid_rows = verse_group[~verse_group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        if valid_rows.empty: continue
            
        notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        atnah_indices = [i for i, note in enumerate(notes) if note == "A4"]
        
        if not atnah_indices:
            # Asymmetric Right-Wing Line
            right_wing = []
            for n in notes:
                if not right_wing or n != right_wing[-1]: right_wing.append(n)
            pre_str, post_str = "None", " -> ".join(right_wing)
        else:
            atnah_idx = atnah_indices
            
            # Compress Pre-Atnah path
            pre_notes = []
            for i in range(atnah_idx + 1):
                if not pre_notes or notes[i] != pre_notes[-1]: pre_notes.append(notes[i])
            pre_str = " -> ".join(pre_notes)
            
            # Compress Post-Atnah path (Right Wing)
            post_notes = notes[atnah_idx + 1:]
            post_syllables = syllables[atnah_idx + 1:]
            post_vector = []
            if post_notes:
                if post_notes[0] == "A4" and not (post_syllables[0] if post_syllables else "").startswith("-"):
                    post_vector.append("A4")
                for n in post_notes:
                    if not post_vector or n != post_vector[-1]: post_vector.append(n)
            post_str = " -> ".join(post_vector) if post_vector else "End"
            
        chapter_data.append({"verse": vs_num, "pre": pre_str, "post": post_str, "raw_notes": notes})
        
        # Feed the discovery pools
        if pre_str != "None": all_pre_motifs.append(pre_str)
        if post_str != "End": all_post_motifs.append(post_str)

    # ---------------------------------------------------------
    # PASS 2: AUTOMATED EMBEDDED DISCOVERY (Finding the Unexpected)
    # ---------------------------------------------------------
    discovered_pre_refrains = {k for k, v in Counter(all_pre_motifs).items() if v >= 2}
    discovered_post_refrains = {k for k, v in Counter(all_post_motifs).items() if v >= 2}
    
    report = [
        "========================================================================\n",
        f"🔍 DISCOVERY PROFILE: {book_id[:4]} CHAPTER {chapter_id}\n",
        "========================================================================\n\n"
    ]
    
    # ---------------------------------------------------------
    # PASS 3: HYPOTHESIS CATALYST MATCHING & CHRONOLOGICAL PRINT
    # ---------------------------------------------------------
    for v in chapter_data:
        v_notes_str = " -> ".join(v['raw_notes'])
        tags = []
        
        # 1. Unbiased Discovery Tags (The unexpected structural echoes)
        if v['pre'] in discovered_pre_refrains:
            tags.append(f"[Echoed Pre-Atnah Motif: {v['pre']}]")
        if v['post'] in discovered_post_refrains:
            tags.append(f"[Echoed Right-Wing Chorus: {v['post']}]")
            
        # 2. Preloaded Catalyst Motifs (Testing your dynamic hunches)
        if "E4 -> G#4 -> B4 -> A4" in v_notes_str:
            tags.append("🌅 [Gen 1 Creation Motif]")
        if "E4 -> G#4 -> A4" in v_notes_str:
            tags.append("🌱 [Human Well-Being / Life Anchor]")
        if "G4 -> B4 -> E4" in v_notes_str or v['post'] == "G4 -> B4 -> E4":
            tags.append("🛐 [Liturgical Response Anchor]")
        if "C5" in v['raw_notes']:
            # Track high register stanza boundaries like Psalm 96
            c5_count = v['raw_notes'].count("C5")
            tags.append(f"🏛️ [High Register: C5 Stanza Pillar (x{c5_count})]")
            
        # Format the output line for maximum scannability
        tag_line = " | ".join(tags) if tags else "• Standard Narrative Progress"
        report.append(f"  Verse {v['verse']:03d}: Pre: [{v['pre']}] | Post: [{v['post']}] \n     ↳ {tag_line}\n\n")
        
    return "".join(report)

def extract_chapter_refrains(chapter_df, book_id, chapter_id):
    """
    Analyzes sequentially to locate your two structural choruses
    (The Post-Atnah Tonic Drop and the Evening/Morning Temporal Refrain).
    """
    chapter_df['VERSE_NUM'] = pd.to_numeric(chapter_df['VERSE_CD'], errors='coerce')
    chapter_df = chapter_df.sort_values('VERSE_NUM').reset_index(drop=True)
    
    chapter_sequence = []
    post_atnah_pool = []
    full_vector_pool = []
    
    for vs_num, verse_group in chapter_df.groupby('VERSE_NUM', sort=False):
        valid_rows = verse_group[~verse_group['SYLL_NOTE'].astype(str).str.strip().isin(['None', '', 'nan'])].reset_index(drop=True)
        if valid_rows.empty:
            continue
            
        notes = valid_rows['SYLL_NOTE'].astype(str).str.strip().tolist()
        syllables = valid_rows['LYRIC_SYLL'].astype(str).str.strip().tolist()
        
        atnah_indices = [i for i, note in enumerate(notes) if note == "A4"]
        
        # -----------------------------------------------------------------
        # CASE 1: INTENTIONAL OMISSION (No Mid-Verse Atnah Cadence Present)
        # -----------------------------------------------------------------
        if not atnah_indices:
            right_wing = []
            for n in notes:
                if not right_wing or n != right_wing[-1]: 
                    right_wing.append(n)
            pre_str = "None"
            post_str = " -> ".join(right_wing) if right_wing else "End"
            
        # -----------------------------------------------------------------
        # CASE 2: STANDARD CADENCE PRESENT (Extract Integer Index Safely)
        # -----------------------------------------------------------------
        else:
            # Extract the raw integer value out of index position 0
            atnah_idx = atnah_indices[0]
            
            # Pre-Atnah sequential reduction
            pre_notes = []
            for i in range(atnah_idx + 1):
                if not pre_notes or notes[i] != pre_notes[-1]: 
                    pre_notes.append(notes[i])
            pre_str = " -> ".join(pre_notes)
            
            # Post-Atnah right-wing reduction
            post_notes = notes[atnah_idx + 1:]
            post_syllables = syllables[atnah_idx + 1:]
            
            post_vector = []
            if post_notes:
                # Continuous phrase word-start boundary evaluation
                first_post_syllable = post_syllables[0] if post_syllables else ""
                if post_notes[0] == "A4" and not first_post_syllable.startswith("-"):
                    post_vector.append("A4")
                    
                for n in post_notes:
                    if not post_vector or n != post_vector[-1]: 
                        post_vector.append(n)
                        
            post_str = " -> ".join(post_vector) if post_vector else "End"

        # Safe sequential thought cache assignment
        chapter_sequence.append({"verse": vs_num, "pre": pre_str, "post": post_str})
        if post_str != "End": post_atnah_pool.append(post_str)
        full_vector_pool.append(f"Pre: [{pre_str}] | Post: [{post_str}]")

    post_refrains = {k for k, v in Counter(post_atnah_pool).items() if v >= 2}
    full_refrains = {k for k, v in Counter(full_vector_pool).items() if v >= 2}
    
    report_lines = [
        "========================================================================\n",
        f"📖 NARRATIVE ARCHITECTURE: {book_id} CHAPTER {chapter_id}\n",
        "========================================================================\n\n"
    ]
    
    for v_data in chapter_sequence:
        v_str = f"Pre: [{v_data['pre']}] | Post: [{v_data['post']}]"
        is_full_chorus = v_str in full_refrains
        is_post_chorus = v_data['post'] in post_refrains and not is_full_chorus
        
        # Explicitly tag the exact musicological anchors you defined
        marker = ""
        if v_data['post'].startswith("E4 -> E4 -> E4") or v_data['post'] == "E4":
            marker = " 📉 [Post-atnah tonic only]"
        elif "E4 -> F4 -> E4 -> G#4 -> F4 -> E4" in v_data['post']:
            marker = " 🌅 [Evening and Morning]"
        elif is_full_chorus: 
            marker = " 🔥 [Refrain]"
        elif is_post_chorus: 
            marker = " 🔁 [Recurring post-atnah motif]"
            
        report_lines.append(f"  Verse {v_data['verse']:03d}: {v_str}{marker}\n")
        
    return "".join(report_lines)

# --- DIRECT EXECUTION ENTRY POINT ---
if not os.path.exists(EXPLICIT_FILE_PATH):
    print(f"❌ Error: Could not find file at absolute target path: {EXPLICIT_FILE_PATH}")
    print("Please double check if your folder name is capitalized exactly ('Genesis' vs 'GENESIS').")
else:
    print(f"🚀 File locked successfully: {EXPLICIT_FILE_PATH}")
    try:
        with open(EXPLICIT_FILE_PATH, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
            
        # --- YOUR PROVEN STABLE RESILIENT LOADER ---
        # --- TARGETED RESILIENT LOADER FOR YOUR SPECIFIC GEOMETRY ---
        items_list = None
        
        if isinstance(raw_data, dict) and "results" in raw_data:
            res_data = raw_data["results"]
            
            # Case A: 'results' is a list (e.g., [ {"items": [...]} ] )
            if isinstance(res_data, list) and len(res_data) > 0:
                first_res = res_data[0]
                if isinstance(first_res, dict):
                    items_list = first_res.get("items")
            
            # Case B: 'results' is a direct dictionary (e.g., {"items": [...]} )
            elif isinstance(res_data, dict):
                items_list = res_data.get("items")
                
        # Fallback to look at root or raw array formats
        if items_list is None and isinstance(raw_data, dict):
            items_list = raw_data.get("items")

        if items_list is not None:
            df = pd.DataFrame(items_list)
            df.columns = df.columns.str.upper()
            
            # Generate the architecture profile
            analysis_output = run_passage_discovery_engine(df, "GENESIS", "001")

            #extract_chapter_refrains(df, "GENESIS", "001")
            
            # Print to screen instantly and save to file
            print("\n" + analysis_output)
            with open(OUTPUT_PASSAGE_FILE, "w", encoding="utf-8") as out:
                out.write(analysis_output)
            print(f"🏭 Analysis saved directly to: {OUTPUT_PASSAGE_FILE}")
        else:
            print("❌ Error: Could not extract 'items' array payload container.")
    except Exception as e:
        print(f"❌ Execution Exception: {str(e)}")
