import os
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd

def analyze_biblical_motifs(base_directory, target_file=None):
    all_records = []
    
    # MIDI values for E, G#, B (4th octave: 64, 68, 71. Adjust if your transcription uses a different octave)
    target_motif = [64, 68, 71]
    
    for root_dir, _, files in os.walk(base_directory):
        for file in files:
            if not file.lower().endswith('.mscz'):
                continue
                
            if target_file and file.upper() != target_file.upper():
                continue
                
            file_path = os.path.join(root_dir, file)
            book_chapter = os.path.splitext(file)[0]
            
            try:
                with zipfile.ZipFile(file_path, 'r') as z:
                    mscx_files = [f for f in z.namelist() if f.endswith('.mscx')]
                    if not mscx_files:
                        continue
                        
                    with z.open(mscx_files[0]) as xml_file:
                        tree = ET.parse(xml_file)
                        root = tree.getroot()
                        
                note_stream = []
                lyric_stream = []
                breath_anchors = []
                measure_mappings = []
                
                for measure in root.iter('Measure'):
                    measure_num = measure.get('number', '1') 
                    
                    for chord in measure.iter('Chord'):
                        note = chord.find('.//Note')
                        pitch_val = None
                        if note is not None:
                            pitch_elem = note.find('pitch')
                            if pitch_elem is not None:
                                pitch_val = int(pitch_elem.text)
                        
                        lyric_elem = chord.find('.//Lyrics/text')
                        text_val = lyric_elem.text if lyric_elem is not None else ""
                        
                        has_breath = chord.find('.//Breath') is not None
                        
                        note_stream.append(pitch_val)
                        lyric_stream.append(text_val)
                        breath_anchors.append(has_breath)
                        measure_mappings.append(measure_num)
                
                for i in range(len(note_stream) - 2):
                    current_window = note_stream[i:i+3]
                    if None in current_window:
                        continue
                        
                    if current_window == target_motif:
                        is_approach_to_atnah = False
                        associated_words = []
                        
                        lookahead_limit = min(i + 8, len(note_stream))
                        for j in range(i, lookahead_limit):
                            if lyric_stream[j]:
                                associated_words.append(lyric_stream[j])
                            if breath_anchors[j]:
                                is_approach_to_atnah = True
                                
                        all_records.append({
                            "Source_File": book_chapter,
                            "Measure": measure_mappings[i],
                            "Motif_Notes": str(current_window),
                            "Approaching_Atnah": is_approach_to_atnah,
                            "Context_Text_Stream": " ".join([w for w in associated_words if w])
                        })
                        
            except Exception as e:
                print(f"Error parsing file {file}: {str(e)}")
                
    return pd.DataFrame(all_records)

# --- EXECUTION ---
if __name__ == "__main__":
    workspace_path = r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores"
    
    print("Searching for GENESIS-001.mscz and analyzing motifs...")
    df_test = analyze_biblical_motifs(workspace_path, target_file="GENESIS-001.mscz")
    
    if df_test.empty:
        print("\n[Result] No exact E-G#-B (64, 68, 71) motif matches found in Genesis 1.")
    else:
        print(f"\n[Result] Found {len(df_test)} match(es):")
        # Tells pandas to display all columns nicely in cmd
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 1000)
        print(df_test)
