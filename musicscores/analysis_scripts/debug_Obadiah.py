import os
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_note_linear(elements, start_idx):
    """
    Scans forward from a direction element to find the true final note of the word.
    We will observe how this behaves on Obadiah.
    """
    for i in range(start_idx, len(elements)):
        elem = elements[i]
        if elem.tag.endswith('note'):
            if elem.find(".//rest") is not None:
                continue
            
            # Case A: Explicit multi-syllable word completion
            syllabic = None
            for sub in elem.iter():
                if sub.tag.endswith('syllabic'):
                    syllabic = sub
                    break
            if syllabic is not None and syllabic.text == "end":
                return elem
                
            # Case B: Standard text-bearing note
            text_elem = None
            for sub in elem.iter():
                if sub.tag.endswith('text'):
                    text_elem = sub
                    break
            if text_elem is not None:
                if i + 1 < len(elements) and elements[i+1].tag.endswith('direction'):
                    return elem
                if syllabic is None or (syllabic is not None and syllabic.text == "single"):
                    return elem
        
        # Guard rail: If we hit a new direction block before finding a valid note match,
        # fallback to scanning backwards for the last lyric text node.
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

def test_obadiah_only():
    print("=" * 115)
    print("OBADIAH TARGET TEST ENGINE: AUDITING PRISTINE SCAN")
    print("=" * 115)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dynamically find the file named 'obadiah' in full capital letters or mixed case right in this folder
    obadiah_file = None
    for filename in os.listdir(script_dir):
        if "obadiah" in filename.lower() and filename.lower().endswith('.xml'):
            obadiah_file = os.path.join(script_dir, filename)
            break
            
    if not obadiah_file:
        print("🚨 'OBADIAH' XML file not found directly in the script folder!")
        print("Please place your Obadiah XML file right next to this script and run it again.")
        return
        
    print(f"Analyzing File: {os.path.basename(obadiah_file)}\n")
    total_errors = 0
    
    try:
        tree = ET.parse(obadiah_file)
        root = tree.getroot()
        
        linear_flow = []
        measure_map = {}
        
        for measure in root.findall(".//measure"):
            m_num = measure.get('number', 'Unknown')
            for child in measure:
                if child.tag.endswith('direction') or child.tag.endswith('note'):
                    linear_flow.append(child)
                    measure_map[child] = m_num
        
        for idx, elem in enumerate(linear_flow):
            if elem.tag.endswith('direction'):
                dir_xml = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                if ZAQEF_QATON_GLYPH in dir_xml:
                    
                    target_note = find_word_end_note_linear(linear_flow, idx + 1)
                    
                    words_elem = None
                    for sub in elem.iter():
                        if sub.tag.endswith('words'):
                            words_elem = sub
                            break
                    word_text = words_elem.text.strip() if words_elem is not None else "Unknown"
                    
                    if target_note is not None:
                        # Safety checks
                        duration_elem = target_note.find(".//duration")
                        if duration_elem is None:
                            for sub in target_note.iter():
                                if sub.tag.endswith('duration'):
                                    duration_elem = sub
                                    break
                        if duration_elem is not None and duration_elem.text == "3":
                            print(f" 🟢 [Skipped - Dur 3] Bar {measure_map[elem]:<4} | Word: {word_text}")
                            continue
                            
                        note_xml_raw = ET.tostring(target_note, encoding='utf-8').decode('utf-8').lower()
                        note_xml_clean = note_xml_raw.replace(" ", "").replace("/", "").replace("-", "")
                        
                        has_breath = "breathmark" in note_xml_clean or "caesura" in note_xml_clean or "comma" in note_xml_clean
                        
                        lyrics = [t.text for t in target_note.iter() if t.tag.endswith('text')]
                        
                        if not has_breath:
                            total_errors += 1
                            print(f" ❌ [Missing Breath] Bar {measure_map[elem]:<4} | Word: {word_text:<12} | Target Note Syllable: {lyrics}")
                        else:
                            print(f" ✅ [Valid Breath]   Bar {measure_map[elem]:<4} | Word: {word_text:<12} | Target Note Syllable: {lyrics}")
                    else:
                        print(f" ⚠️ [No Note Found]  Bar {measure_map[elem]:<4} | Word: {word_text}")
                        
    except Exception as e:
        print(f"🚨 Script encountered an execution error: {e}")

    print("\n" + "=" * 115)
    print(f"TEST COMPLETE. Total Errors Flagged in Obadiah: {total_errors}")
    print("=" * 115)

if __name__ == "__main__":
    test_obadiah_only()
