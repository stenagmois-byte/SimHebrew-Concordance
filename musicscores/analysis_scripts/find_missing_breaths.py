import os
import xml.etree.ElementTree as ET

# Unicode glyph for 1428 (Zaqef-Qaton)
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
    
    # 1. Anchor Condition: If it doesn't have the accent, it's not our target
    if ZAQEF_QATON_GLYPH not in measure_xml:
        return False
        
    # 2. Strict Filter Scan across all individual notes in this measure
    notes_in_measure = measure_element.findall(".//note")
    
    for note in notes_in_measure:
        # Check for duration values
        duration_elem = note.find("duration")
        if duration_elem is not None and duration_elem.text == "3":
            return False  # Rule: If duration is 3, there is NEVER an error. Skip!
            
        # Check for a physical breath mark anywhere in this note block
        note_xml_lower = ET.tostring(note, encoding='utf-8').decode('utf-8').lower()
        if "breath" in note_xml_lower or "comma" in note_xml_lower:
            return False  # Rule: If there is a breath mark, there is NO error. Skip!

    # If it has Zaqef-Qaton, but completely failed both safety checks, it's a true error
    return True

def run_global_clean_diagnostic():
    print("=" * 105)
    print("MUSICXML COMPILER: ISOLATING GENUINE ERRORS ONLY (STRICT EXCLUSION WALLED)")
    print("=" * 105)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Pre-gather all XML files on the local drive
    all_xml_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                all_xml_files.append(os.path.join(dirpath, filename))
                
    print(f"Scanning {len(all_xml_files)} files. Displaying errors ONLY...\n")
    print(f"{'FILE PATH LOCATION':<65} | {'MEASURE NUMBER'}")
    print("-" * 105)
    
    total_anomalies_found = 0
    clean_files_count = 0
    
    for full_file_path in all_xml_files:
        try:
            tree = ET.parse(full_file_path)
            root = tree.getroot()
            
            file_had_anomaly = False
            
            for measure in root.findall(".//measure"):
                measure_num = measure.get('number', 'Unknown')
                
                # Execute the strict error validation check
                if scan_measure_for_true_error(measure):
                    total_anomalies_found += 1
                    file_had_anomaly = True
                    relative_book_path = os.path.relpath(full_file_path, parent_dir)
                    
                    # Output ONLY the file path and the explicit measure coordinate
                    print(f" {relative_book_path:<65} | Measure {measure_num}")
            
            if not file_had_anomaly:
                clean_files_count += 1
                
        except Exception:
            pass # Gracefully bypass locked files

    print("\n" + "=" * 105)
    print(f"COMPILATION COMPLETE. Scanned {len(all_xml_files)} files.")
    print(f"Files completely without error: {clean_files_count}")
    print(f"Total genuine errors isolated across the corpus: {total_anomalies_found}")
    print("=" * 105)

if __name__ == "__main__":
    run_global_clean_diagnostic()
