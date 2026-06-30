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
