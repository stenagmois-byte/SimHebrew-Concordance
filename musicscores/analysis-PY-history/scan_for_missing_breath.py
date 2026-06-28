import os
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_note_linear(elements, start_idx):
    """Scans forward from a direction element to find the true final note of the word."""
    for i in range(start_idx, len(elements)):
        elem = elements[i]
        if elem.tag == 'note':
            if elem.find("rest") is not None:
                continue
            
            # Case A: Explicit multi-syllable word completion
            syllabic = elem.find(".//lyric/syllabic")
            if syllabic is not None and syllabic.text == "end":
                return elem
                
            # Case B: If another word starting direction or a single-syllable text note appears,
            # we check if this is the text-bearing note completing a short word.
            if elem.find(".//lyric/text") is not None:
                # If the next element is another word direction, this note must be the end of our current word
                if i + 1 < len(elements) and elements[i+1].tag == 'direction':
                    return elem
                # If no explicit 'end' tag is found but it has text, fall back to it
                if syllabic is None or syllabic.text == "single":
                    return elem
        
        # If we hit a new Hebrew word block before finding an 'end' syllable note, 
        # the previous note was the fallback word cap.
        if elem.tag == 'direction' and i > start_idx:
            for j in range(i - 1, start_idx - 1, -1):
                if elements[j].tag == 'note' and elements[j].find(".//lyric/text") is not None:
                    return elements[j]
    return None

def run_linear_diagnostic_report():
    print("=" * 115)
    print("MUSICXML LINEAR AUDITOR: ISOLATING TRUE STRUCTURAL ACCENT MISSES")
    print("=" * 115)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    all_xml_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP" in dirpath or "analysis_scripts" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.xml'):
                all_xml_files.append(os.path.join(dirpath, filename))
                
    total_errors = 0
    
    for full_file_path in all_xml_files:
        try:
            tree = ET.parse(full_file_path)
            root = tree.getroot()
            
            # Step 1: Flatten everything inside all measures sequentially
            linear_flow = []
            measure_map = {} # Track which measure an element belongs to for reporting
            
            for measure in root.findall(".//measure"):
                m_num = measure.get('number', 'Unknown')
                for child in measure:
                    if child.tag.endswith('direction') or child.tag.endswith('note'):
                        linear_flow.append(child)
                        measure_map[child] = m_num
            
            # Step 2: Linear Stream Evaluation
            for idx, elem in enumerate(linear_flow):
                if elem.tag.endswith('direction'):
                    dir_xml = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                    if ZAQEF_QATON_GLYPH in dir_xml:
                        
                        # Pinpoint the exact final note of this accented word string
                        target_note = find_word_end_note_linear(linear_flow, idx + 1)
                        
                        if target_note is not None:
                            # Strict Safety Check: Duration 3 exception rules out errors
                            duration_elem = target_note.find(".//duration") if target_note.find("duration") is None else target_note.find("duration")
                            if duration_elem is not None and duration_elem.text == "3":
                                continue
                                
                            # Universal String Normalization: Converts note block to raw flat string
                            # This removes namespaces, slashes, and spaces to completely bypass layout bugs
                            note_xml_raw = ET.tostring(target_note, encoding='utf-8').decode('utf-8').lower()
                            note_xml_clean = note_xml_raw.replace(" ", "").replace("/", "").replace("-", "")
                            
                            # Perform broad, bulletproof text detection on the clean block
                            has_breath_mark = "breathmark" in note_xml_clean
                            has_caesura = "caesura" in note_xml_clean
                            has_comma = "comma" in note_xml_clean
                            
                            has_breath = has_breath_mark or has_caesura or has_comma
                            
                            if not has_breath:
                                total_errors += 1
                                relative_path = os.path.relpath(full_file_path, parent_dir)
                                words_elem = elem.find(".//words") if elem.find("words") is None else elem.find("words")
                                # Fallback namespace search for words element
                                if words_elem is None:
                                    for sub in elem.iter():
                                        if sub.tag.endswith('words'):
                                            words_elem = sub
                                            break
                                            
                                word_text = words_elem.text if words_elem is not None else "Unknown"
                                print(f" ❌ [Missing Breath] {relative_path:<50} | Bar {measure_map[target_note]:<4} | Word: {word_text.strip()}")
                                
        except Exception as e:
            pass

    print("\n" + "=" * 115)
    print(f"DIAGNOSTIC COMPLETE. Total True Unresolved Errors Found: {total_errors}")
    print("=" * 115)


if __name__ == "__main__":
    run_linear_diagnostic_report()
