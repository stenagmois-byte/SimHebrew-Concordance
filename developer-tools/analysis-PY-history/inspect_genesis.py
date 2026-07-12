import os
import zipfile
import xml.etree.ElementTree as ET

def diagnose_mscz_stream(mscz_filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mscz_path = os.path.join(script_dir, mscz_filename)
    
    print("=" * 90)
    print(f"DIAGNOSTIC STREAM DECODER: DECONSTRUCTING {mscz_filename}")
    print("=" * 90)
    
    if not os.path.exists(mscz_path):
        print(f"Error: Could not locate file at:\n -> {mscz_path}")
        return
        
    try:
        # Unzip and extract the XML code layer
        with zipfile.ZipFile(mscz_path, 'r') as archive:
            mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            if not mscx_files:
                print("Error: No plain-text .mscx score file found inside container.")
                return
            
            with archive.open(mscx_files[0]) as file_stream:
                xml_data = file_stream.read()
                
        root = ET.fromstring(xml_data)
        
        # Comprehensive recursive extraction targeting structural content
        print(f"XML Tree Root Node: <{root.tag}>")
        print("\nSTREAMING CHRONOLOGICAL EVENTS (FIRST 40 HIGHLIGHTS):")
        print("-" * 90)
        print(f"{'MEASURE':<10} | {'ELEMENT TYPE':<15} | {'VALUES DETECTED / INTERNAL STREAM DATA'}")
        print("-" * 90)
        
        current_measure = "0"
        printed_count = 0
        
        # Traverse every single subnode across all levels of the tree hierarchy
        for elem in root.iter():
            tag = elem.tag.split('}')[-1] # Remove XML namespace variants
            
            if tag == 'Measure':
                current_measure = elem.get('number', current_measure)
                
            elif tag == 'Chord':
                # Peek ahead inside this specific chord frame to isolate child notes
                pitches = [p.text for p in elem.findall('.//pitch')]
                if pitches:
                    print(f"Bar {current_measure:<5} | {'<Chord/Notes>':<15} | MIDI Pitches Found: {', '.join(pitches)}")
                    printed_count += 1
                    
            elif tag == 'text' and elem.text and elem.text.strip():
                # Capture Hebrew syllables, lyrics, text tokens, or custom text formatting
                cleaned_text = elem.text.strip()
                print(f"Bar {current_measure:<5} | {'<Text/Lyrics>':<15} | \"{cleaned_text}\"")
                printed_count += 1
                
            elif tag == 'Breath':
                # Check for your linear patched phrase breaks
                symbol_type = elem.find('.//symbol')
                sym_text = symbol_type.text if symbol_type is not None else "breathMarkComma"
                print(f"Bar {current_measure:<5} | {'<Breath Mark>':<15} | Type: {sym_text} [AGOGIC BOUNDARY]")
                printed_count += 1
                
            if printed_count >= 40:
                break
                
        print("-" * 90)
        print("💡 CRITICAL CHECK: Look at the 'MIDI Pitches Found' values above.")
        print("Note the 3-number sequence representing your E Major triad tonic opening.")
        print("Update the `target_motif = [...]` array in the main script to match this octave.")
        print("=" * 90)
        
    except Exception as e:
        print(f"Execution failed on parser loop: {e}")

if __name__ == "__main__":
    diagnose_mscz_stream("GENESIS-001.mscz")
