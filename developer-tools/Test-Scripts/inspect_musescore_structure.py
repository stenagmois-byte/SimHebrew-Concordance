import sys
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

def inspect_musescore_structure():
    print("Initiating MuseScore 4 Structural Inspector Engine...")
    
    # 🔍 Locate your reference file across your current directories
    target_filename = "2_voices_GENESIS-001.mscz"
    mscz_path = None
    
    for path in Path(".").glob(f"**/{target_filename}"):
        mscz_path = path
        break
        
    if not mscz_path or not mscz_path.exists():
        print(f"❌ Error: Cannot locate '{target_filename}' anywhere in your workspace.")
        print("   Make sure the file is dropped inside your musicscores/Genesis folder or the root directory.")
        return

    print(f"✅ Found target file asset at: {mscz_path.resolve()}\n")

    try:
        # 1. Open the .mscz zip container directly in memory without writing files to disk
        with zipfile.ZipFile(mscz_path, 'r') as zip_ref:
            # Find the uncompressed internal .mscx layout descriptor file
            mscx_files = [f for f in zip_ref.namelist() if f.endswith(".mscx")]
            if not mscx_files:
                print("❌ Error: Core .mscx score definition element missing inside this container.")
                return
                
            mscx_filename = mscx_files[0]
            print(f"--- Found Internal Layout File: {mscx_filename} ---")
            
            # Read the raw text data straight out of the zipped file stream
            with zip_ref.open(mscx_filename) as mscx_file:
                raw_xml_data = mscx_file.read()
                
        # 2. Parse the underlying tree data
        root = ET.fromstring(raw_xml_data)
        
        # Print out the root tag metadata attributes
        print(f"Root Element Tag: <{root.tag}> | Version Attribute: {root.attrib.get('version', 'Unknown')}")
        print("=" * 60)

        # 3. 🎯 EXTRACT STRUCTURAL PART DEFINITIONS (The Mixer Channels)
        print("\n[PART & INSTRUMENT DEFINITIONS]")
        parts = root.findall(".//Part")
        if not parts:
            # If MuseScore 4 wraps it inside a different high-level branch, check globally
            parts = root.findall("Score/Part") or root.findall(".//part")
            
        print(f"Total <Part> tracks registered on the score sheet: {len(parts)}")
        
        for idx, part in enumerate(parts, 1):
            print(f"\n--- Part Track {idx} ---")
            # Print out the element properties inside MuseScore's internal structure
            for child in part:
                if child.tag in ["Staff", "Instrument", "trackName", "longName", "shortName"]:
                    if child.tag == "Instrument":
                        print(f"  <{child.tag} id=\"{child.attrib.get('id', '')}\">")
                        for inst_child in child:
                            if inst_child.tag in ["longName", "shortName", "trackName", "Channel"]:
                                print(f"    <{inst_child.tag}>: {inst_child.text or ''}")
                    else:
                        print(f"  <{child.tag}>: {child.text or child.attrib}")

        # 4. 🎯 EXTRACT MEASURE AND NOTE ARCHITECTURE (Syllable Track Mechanics)
        print("\n" + "=" * 60)
        print("[MEASURE 1 DATA TRACK LAYOUT]")
        
        # Grab the first measure inside the file to analyze note/voice structures
        first_measure = root.find(".//measure")
        if first_measure is not None:
            print(f"Found Measure Number: {first_measure.attrib.get('number', '1')}")
            
            # Print out the raw XML layout blocks of the first measure so we can see how voices are stored
            # (Limiting output length so it doesn't flood your screen terminal window)
            measure_string = ET.tostring(first_measure, encoding="utf-8").decode("utf-8")
            print(measure_string[:1500])
            if len(measure_string) > 1500:
                print("\n   [... Text truncated for display cleanliness ...] ")
        else:
            print("⚠️ No <measure> tags found inside the structural file tree layout.")

    except Exception as e:
        print(f"❌ Structural analysis failure: {e}")

if __name__ == "__main__":
    inspect_musescore_structure()
