import os
import json
import html
import pandas as pd

def analyze_strophic_shapes(passage_df, output_file="psalm78_macro_patterns.txt"):
    """
    Condenses the massive syllable dataset into pure, non-repeating melodic paths
    per verse, and implements a multi-syllable sequence check for the Tuba.
    """
    print("\n=== RUNNING CONDENSED MACRO-PATTERN MAP (WITH MULTI-SYLLABLE TUBA CHECK) ===")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("========================================================================\n")
        f.write("             PSALM 78 PURE MELODIC SEQUENCE MAP                         \n")
        f.write("========================================================================\n\n")
        
        # Group by verse keeping the original database sequence intact (sort=False)
        for (ch, vs), group in passage_df.groupby(['CHAPTER_CD', 'VERSE_CD'], sort=False):
            group = group.reset_index(drop=True)
            if group.empty: 
                continue
            
            # 1. Collapse consecutive identical notes into a single chronological path
            raw_notes = group['SYLL_NOTE'].astype(str).tolist()
            condensed_path = []
            
            for note in raw_notes:
                if note != 'None' and note.strip() != "":
                    # Only append if it's a change in pitch
                    if not condensed_path or condensed_path[-1] != note:
                        condensed_path.append(note)
            
            pitch_sequence_str = " -> ".join(condensed_path)
            
            # 2. Check for the multi-syllable Tuba (Geresh followed by Revia within 3 syllables)
            ornaments = group['ORNAMENT_NAME'].astype(str).str.lower().str.strip().tolist()
            tuba_found = "NONE"
            
            for idx in range(len(ornaments)):
                if ornaments[idx] == 'geresh':
                    # Look ahead up to 3 syllables (indices +1, +2, +3)
                    lookahead_limit = min(idx + 4, len(ornaments))
                    for next_idx in range(idx + 1, lookahead_limit):
                        if ornaments[next_idx] == 'revia':
                            # Found the sequence! Log the pitch where the resolution (revia) lands
                            tuba_found = f"FOUND on {raw_notes[next_idx]}"
                            break
                    if "FOUND" in tuba_found:
                        break # Stop searching this verse once the Tuba boundary marker is confirmed
            
            # 3. Clean up the Hebrew text for a clean visual anchor
            heb = ""
            if 'HEB_TEXT' in group.columns:
                valid_heb = group['HEB_TEXT'].dropna()
                if not valid_heb.empty:
                    heb = html.unescape(str(valid_heb.iloc[0])).replace('\n', ' ').strip()
                    heb = (heb[:40] + '...') if len(heb) > 40 else heb

            # 4. Write a single, dense line per verse
            f.write(f"Verse {ch}:{vs} | Tuba: {tuba_found.ljust(15)} | Text: {heb.ljust(45)}\n")
            f.write(f"   🎵 Path: {pitch_sequence_str}\n")
            f.write("-" * 90 + "\n")
            
    print(f"✅ Condensed macro map saved successfully to: {output_file}")


if __name__ == "__main__":
    json_path = os.path.join("..", "The Psalms", "PSALMS_078.json")
    output_filename = "psalm78_macro_patterns.txt"
    
    print(f"Targeting dataset file: {os.path.abspath(json_path)}")
    
    if not os.path.exists(json_path):
        print(f"❌ Error: Could not find the file at {json_path}")
        print("Please verify your folder names. 'The Psalms' must exactly match case.")
    else:
        with open(json_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
        
        # Structure-agnostic extraction for Oracle SQL Developer outputs
        if isinstance(raw_data, list):
            # If the root is a list, extract from the first element
            items_list = raw_data[0]["results"]["items"]
        elif "results" in raw_data and isinstance(raw_data["results"], list):
            # If results is wrapped as a list container
            items_list = raw_data["results"][0]["items"]
        else:
            # Standard single-object root dict
            items_list = raw_data["results"]["items"]
        
        # Create standard Pandas Dataframe
        selected_passage = pd.DataFrame(items_list)
        selected_passage.columns = selected_passage.columns.str.upper()
        
        analyze_strophic_shapes(selected_passage, output_file=output_filename)
