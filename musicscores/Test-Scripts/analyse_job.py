import os
import zipfile
import re
import xml.etree.ElementTree as ET

# 1. Point to the Job directory one level up
job_dir = "../Job"

print("==================================================")
print("   COMPUTATIONAL ANALYSIS OF THE BOOK OF JOB      ")
print("==================================================\n")

# 2. Find and sort all .mxl files in the Job folder
mxl_files = sorted([f for f in os.listdir(job_dir) if f.lower().endswith('.mxl')])

for filename in mxl_files:
    mxl_path = os.path.join(job_dir, filename)
    print(f"\n--- Analyzing File: {filename} ---")
    
    try:
        # Open and parse the MXL archive in memory
        with zipfile.ZipFile(mxl_path, 'r') as archive:
            xml_name = [f for f in archive.namelist() if f.endswith('.xml') or f.endswith('.musicxml')]
            if not xml_name:
                continue
                
            with archive.open(xml_name[0]) as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
        
        current_verse = None
        
        # Traverse measures to look for verse markers
        for measure in root.findall(".//measure"):
            for words in measure.findall(".//words"):
                text = words.text if words.text else ""
                
                # Extract chapter.verse patterns (e.g., "3.7")
                match = re.match(r"^(\d+)\.(\d+)\s*", text)
                if match:
                    chap_num = match.group(1)
                    verse_num = match.group(2)
                    verse_id = f"Verse {verse_num}"
                    
                    if verse_id != current_verse:
                        current_verse = verse_id
                        
                        # Find the first true melodic pitch following this marker
                        first_pitch = None
                        for note in measure.findall("note"):
                            if note.find("rest") is None:
                                step = note.find(".//step")
                                octave = note.find(".//octave")
                                if step is not None and octave is not None:
                                    first_pitch = f"{step.text}{octave.text}"
                                    break
                        
                        # Highlight high C notes (C5 is common, C6 is octave higher depending on register)
                        if first_pitch in ["C5", "C6"]:
                            print(f"  ⭐ {verse_id} starts on HIGH C ({first_pitch}) -> Structural Stanza Change!")
                        elif first_pitch:
                            print(f"   • {verse_id} starts on {first_pitch}")
                            
    except Exception as e:
        print(f"Error reading {filename}: {e}")
