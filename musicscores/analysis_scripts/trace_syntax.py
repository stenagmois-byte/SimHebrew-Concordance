import xml.etree.ElementTree as ET
import re

# Targeting your clean, uncompressed XML file directly
xml_path = "../Job/JOB-003.xml"

print("==========================================================")
print("     EXACT MEASURE AND VERSE SYNTAX TRACE: JOB 3          ")
print("==========================================================\n")

tree = ET.parse(xml_path)
root = tree.getroot()

current_verse_context = "Unknown Verse"

# Iterate through every measure by its actual layout structure
for measure in root.findall(".//measure"):
    measure_num = measure.get("number", "Unknown")
    
    # Check if a new verse text marker (like '3.1') appears above the score in this measure
    for words in measure.findall(".//words"):
        text = words.text if words.text else ""
        if re.match(r"^\d+\.\d+", text.strip()):
            current_verse_context = f"Verse {text.strip()}"

    # Collect notes inside this specific measure sequentially
    notes = measure.findall("note")
    for idx, note in enumerate(notes):
        if note.find("rest") is not None:
            continue
            
        step = note.find(".//step")
        octave = note.find(".//octave")
        
        if step is not None and octave is not None:
            pitch = step.text
            
            # If we hit an A, inspect what came immediately before it to check your law
            if pitch == 'A':
                prev_pitch = "START OF MEASURE"
                if idx > 0:
                    prev_step = notes[idx-1].find(".//step")
                    if prev_step is not None:
                        prev_pitch = prev_step.text
                        
                print(f"[{current_verse_context}] Measure {measure_num} -> Note A is approached from: {prev_pitch}")
