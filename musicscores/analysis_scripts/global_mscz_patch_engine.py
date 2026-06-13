import os
import shutil
import zipfile
import xml.etree.ElementTree as ET

ZAQEF_QATON_GLYPH = "\u0594"

def find_word_end_chord_linear(elements, start_idx):
    """
    Traces forward from a StaffText element to find the true final Chord of the word.
    Handles MuseScore 4 .mscx linear hierarchies.
    """
    last_seen_chord = None
    
    for i in range(start_idx, len(elements)):
        elem = elements[i]
        
        if elem.tag == 'Chord':
            last_seen_chord = elem
            
            # Explicit multi-syllable lyric word completion
            syllabic = elem.find(".//Lyrics/syllabic")
            if syllabic is not None and syllabic.text == "end":
                return elem
                
            # Fallback Check: Standalone single-syllable notes
            text_elem = elem.find(".//Lyrics/text")
            if text_elem is not None:
                if i + 1 < len(elements) and elements[i+1].tag == 'StaffText':
                    return elem
                if syllabic is None or syllabic.text == "single":
                    return elem
                    
        if elem.tag == 'StaffText' and i > start_idx:
            if last_seen_chord is not None:
                return last_seen_chord
                
    return last_seen_chord

def patch_mscx_content(mscx_text):
    """Parses and updates the internal XML structure, returning modified text."""
    root = ET.fromstring(mscx_text)
    
    linear_flow = []
    parent_map = {}
    
    for parent in root.iter():
        for child in parent:
            if child.tag in ['StaffText', 'Chord', 'Breath']:
                linear_flow.append(child)
                parent_map[child] = parent
                
    total_patches = 0
    
    for idx, elem in enumerate(linear_flow):
        if elem.tag == 'StaffText':
            text_node = elem.find("text")
            if text_node is not None and text_node.text and ZAQEF_QATON_GLYPH in text_node.text:
                
                # Trace forward to target the closing note chord of this word
                target_chord = find_word_end_chord_linear(linear_flow, idx + 1)
                
                if target_chord is not None:
                    # SAFETY CHECK 1: Skip if the note is an eighth note
                    # MuseScore uses string type tags rather than raw MusicXML numeric duration values
                    duration_type = target_chord.find("durationType")
                    if duration_type is not None and duration_type.text == "eighth":
                        continue  # Rule: Eighth notes already have valid pauses. Skip!
                    
                    # SAFETY CHECK 2: Look ahead to ensure a Breath element doesn't already exist
                    parent_voice = parent_map[target_chord]
                    voice_elements = list(parent_voice)
                    target_chord_index = voice_elements.index(target_chord)
                    
                    already_has_breath = False
                    
                    # Check local sibling right after the chord in the parent block
                    if target_chord_index + 1 < len(voice_elements):
                        next_sibling = voice_elements[target_chord_index + 1]
                        if next_sibling.tag == 'Breath':
                            already_has_breath = True
                            
                    # Check the global linear stream list as a safety fallback
                    chord_idx_in_flow = linear_flow.index(target_chord)
                    if chord_idx_in_flow + 1 < len(linear_flow):
                        if linear_flow[chord_idx_in_flow + 1].tag == 'Breath':
                            already_has_breath = True
                            
                    # Only inject if all safety rules pass and the space is empty
                    if not already_has_breath:
                        # Construct the MuseScore 4 compatible Breath element
                        breath_elem = ET.Element("Breath")
                        symbol_sub = ET.SubElement(breath_elem, "symbol")
                        symbol_sub.text = "breathMarkComma"
                        
                        # Surgically inject it directly after the target chord inside the timeline
                        parent_voice.insert(target_chord_index + 1, breath_elem)
                        total_patches += 1
                        
    if total_patches > 0:
        return ET.tostring(root, encoding='utf-8').decode('utf-8'), total_patches
    return None, 0

def run_global_mscz_patch_engine():
    print("=" * 115)
    print("MSCZ PRODUCTION PATCH ENGINE: CALIBRATED FOR EIGHTH-NOTE FILTERING")
    print("=" * 115)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    backup_dir = os.path.join(parent_dir, "_PRE_PATCH_BACKUP_MSCZ")
    
    mscz_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP_MSCZ" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.mscz'):
                mscz_files.append(os.path.join(dirpath, filename))
                
    print(f"Isolated {len(mscz_files)} native MuseScore files for automated patching.\n")
    
    modified_files_count = 0
    global_injections_count = 0
    
    for full_file_path in mscz_files:
        try:
            mscx_filename = None
            mscx_content = None
            
            with zipfile.ZipFile(full_file_path, 'r') as archive:
                mscx_targets = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
                if mscx_targets:
                    mscx_filename = mscx_targets[0]
                    with archive.open(mscx_filename) as file_stream:
                        mscx_content = file_stream.read().decode('utf-8', errors='ignore')
                        
            if mscx_content is not None:
                modified_xml, patch_count = patch_mscx_content(mscx_content)
                
                if modified_xml is not None:
                    modified_files_count += 1
                    global_injections_count += patch_count
                    relative_path = os.path.relpath(full_file_path, parent_dir)
                    
                    # Create backup copy
                    backup_file_path = os.path.join(backup_dir, relative_path)
                    os.makedirs(os.path.dirname(backup_file_path), exist_ok=True)
                    shutil.copy2(full_file_path, backup_file_path)
                    
                    # Re-package clean ZIP container
                    temp_zip_path = full_file_path + ".tmp"
                    with zipfile.ZipFile(full_file_path, 'r') as source_zip:
                        with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as target_zip:
                            for item in source_zip.infolist():
                                if item.filename == mscx_filename:
                                    target_zip.writestr(mscx_filename, modified_xml)
                                else:
                                    target_zip.writestr(item, source_zip.read(item.filename))
                                    
                    os.remove(full_file_path)
                    os.rename(temp_zip_path, full_file_path)
                    print(f" 🛠️ [MSCZ Patched] {relative_path} -> Injected {patch_count} commas")
                    
        except Exception as e:
            print(f" 🚨 Failed processing {os.path.basename(full_file_path)}: {e}")
            if os.path.exists(full_file_path + ".tmp"):
                os.remove(full_file_path + ".tmp")

    print("\n" + "=" * 115)
    print("MSCZ COMPILATION CYCLE COMPLETE.")
    print(f" Total native MuseScore files updated: {modified_files_count}")
    print(f" Total automated comma injections:     {global_injections_count}")
    print("=" * 115)

if __name__ == "__main__":
    run_global_mscz_patch_engine()
