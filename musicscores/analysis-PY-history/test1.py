import zipfile
import xml.etree.ElementTree as ET

mxl_path = "..\job\JOB-003.mxl"

# 1. Open the zip archive in memory
with zipfile.ZipFile(mxl_path, 'r') as archive:
    xml_name = [f for f in archive.namelist() if f.endswith('.xml') or f.endswith('.musicxml')][0]
    with archive.open(xml_name) as xml_file:
        tree = ET.parse(xml_file)
        root = tree.getroot()

# 2. Walk through the first few measures to see your specific tags
for measure in root.findall(".//measure")[:3]: # Look at first 3 measures
    print(f"\n=== Measure Number: {measure.get('number')} ===")
    
    # Check for text placements above the score
    for words in measure.findall(".//words"):
        print(f" Found Text Above Score: '{words.text}'")
        
    # Check for text in lyric tags
    for text in measure.findall(".//lyric/text"):
        print(f" Found Lyric Text: '{text.text}'")

    # Inspect the note elements inside this measure
    for note in measure.findall("note"):
        # Check if the note is a rest
        is_rest = note.find("rest") is not None
        
        if is_rest:
            print(" [Note Type]: REST (End of verse marker)")
        else:
            # Grab pitch information
            step = note.find(".//step")
            octave = note.find(".//octave")
            if step is not None and octave is not None:
                print(f" [Note Type]: PITCH {step.text}{octave.text}")
