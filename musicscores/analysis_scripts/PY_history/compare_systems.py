import os
import xml.etree.ElementTree as ET

def extract_melody_from_musicxml(xml_path):
    """
    Parses a MusicXML file and returns a simple string of pitches 
    and any accidental markers associated with them.
    """
    if not os.path.exists(xml_path):
        return None
        
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        notes_sequence = []
        
        # Loop through all measures and notes in the MusicXML structure
        for note in root.findall(".//note"):
            # Skip rests
            if note.find("rest") is not None:
                continue
                
            pitch = note.find("pitch")
            if pitch is not None:
                step = pitch.find("step").text  # e.g., 'E', 'F', 'G'
                
                # Check for an accidental (like a sharp sign '#')
                accidental_element = note.find("accidental")
                accidental = ""
                if accidental_element is not None:
                    if accidental_element.text == "sharp":
                        accidental = "#"
                    elif accidental_element.text == "flat":
                        accidental = "b"
                        
                # Format to look like your note nomenclature
                note_name = f"{step.lower()}{accidental}"
                notes_sequence.append(note_name)
                
        return notes_sequence
    except Exception as e:
        print(f"  [Error] Failed parsing XML file {os.path.basename(xml_path)}: {e}")
        return None

def run_system_comparison():
    print("=" * 85)
    print("CANONICAL TEXT COMPARISON ENGINE: PROSE (1 CHRONICLES) VS. POETRY (PSALM 96)")
    print("=" * 85)
    
    # Locate files relative to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Define paths to your target files in the repository
    chronicles_path = os.path.join(parent_dir, "1 CHRONICLES 16.xml")
    psalm_path = os.path.join(parent_dir, "PSALMS 96.xml")
    
    print("Extracting note arrays from MusicXML database files...")
    chronicles_notes = extract_melody_from_musicxml(chronicles_path)
    psalm_notes = extract_melody_from_musicxml(psalm_path)
    
    if not chronicles_notes or not psalm_notes:
        print("\n[Warning] File matching failed!")
        print(f"Ensure files match exactly: \n -> {chronicles_path}\n -> {psalm_path}")
        return

    # For 1 Chronicles 16, we want to isolate verses 23-33
    # (Note: In a true syllable trace, you can slice by exact index. 
    # For day one, we will look at the macro-level differences of the full files)
    
    print("\n" + "-" * 50)
    print("MELODIC COMPREHENSIVE PROFILES")
    print("-" * 50)
    print(f"Total notes in 1 Chronicles 16 Score : {len(chronicles_notes)}")
    print(f"Total notes in Psalm 96 Score        : {len(psalm_notes)}")
    
    # Let's inspect the opening musical gestures side-by-side
    print("\n" + "-" * 50)
    print("OPENING MOTIF COMPARISON (First 20 notes)")
    print("-" * 50)
    
    chron_snippet = " ".join(chronicles_notes[:20])
    psalm_snippet = " ".join(psalm_notes[:20])
    
    print(f"Prose (1 Chron 16) : {chron_snippet}")
    print(f"Poetry (Psalm 96)  : {psalm_snippet}")
    
    # Calculate the frequency of key structural accidentals
    print("\n" + "-" * 50)
    print("MODAL ACCIDENTAL ACCUMULATION SCAN")
    print("-" * 50)
    
    print(f"Prose (1 Chron 16) -> Total sharps (#): {chronicles_notes.count('f#') + chronicles_notes.count('g#')}")
    print(f"Poetry (Psalm 96)  -> Total sharps (#): {psalm_notes.count('f#') + psalm_notes.count('g#')}")
    
    print("\n" + "=" * 85)

if __name__ == "__main__":
    run_system_comparison()
