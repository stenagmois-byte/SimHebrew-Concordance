import os
import zipfile
import xml.etree.ElementTree as ET

def trace_mscz_structure(mscz_filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mscz_path = os.path.join(script_dir, mscz_filename)
    
    print("=" * 115)
    print(f"MUSE SCORE ZIP EXTRACTOR: ANALYZING STRUCTURAL INTERNALS FOR {mscz_filename}")
    print("=" * 115)
    
    if not os.path.exists(mscz_path):
        print(f"🚨 File not found in local script folder! Checked path:\n -> {mscz_path}")
        return
        
    try:
        # Step 1: Open the compressed MuseScore zip container
        with zipfile.ZipFile(mscz_path, 'r') as archive:
            # Locate the uncompressed plain-text XML (.mscx) file hidden inside
            mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            
            if not mscx_files:
                print("🚨 No uncompressed .mscx XML file found inside this MSCZ package!")
                return
                
            mscx_internal_name = mscx_files[0]
            print(f" Found compressed internal XML target: '{mscx_internal_name}'")
            
            # Step 2: Read the XML layout text directly out of memory
            with archive.open(mscx_internal_name) as file_stream:
                mscx_content = file_stream.read().decode('utf-8', errors='ignore')
                
        # Step 3: Parse a safe sample frame using ElementTree to look at the node tags
        root = ET.fromstring(mscx_content)
        
        print("\n--- DETECTED XML WRAPPER METADATA ---")
        print(f"Root XML Tag Type: {root.tag}")
        if 'version' in root.attrib:
            print(f"MuseScore Version File Attribute: {root.attrib['version']}")
            
        print("\n--- RECONNOITERING PRIMARY ELEMENT FLOW (SAMPLE SLICE) ---")
        
        # We search broadly for common MuseScore layout tags to see how they are written
        sample_limit = 15
        count = 0
        
        # Walk through all nodes to show a structural map of StaffText, Lyrics, and Chords
        for elem in root.iter():
            tag_clean = elem.tag.split('}')[-1] # Clean out any potential namespaces
            
            if tag_clean in ['StaffText', 'SystemText', 'Chord', 'Note', 'Lyrics', 'text', 'syllabic']:
                count += 1
                indent = "  "
                if tag_clean in ['text', 'syllabic']:
                    indent = "    "
                    print(f"{indent}├── <{tag_clean}> = {elem.text}")
                else:
                    text_preview = f" (Text: {elem.text.strip()})" if elem.text and elem.text.strip() else ""
                    print(f"{indent}└── <{tag_clean}>{text_preview}")
                    
            if count >= sample_limit:
                break
                
        print("\n" + "-" * 115)
        print("💡 INSIGHT: Paste a snippet of the raw .mscx XML text below where your Hebrew words appear,")
        print("and we can map the exact linear loop to patch your native MuseScore files automatically.")
        print("=" * 115)
        
    except Exception as e:
        print(f"🚨 Extraction loop failed: {e}")

if __name__ == "__main__":
    # Put a native MuseScore compressed archive into this folder and type its filename here:
    TARGET_MSCZ = "OBADIAH-001.mscz" 
    trace_mscz_structure(TARGET_MSCZ)
