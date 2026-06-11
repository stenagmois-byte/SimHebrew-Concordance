import os
import shutil
import xml.etree.ElementTree as ET

# Unicode glyph for 1428 (Zaqef-Qaton)
ZAQEF_QATON_GLYPH = "\u0594"

def patch_measure_xml(measure_element):
    """
    Surgically inspects a measure. Finds the absolute final note of the word
    carrying the Zaqef-Qaton, and injects the breath mark precisely there.
    """
    measure_xml = ET.tostring(measure_element, encoding='utf-8').decode('utf-8')
    if ZAQEF_QATON_GLYPH not in measure_xml:
        return False
        
    notes_in_measure = measure_element.findall(".//note")
    
    # 1. Exclusion Check: If ANY note has a duration of 3 or a breath mark, skip it!
    for note in notes_in_measure:
        duration_elem = note.find("duration")
        if duration_elem is not None and duration_elem.text == "3":
            return False
            
        note_xml_lower = ET.tostring(note, encoding='utf-8').decode('utf-8').lower()
        if "breath" in note_xml_lower or "comma" in note_xml_lower:
            return False

    # 2. TARGET LOCKING: Find the LAST note that ends the accented word.
    target_word_end_note = None
    
    # Scan all notes and keep updating so we truly grab the LAST syllable ('end')
    for note in notes_in_measure:
        if note.find("rest") is not None:
            continue
            
        syllabic_elem = note.find(".//lyric/syllabic")
        if syllabic_elem is not None and syllabic_elem.text == "end":
            target_word_end_note = note  # REMOVED 'break' to capture the true final syllable

    # Fallback: If no explicit 'end' tag is found, look for the LAST note with lyric text
    if target_word_end_note is None:
        for note in notes_in_measure:
            if note.find(".//lyric/text") is not None:
                target_word_end_note = note  # REMOVED 'break' to get the last text-bearing note

    # 3. SURGICAL INJECTION WITH MUSICXML SCHEMA COMPLIANCE
    if target_word_end_note is not None:
        # Construct the exact MuseScore-compatible XML structure
        notations = ET.Element("notations")
        articulations = ET.SubElement(notations, "articulations")
        ET.SubElement(articulations, "breath-mark", {
            "default-x": "41", 
            "default-y": "11", 
            "placement": "above"
        })
        
        # To comply with the MusicXML schema and force the engine to render the breath
        # after the note's main visual body, we position it carefully.
        # It must come after <pitch>, <duration>, <voice>, and <type> if they exist.
        insert_index = len(target_word_end_note)
        for idx, child in enumerate(target_word_end_note):
            if child.tag in ['lyric', 'notations']:
                insert_index = idx
                break
        
        target_word_end_note.insert(insert_index, notations)
        return True

    return False

def run_global_patch_engine():
    print("=" * 105)
    # Register namespaces to prevent Python from corrupting your file wrappers with 'ns0:' tags
    ET.register_namespace('', 'http://idpf.org') 
    print("MUSICXML PATCH ENGINE: EXECUTING PRECISION WORD-LOCKED BREATH INJECTIONS")
    print("=" * 105)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    backup_dir = os.path.join(parent_dir, "_PRE_PATCH_BACKUP")
    print(f"Creating an absolute safety backup of files inside:\n -> {backup_dir}\n")
    
    all_xml_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP" in dirpath or "analysis_scripts" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                all_xml_files.append(os.path.join(dirpath, filename))
                
    total_patched_count = 0
    files_modified_count = 0
    
    for full_file_path in all_xml_files:
        try:
            tree = ET.parse(full_file_path)
            root = tree.getroot()
            
            file_changed = False
            for measure in root.findall(".//measure"):
                if patch_measure_xml(measure):
                    file_changed = True
                    total_patched_count += 1
            
            if file_changed:
                files_modified_count += 1
                relative_path = os.path.relpath(full_file_path, parent_dir)
                
                # Copy original pristine file to backup tree
                backup_file_path = os.path.join(backup_dir, relative_path)
                os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                shutil.copy2(full_file_path, backup_file_path)
                
                # Overwrite original local file with precision injection
                tree.write(full_file_path, encoding="utf-8", xml_declaration=True)
                print(f" 🛠️ [Patched & Word-Locked] {relative_path}")
                
        except Exception as e:
            print(f" 🚨 [Error File Process] Skipping {os.path.basename(full_file_path)}: {e}")

    print("\n" + "=" * 105)
    print("PATCH OPERATION FINALIZED SUCCESSFUL.")
    print(f" Total chapter files modified and rewritten: {files_modified_count}")
    print(f" Total word-locked breath-mark injections:  {total_patched_count}")
    print("=" * 105)

if __name__ == "__main__":
    run_global_patch_engine()
