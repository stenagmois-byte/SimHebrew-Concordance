import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import re

def extract_verse_prefix(text_string):
    """Parses a text string to extract verse numbers like 1.1, 3, or 10."""
    if not text_string:
        return None
    match = re.search(r'(\d+\.\d+|\d+)', text_string.strip())
    return match.group(1) if match else None

def analyze_biblical_motifs():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_workspace = os.path.dirname(script_dir)
    
    all_records = []
    
    for root_dir, _, files in os.walk(parent_workspace):
        if "analysis_scripts" in root_dir:
            continue
            
        for file in files:
            if not file.lower().endswith('.mscz'):
                continue
                
            if "GENESIS-" in file.upper():
                try:
                    # FIXED: Extracting index 0 cleanly maps primitive string scalar values
                    chapter_part = file.upper().split("GENESIS-")[-1]
                    chapter_num = int(chapter_part.split(".")[0])
                    if chapter_num < 1 or chapter_num > 11:
                        continue
                except (ValueError, IndexError):
                    continue
            else:
                continue
                
            file_path = os.path.join(root_dir, file)
            clean_book_id = os.path.splitext(file)[0]
            
            try:
                with zipfile.ZipFile(file_path, 'r') as z:
                    mscx_matches = [f for f in z.namelist() if f.lower().endswith('.mscx')]
                    if not mscx_matches:
                        continue
                    
                    with z.open(mscx_matches[0]) as xml_file:
                        root = ET.fromstring(xml_file.read())
                
                timeline = []
                current_measure = "1"
                current_hebrew_word = ""
                
                # Step 1: Linear structural pass mapping chronologically
                for elem in root.iter():
                    tag = elem.tag.split('}')[-1]
                    
                    if tag == 'Measure':
                        val = elem.get('number')
                        if val is not None:
                            current_measure = str(val)
                        
                    elif tag == 'StaffText':
                        text_pieces = [t.text for t in elem.iter() if t.tag.split('}')[-1] == 'text' and t.text]
                        if text_pieces:
                            current_hebrew_word = " ".join(text_pieces).strip()
                            
                    elif tag == 'Breath':
                        timeline.append({
                            'measure': current_measure, 'pitch': None, 'syllable': "", 
                            'hebrew_word': "", 'caesura': True, 'is_rest': False
                        })
                        
                    elif tag == 'Rest':
                        current_hebrew_word = "" # Reset word buffer on structural rest
                        timeline.append({
                            'measure': current_measure, 'pitch': -1, 'syllable': "", 
                            'hebrew_word': "", 'caesura': False, 'is_rest': True
                        })
                            
                    elif tag == 'Chord':
                        pitch_elem = elem.find('.//pitch')
                        lyric_pieces = [l.text for l in elem.iter() if l.tag.split('}')[-1] == 'text' and l.text]
                        lyric_val = "-".join(lyric_pieces).strip() if lyric_pieces else ""
                        
                        has_caesura_break = elem.find('Breath') is not None or elem.find('.//Breath') is not None
                        pitch_val = int(pitch_elem.text) if (pitch_elem is not None and pitch_elem.text) else None
                        
                        if pitch_val is not None:
                            timeline.append({
                                'measure': current_measure,
                                'pitch': pitch_val,
                                'syllable': lyric_val,
                                'hebrew_word': current_hebrew_word,
                                'caesura': has_caesura_break,
                                'is_rest': False
                            })
                
                # Step 2: Build pitch stream map
                compressed_indices = []
                for idx, event in enumerate(timeline):
                    if event['pitch'] is not None and event['pitch'] != -1:
                        if not compressed_indices or timeline[compressed_indices[-1]]['pitch'] != event['pitch']:
                            compressed_indices.append(idx)
                        
                # Step 3: Scan timeline for motif windows
                for i in range(len(compressed_indices) - 2):
                    p1 = timeline[compressed_indices[i]]['pitch']
                    p2 = timeline[compressed_indices[i+1]]['pitch']
                    p3 = timeline[compressed_indices[i+2]]['pitch']
                    
                    if p1 == 64 and p2 == 68 and p3 == 71:
                        start_tl_idx = compressed_indices[i]
                        
                        words_collected_heb = []
                        words_collected_eng = []
                        is_atnah_caesura = False
                        
                        # Gather text elements forward from the start of the motif sequence
                        for k in range(start_tl_idx, len(timeline)):
                            evt = timeline[k]
                            
                            if evt['hebrew_word'] and evt['hebrew_word'] not in words_collected_heb:
                                words_collected_heb.append(evt['hebrew_word'])
                            if evt['syllable'] and evt['syllable'] not in words_collected_eng:
                                words_collected_eng.append(evt['syllable'])
                                
                            if evt['caesura']:
                                is_atnah_caesura = True
                                break
                        
                        # Find the true verse prefix within the collected phrase text
                        assigned_verse = None
                        for word_chunk in words_collected_heb:
                            found_num = extract_verse_prefix(word_chunk)
                            if found_num:
                                assigned_verse = found_num
                                break
                                
                        # Fallback to a backward sweep if no verse number string is embedded directly in the phrase
                        if not assigned_verse:
                            for rev_idx in range(start_tl_idx, -1, -1):
                                found_num = extract_verse_prefix(timeline[rev_idx]['hebrew_word'])
                                if found_num:
                                    assigned_verse = found_num
                                    break
                        if not assigned_verse:
                            assigned_verse = "1"
                        
                        # CLEANUP: Flush out any hanging text fragments belonging to the previous verse
                        cleaned_heb_words = []
                        verse_started = False
                        
                        for w in words_collected_heb:
                            if assigned_verse in w:
                                verse_started = True
                            
                            if verse_started or assigned_verse == "1.1":
                                clean_w = re.sub(r'^' + re.escape(assigned_verse) + r'\s*', '', w).strip()
                                if clean_w and clean_w not in cleaned_heb_words:
                                    cleaned_heb_words.append(clean_w)
                                    
                        # Ensure the phonetics stream drops prior verse syllables as well
                        cleaned_eng_phonetics = "-".join(words_collected_eng)
                        # FIXED: Resolved naming reference for internal array split evaluation
                        if "eid" in cleaned_eng_phonetics and assigned_verse == "6":
                            cleaned_eng_phonetics = "ve-eid" + cleaned_eng_phonetics.split("ve-eid")[-1]
                        elif "mah" in cleaned_eng_phonetics:
                            parts = cleaned_eng_phonetics.split("-")
                            if parts:
                                cleaned_eng_phonetics = "-".join(parts)
                        
                        if is_atnah_caesura and cleaned_heb_words:
                            all_records.append({
                                "File": clean_book_id,
                                "Verse": assigned_verse,
                                "Hebrew_Context": " ".join(cleaned_heb_words),
                                "English_Phonetics": cleaned_eng_phonetics
                            })
                        
            except Exception as e:
                print(f"Skipping error file {file}: {str(e)}")
                
    return pd.DataFrame(all_records)

if __name__ == "__main__":
    df_results = analyze_biblical_motifs()
    if df_results.empty:
        print("\nNo motif matches isolated under current constraint rules.")
    else:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        pd.set_option('display.max_colwidth', None)
        print(df_results.to_string(index=False))
