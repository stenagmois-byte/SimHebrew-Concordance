import os
import xml.etree.ElementTree as ET

# Unicode glyph for 1428 (Zaqef-Qaton)
ZAQEF_QATON_GLYPH = "\u0594"

def run_global_clean_diagnostic():
    print("=" * 105)
    print("MUSICXML COMPILER: ISOLATING GENUINE BUGS (SILENT FOR CLEAN MEASURES)")
    print("=" * 105)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    # Pre-gather all XML files on the drive
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
            
            # Evaluate every measure strictly as an isolated unit
            for measure in root.findall(".//measure"):
                measure_xml = ET.tostring(measure, encoding='utf-8').decode('utf-8')
                
                # Check 1: Does this specific bar contain the Zaqef-Qaton accent?
                if ZAQEF_QATON_GLYPH in measure_xml:
                    
                    # Check 2: Does a breath mark or comma notation exist inside this same bar?
                    measure_xml_lower = measure_xml.lower()
                    has_breath = "breath" in measure_xml_lower or "comma" in measure_xml_lower
                    
                    # TRUE BUG INTERSECTION: Accent is active but a breath mark is completely missing
                    if not has_breath:
                        total_anomalies_found += 1
                        file_had_anomaly = True
                        relative_book_path = os.path.relpath(full_file_path, parent_dir)
                        measure_num = measure.get('number', 'Unknown')
                        
                        # Only print when an actual error is triggered
                        print(f" {relative_book_path:<65} | Measure: {measure_num}")
            
            if not file_had_anomaly:
                clean_files_count += 1
                
        except Exception:
            pass # Gracefully bypass locked files

    print("\n" + "=" * 105)
    print(f"COMPILATION COMPLETE. Scanned {len(all_xml_files)} files.")
    print(f"Files completely without error: {clean_files_count}")
    print(f"Total isolated anomalies: {total_anomalies_found}")
    print("=" * 105)

if __name__ == "__main__":
    run_global_clean_diagnostic()
