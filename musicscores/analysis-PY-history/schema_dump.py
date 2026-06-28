import os
import zipfile
import xml.etree.ElementTree as ET

def structural_footprint_scan():
    # 1. Target GENESIS-001.mscz sitting up one level in the parent workspace directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_workspace = os.path.dirname(script_dir) # Drops down to \musicscores
    
    # We will search the parent directory recursively to find where GENESIS-001 sits
    target_file_path = None
    for root, dirs, files in os.walk(parent_workspace):
        if "GENESIS-001.mscz" in files:
            target_file_path = os.path.join(root, "GENESIS-001.mscz")
            break
            
    print("=" * 100)
    print("MUSE SCORE 4 DEEP SCHEMA SCAN")
    print("=" * 100)
    
    if not target_file_path:
        print(f"🚨 Error: Could not locate 'GENESIS-001.mscz' anywhere inside:\n -> {parent_workspace}")
        return
        
    print(f"Targeting score file: {target_file_path}\n")
    
    try:
        # 2. Extract and unzip internal XML data string
        with zipfile.ZipFile(target_file_path, 'r') as archive:
            mscx_targets = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            if not mscx_targets:
                print("🚨 Error: No internal .mscx XML file found in this archive container.")
                return
            with archive.open(mscx_targets[0]) as file_stream:
                xml_string = file_stream.read()
                
        root = ET.fromstring(xml_string)
        
        print(f"{'BAR':<6} | {'TAG ARCHITECTURE':<25} | {'TEXT / MIDI VALUE DETECTED'}")
        print("-" * 100)
        
        current_bar = "0"
        element_counter = 0
        
        # 3. Stream all node components sequentially to map names and attributes
        for elem in root.iter():
            tag_clean = elem.tag.split('}')[-1] # Drop messy namespaces
            
            if tag_clean.lower() == 'measure':
                current_bar = elem.get('number', current_bar)
                
            # Print a precise cross-section of note elements and textual variations
            if tag_clean in ['pitch', 'text', 'StaffText', 'Lyrics', 'Breath', 'name', 'Symbol']:
                element_counter += 1
                
                # Format output values based on what the tag carries
                display_value = elem.text.strip() if elem.text and elem.text.strip() else "[Empty Node / Envelope Container]"
                
                # Highlight if it's your agogic mark
                if tag_clean == 'Breath':
                    display_value = "🚩 [FOUND AGOGIC BREATH CONTAINER]"
                
                print(f"{current_bar:<6} | <{tag_clean}>" + " " * (23 - len(tag_clean)) + f" | {display_value}")
                
                # Stop after 45 explicit markers so we don't spam the console window
                if element_counter >= 45:
                    break
                    
        print("-" * 100)
        print("💡 INSIGHT: Look closely at the exact spelling/casing of the tags above.")
        print("We will use this exact structural printout to rebuild our main concordance matcher.")
        print("=" * 100)
        
    except Exception as e:
        print(f"🚨 Scan Interrupted: {str(e)}")

if __name__ == "__main__":
    structural_footprint_scan()
