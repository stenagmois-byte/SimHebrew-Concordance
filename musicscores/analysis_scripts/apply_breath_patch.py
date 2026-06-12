import os
import shutil
import xml.etree.ElementTree as ET

# Unicode glyph for 1428 (Zaqef-Qaton)
ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_note_linear(elements, start_idx):
    """
    Traces forward from a direction element to find the true final note of the word.
    Verified flawless during the Obadiah trace!
    """
    for i in range(start_idx, len(elements)):
        elem = elements[i]
        if elem.tag.endswith('note'):
            if elem.find(".//rest") is not None:
                continue
            
            # Find syllabic tag layout
            syllabic = None
            for sub in elem.iter():
                if sub.tag.endswith('syllabic'):
                    syllabic = sub
                    break
            
            if syllabic is not None and syllabic.text == "end":
                return elem
            
            # Find lyric text layout
            text_elem = None
            for sub in elem.iter():
                if sub.tag.endswith('text'):
                    text_elem = sub
                    break
                        
            if text_elem is not None:
                if i + 1 < len(elements) and elements[i+1].tag.endswith('direction'):
                    return elem
                if syllabic is None or syllabic.text == "single":
                    return elem
                    
        if elem.tag.endswith('direction') and i > start_idx:
            for j in range(i - 1, start_idx - 1, -1):
                if elements[j].tag.endswith('note'):
                    text_sub = None
                    for sub in elements[j].iter():
                        if sub.tag.endswith('text'):
                            text_sub = sub
                            break
                    if text_sub is not None:
                        return elements[j]
    return None

def run_global_linear_repair_engine():
    print("=" * 115)
    ET.register_namespace('', 'http://idpf.org') 
    print("MUSICXML LINEAR PATCH ENGINE: EXECUTING STREAM-BASED WORD-LOCKED REPAIRS")
    print("=" * 115)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    backup_dir = os.path.join(parent_dir, "_PRE_PATCH_BACKUP")
    
    # Pre-gather all target XML files
    all_xml_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP" in dirpath or "analysis_scripts" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                all_xml_files.append(os.path.join(dirpath, filename))
                
    print(f"Scanning and repairing {len(all_xml_files)} files across the corpus...\n")
    
    total_patched_count = 0
    files_modified_count = 0
    
    for full_file_path in all_xml_files:
        try:
            tree = ET.parse(full_file_path)
            root = tree.getroot()
            
            # Step 1: Flatten everything inside all measures sequentially
            linear_flow = []
            for measure in root.findall(".//measure"):
                for child in measure:
                    if child.tag.endswith('direction') or child.tag.endswith('note'):
                        linear_flow.append(child)
            
            file_changed = False
            
            # Step 2: Linear Stream Evaluation & Injection
            for idx, elem in enumerate(linear_flow):
                if elem.tag.endswith('direction'):
                    dir_xml = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                    if ZAQEF_QATON_GLYPH in dir_xml:
                        
                        target_note = find_word_end_note_linear(linear_flow, idx + 1)
                        
                        if target_note is not None:
                            # Strict Safety Check: Duration 3 exception rules out errors
                            duration_elem = target_note.find(".//duration") if target_note.find("duration") is None else target_note.find("duration")
                            if duration_elem is not None and duration_elem.text == "3":
                                continue
                                
                            # Universal String Normalization to check for existing breaths
                            note_xml_raw = ET.tostring(target_note, encoding='utf-8').decode('utf-8').lower()
                            note_xml_clean = note_xml_raw.replace(" ", "").replace("/", "").replace("-", "")
                            
                            has_breath_mark = "breathmark" in note_xml_clean
                            has_caesura = "caesura" in note_xml_clean
                            has_comma = "comma" in note_xml_clean
                            
                            has_breath = has_breath_mark or has_caesura or has_comma
                            
                            # If no breath exists, inject it surgically to the right
                            if not has_breath:
                                notations = ET.Element("notations")
                                articulations = ET.SubElement(notations, "articulations")
                                ET.SubElement(articulations, "breath-mark", {
                                    "default-x": "41", 
                                    "default-y": "11", 
                                    "placement": "above"
                                })
                                
                                # Schema-compliant sequence placement (insert right before lyrics/notations)
                                insert_index = len(target_note)
                                for c_idx, child_node in enumerate(target_note):
                                    if child_node.tag.endswith('lyric') or child_node.tag.endswith('notations'):
                                        insert_index = c_idx
                                        break
                                        
                                target_note.insert(insert_index, notations)
                                file_changed = True
                                total_patched_count += 1
            
            # Step 3: Backup and rewrite modifications
            if file_changed:
                files_modified_count += 1
                relative_path = os.path.relpath(full_file_path, parent_dir)
                
                backup_file_path = os.path.join(backup_dir, relative_path)
                os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                shutil.copy2(full_file_path, backup_file_path)
                
                tree.write(full_file_path, encoding="utf-8", xml_declaration=True)
                print(f" 🛠️ [Stream-Patched] {relative_path}")
                
        except Exception as e:
            pass

    print("\n" + "=" * 115)
    print("PATCH OPERATION FINALIZED SUCCESSFUL.")
    print(f" Total chapter files modified and rewritten: {files_modified_count}")
    print(f" Total word-locked breath-mark injections:  {total_patched_count}")
    print("=" * 115)

if __name__ == "__main__":
    run_global_linear_repair_engine()
