import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import re

def extract_verse_prefix(text_string):
    if not text_string:
        return None
    match = re.search(r'(\d+\.\d+|\d+)', text_string.strip())
    return match.group(1) if match else None

def interpret_structural_role(verse, context_heb):
    """
    Musicological Interpretation Rules Engine: Evaluates the functional
    role of the tonic major triad based on syntax and text properties.
    """
    if not context_heb:
        return "Unknown Context"
    
    # Core interpretation logic mapping cosmic foundations vs narrative subsets
    if "בְּרֵאשִׁ֖ית" in context_heb or verse == "1.1":
        return "Acoustic Archetype: Primeval Cosmic Foundation / Sovereign Order"
    elif "בָּרָ֣א" in context_heb or "יָלַ֣ד" in context_heb:
        return "Generative Blueprint: Creation / Active Progenitor Manifestation"
    elif "וַיֹּאמְר֞וּ" in context_heb or "וַיֹּ֖אמֶר" in context_heb:
        return "Narrative Quotation Framework: Dialogue Initialization Hub"
    elif "אָר֣וּר" in context_heb:
        return "Disruption Boundary: Order Fracture / Judgment Inversion"
    else:
        return "Structural Signpost: Transition Matrix Approaching Caesura Wall"

def build_and_append_ledger():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_workspace = os.path.dirname(script_dir)
    excel_path = os.path.join(parent_workspace, "MUSICSTATS.xlsx")
    
    print("=" * 95)
    print("MUSICSTATS INTERPRETATION EXPANSION ENGINE")
    print("=" * 95)
    
    if not os.path.exists(excel_path):
        print(f"🚨 Error: Master spreadsheet matrix not found at:\n -> {excel_path}")
        return

    all_records = []
    
    # Gather music tracking vectors recursively across parent volumes
    for root_dir, _, files in os.walk(parent_workspace):
        if "analysis_scripts" in root_dir:
            continue
            
        for file in files:
            if not file.lower().endswith('.mscz') or "GENESIS-" not in file.upper():
                continue
                
            try:
                # FIXED: Added [0] to extract the string out of the split list
                chapter_part = file.upper().split("GENESIS-")[-1]
                chapter_num = int(chapter_part.split(".")[0])
                if chapter_num < 1 or chapter_num > 11:
                    continue
            except (ValueError, IndexError):
                continue
                
            file_path = os.path.join(root_dir, file)
            # FIXED: Explicitly pull index 0 to avoid tuple assignment issues
            clean_book_id = os.path.splitext(file)[0]
            
            try:
                with zipfile.ZipFile(file_path, 'r') as z:
                    mscx_matches = [f for f in z.namelist() if f.lower().endswith('.mscx')]
                    if mscx_matches:
                        with z.open(mscx_matches[0]) as xml_file:
                            root = ET.fromstring(xml_file.read())
                
                timeline = []
                current_measure = "1"
                current_hebrew_word = ""
                
                for elem in root.iter():
                    tag = elem.tag.split('}')[-1]
                    if tag == 'Measure':
                        val = elem.get('number')
                        if val is not None: current_measure = str(val)
                    elif tag == 'StaffText':
                        text_pieces = [t.text for t in elem.iter() if t.tag.split('}')[-1] == 'text' and t.text]
                        if text_pieces: current_hebrew_word = " ".join(text_pieces).strip()
                    elif tag == 'Breath':
                        timeline.append({'measure': current_measure, 'pitch': None, 'syllable': "", 'hebrew_word': "", 'caesura': True, 'is_rest': False})
                    elif tag == 'Rest':
                        current_hebrew_word = ""
                        timeline.append({'measure': current_measure, 'pitch': -1, 'syllable': "", 'hebrew_word': "", 'caesura': False, 'is_rest': True})
                    elif tag == 'Chord':
                        pitch_elem = elem.find('.//pitch')
                        lyric_pieces = [l.text for l in elem.iter() if l.tag.split('}')[-1] == 'text' and l.text]
                        lyric_val = "-".join(lyric_pieces).strip() if lyric_pieces else ""
                        has_caesura_break = elem.find('Breath') is not None or elem.find('.//Breath') is not None
                        pitch_val = int(pitch_elem.text) if (pitch_elem is not None and pitch_elem.text) else None
                        
                        if pitch_val is not None:
                            timeline.append({
                                'measure': current_measure, 'pitch': pitch_val, 'syllable': lyric_val,
                                'hebrew_word': current_hebrew_word, 'caesura': has_caesura_break, 'is_rest': False
                            })
                
                compressed_indices = []
                for idx, event in enumerate(timeline):
                    if event['pitch'] is not None and event['pitch'] != -1:
                        if not compressed_indices or timeline[compressed_indices[-1]]['pitch'] != event['pitch']:
                            compressed_indices.append(idx)
                        
                for i in range(len(compressed_indices) - 2):
                    if timeline[compressed_indices[i]]['pitch'] == 64 and timeline[compressed_indices[i+1]]['pitch'] == 68 and timeline[compressed_indices[i+2]]['pitch'] == 71:
                        start_tl_idx = compressed_indices[i]
                        words_collected_heb = []
                        words_collected_eng = []
                        is_atnah_caesura = False
                        
                        for k in range(start_tl_idx, len(timeline)):
                            evt = timeline[k]
                            if evt['hebrew_word'] and evt['hebrew_word'] not in words_collected_heb:
                                words_collected_heb.append(evt['hebrew_word'])
                            if evt['syllable'] and evt['syllable'] not in words_collected_eng:
                                words_collected_eng.append(evt['syllable'])
                            if evt['caesura']:
                                is_atnah_caesura = True
                                break
                        
                        assigned_verse = None
                        for word_chunk in words_collected_heb:
                            found_num = extract_verse_prefix(word_chunk)
                            if found_num:
                                assigned_verse = found_num
                                break
                        if not assigned_verse:
                            for rev_idx in range(start_tl_idx, -1, -1):
                                found_num = extract_verse_prefix(timeline[rev_idx]['hebrew_word'])
                                if found_num: assigned_verse = found_num; break
                        if not assigned_verse: assigned_verse = "1"
                        
                        cleaned_heb_words = []
                        verse_started = False
                        for w in words_collected_heb:
                            if assigned_verse in w: verse_started = True
                            if verse_started or assigned_verse == "1.1":
                                clean_w = re.sub(r'^' + re.escape(assigned_verse) + r'\s*', '', w).strip()
                                if clean_w and clean_w not in cleaned_heb_words: cleaned_heb_words.append(clean_w)
                                    
                        combined_hebrew_phrase = " ".join(cleaned_heb_words)
                        interpretation = interpret_structural_role(assigned_verse, combined_hebrew_phrase)
                        
                        if is_atnah_caesura and cleaned_heb_words:
                            all_records.append({
                                "Book_File": clean_book_id,
                                "Verse_ID": assigned_verse,
                                "Hebrew_Context_Text": combined_hebrew_phrase,
                                "Musicological_Interpretation": interpretation
                            })
            except Exception as e:
                print(f"Skipping {file}: {e}")

    # Step 4: Safely append the new analysis sheet to the master workbook using ExcelWriter
    df_new = pd.DataFrame(all_records)
    if df_new.empty:
        print("⚠ Operation aborted: No matching triad patterns found to commit.")
        return

    print(f"Read success! Extracted {len(df_new)} rows for matrix output mapping.")
    try:
        # Requires 'openpyxl' installed internally to support open writing modifications
        with pd.ExcelWriter(excel_path, mode='a', engine='openpyxl', if_sheet_exists='replace') as writer:
            df_new.to_excel(writer, sheet_name="Motif_Concordance_Map", index=False)
        print(f"🚀 Success! Locked new tab 'Motif_Concordance_Map' inside:\n -> {excel_path}")
    except Exception as ex:
        print(f"🚨 Write Loop Interrupted: Ensure the Excel sheet is closed! Details: {ex}")

if __name__ == "__main__":
    build_and_append_ledger()
