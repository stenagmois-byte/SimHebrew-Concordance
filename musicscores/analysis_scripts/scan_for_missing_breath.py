import os
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def scan_measure_for_true_error(measure_element):
    """
    Bob's Explicit Truth Conditions:
    - Must contain Zaqef-Qaton.
    - If ANY note has a duration of 3 -> NOT an error.
    - If ANY note has a breath mark -> NOT an error.
    - Otherwise -> Flag as a genuine error.
    """
    measure_xml = ET.tostring(measure_element, encoding='utf-8').decode('utf-8')
    if ZAQEF_QATON_GLYPH not in measure_xml:
        return False
        
    notes_in_measure = measure_element.findall(".//note")
    for note in notes_in_measure:
        duration_elem = note.find("duration")
        if duration_elem is not None and duration_elem.text == "3":
            return False
            
        note_xml_lower = ET.tostring(note, encoding='utf-8').decode('utf-8').lower()
        if "breath" in note_xml_lower or "comma" in note_xml_lower:
            return False

    return True

def run_global_diagnostic_report():
    print("=" * 105)
    print("MUSICXML COMPILER: ISOLATING UNRESOLVED GENUINE ERRORS ONLY")
    print("=" * 105)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    all_xml_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP" in dirpath or "analysis_scripts" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                all_xml_files.append(os.path.join(dirpath, filename))
                
    print(f"Scanning {len(all_xml_files)} files...\n")
    print(f"{'FILE PATH LOCATION':<65} | {'MEASURE NUMBER'}")
    print("-" * 105)
    
    total_anomalies_found = 0
    
    for full_file_path in all_xml_files:
        try:
            tree = ET.parse(full_file_path)
            root = tree.getroot()
            
            for measure in root.findall(".//measure"):
                measure_num = measure.get('number', 'Unknown')
                if scan_measure_for_true_error(measure):
                    total_anomalies_found += 1
                    relative_path = os.path.relpath(full_file_path, parent_dir)
                    print(f" ⚠️ [Unresolved] {relative_path:<54} | Measure {measure_num}")
                    
        except Exception:
            pass

    print("\n" + "=" * 105)
    print(f"SCAN COMPLETE. Total remaining unresolved errors: {total_anomalies_found}")
    print("=" * 105)

if __name__ == "__main__":
    run_global_diagnostic_report()
