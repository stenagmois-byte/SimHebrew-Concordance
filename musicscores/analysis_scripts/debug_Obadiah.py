import os
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_note_linear(elements, start_idx):
    """Traces forward to find what note Python thinks ends the word."""
    for i in range(start_idx, len(elements)):
        elem = elements[i]
        if elem.tag.endswith('note'):
            if elem.find(".//rest") is not None:
                continue
            
            syllabic = None
            for sub in elem.iter():
                if sub.tag.endswith('syllabic'):
                    syllabic = sub
                    break
            
            if syllabic is not None and syllabic.text == "end":
                return elem, f"Locked on explicitly marked <syllabic>end</syllabic> node (Index {i})"
            
            text_elem = None
            for sub in elem.iter():
                if sub.tag.endswith('text'):
                    text_elem = sub
                    break
                        
            if text_elem is not None:
                if i + 1 < len(elements) and elements[i+1].tag.endswith('direction'):
                    return elem, f"Locked on text note followed by a new direction (Index {i})"
                if syllabic is None or syllabic.text == "single":
                    return elem, f"Locked on standalone single-syllable note (Index {i})"
                    
        if elem.tag.endswith('direction') and i > start_idx:
            for j in range(i - 1, start_idx - 1, -1):
                if elements[j].tag.endswith('note'):
                    text_sub = None
                    for sub in elements[j].iter():
                        if sub.tag.endswith('text'):
                            text_sub = sub
                            break
                    if text_sub is not None:
                        return elements[j], f"Fallback: Locked on last text note before next direction (Index {j})"
    return None, "No target note found"

def trace_local_obadiah():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, "Obadiah.xml")
    
    print("=" * 115)
    print(f"DEBUGGER ENGINE: LOCAL FLOW TRACE FOR -> {os.path.basename(full_path)}")
    print("=" * 115)
    
    if not os.path.exists(full_path):
        print(f"🚨 File not found in the script's local folder! Checked path:\n -> {full_path}")
        print("Please verify the filename matches 'Obadiah.xml' exactly (case-sensitive).")
        return
        
    try:
        tree = ET.parse(full_path)
        root = tree.getroot()
        
        linear_flow = []
        measure_map = {}
        
        for measure in root.findall(".//measure"):
            m_num = measure.get('number', 'Unknown')
            for child in measure:
                if child.tag.endswith('direction') or child.tag.endswith('note'):
                    linear_flow.append(child)
                    measure_map[child] = m_num
                    
        found_any = False
        for idx, elem in enumerate(linear_flow):
            if elem.tag.endswith('direction'):
                dir_xml = ET.tostring(elem, encoding='utf-8').decode('utf-8')
                if ZAQEF_QATON_GLYPH in dir_xml:
                    found_any = True
                    words_elem = None
                    for sub in elem.iter():
                        if sub.tag.endswith('words'):
                            words_elem = sub
                            break
                    word_text = words_elem.text.strip() if words_elem is not None else "Unknown"
                    current_bar = measure_map[elem]
                    
                    print(f"🔍 Found Zaqef-Qaton at Bar {current_bar} on word: '{word_text}'")
                    
                    # Run tracking routine
                    target_note, log_reason = find_word_end_note_linear(linear_flow, idx + 1)
                    print(f"   └── Tracking Result: {log_reason}")
                    
                    if target_note is not None:
                        target_bar = measure_map[target_note]
                        note_xml = ET.tostring(target_note, encoding='utf-8').decode('utf-8')
                        
                        lyrics = [t.text for t in target_note.iter() if t.tag.endswith('text')]
                        print(f"   └── Target Note Bar: {target_bar}")
                        print(f"   └── Target Note Syllable Text: {lyrics}")
                        
                        note_xml_clean = note_xml.lower().replace(" ", "").replace("/", "").replace("-", "")
                        has_breath = "breathmark" in note_xml_clean or "caesura" in note_xml_clean or "comma" in note_xml_clean
                        print(f"   └── Python detects breath-mark? {'YES (Perfect)' if has_breath else 'NO (Flagged as Error!)'}")
                    print("-" * 115)
                    
        if not found_any:
            print("⚠️ Scanned the local file, but did not find any instances of the Zaqef-Qaton glyph character.")
            
    except Exception as e:
        print(f"🚨 Crash during execution: {e}")

if __name__ == "__main__":
    trace_local_obadiah()
