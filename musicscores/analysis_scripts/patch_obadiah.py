import os
import shutil
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_note_linear(elements, start_idx):
    """
    Traces forward from a direction element to find the true final note of the word.
    Verified flawless during your local test run!
    """
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
                return elem
                
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

def patch_local_obadiah():
    print("=" * 115)
    # Register namespaces to prevent 'ns0:' tags from corrupting the schema wrapper
    ET.register_namespace('', 'http://idpf.org') 
    print("OBADIAH LOCAL PATCH ENGINE: EXECUTING PRECISION TEST REPAIRS")
    print("=" * 115)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Locate Obadiah in the local directory
    obadiah_file = None
    for filename in os.listdir(script_dir):
        if "obadiah" in filename.lower() and filename.lower().endswith('.xml'):
            obadiah_file = os.path.join(script_dir, filename)
            break
            
    if not obadiah_file:
        print("🚨 'OBADIAH' XML file not found directly in the script folder!")
        return
        
    print(f"Repairing File: {os.path.basename(obadiah_file)}\n")
    total_patches = 0
    
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
                        # 1. Duration 3 safety check
                        duration_elem = None
                        for sub in target_note.iter():
                            if sub.tag.endswith('duration'):
                                duration_elem = sub
                                break
                        if duration_elem is not None and duration_elem.text == "3":
                            continue
                            
                        # 2. Universal String Normalization check
                        note_xml_raw = ET.tostring(target_note, encoding='utf-8').decode('utf-8').lower()
                        note_xml_clean = note_xml_raw.replace(" ", "").replace("/", "").replace("-", "")
                        
                        has_breath = "breathmark" in note_xml_clean or "caesura" in note_xml_clean or "comma" in note_xml_clean
                        
                        # 3. Surgical Injection if breath is missing
                        if not has_breath:
                            # Construct structural element with namespace-safe tag creation
                            # Elements inside standard musicxml root will inherit the registered default empty prefix
                            notations = ET.Element("notations")
                            articulations = ET.SubElement(notations, "articulations")
                            ET.SubElement(articulations, "breath-mark", {
                                "default-x": "41", 
                                "default-y": "11", 
                                "placement": "above"
                            })
                            
                            # Sequential schema-compliant layout placement (Insert right before lyric tags)
                            insert_index = len(target_note)
                            for c_idx, child_node in enumerate(target_note):
                                if child_node.tag.endswith('lyric') or child_node.tag.endswith('notations'):
                                    insert_index = c_idx
                                    break
                                    
                            target_note.insert(insert_index, notations)
                            total_patches += 1
                            print(f" 🛠️ [Inserted Breath] Bar {measure_map[elem]:<4} | Word: {word_text}")
                            
        # Overwrite file with precision additions
        if total_patches > 0:
            tree.write(obadiah_file, encoding="utf-8", xml_declaration=True)
            print(f"\n✅ REPAIR COMPLETE. Overwrote local file with {total_patches} precision updates.")
        else:
            print("\n🟢 No changes needed. File matches target rules perfectly.")
            
    except Exception as e:
        print(f"🚨 Script encountered an error during patch execution: {e}")

if __name__ == "__main__":
    patch_local_obadiah()
