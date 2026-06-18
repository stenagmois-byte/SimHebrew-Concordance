import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# Path directly to your active Deuteronomy file
MSC_DIR = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores\Deuteronomy")

def dump_target_measure():
    mscz_files = list(MSC_DIR.glob("*.mscz"))
    if not mscz_files:
        print(f"❌ No .mscz files found inside {MSC_DIR}")
        return
        
    target_file = sorted(mscz_files)[0] # Grab the first file (usually Chapter 1)
    print(f"Inspecting file: {target_file.name}\n")
    
    with zipfile.ZipFile(target_file, 'r') as archive:
        mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
        with archive.open(mscx_files[0]) as file_stream:
            mscx_content = file_stream.read().decode('utf-8', errors='ignore')
            
    root = ET.fromstring(mscx_content)
    measures = root.findall(".//Measure")
    
    # Target Measure 13 (index 12 in zero-based arrays)
    if len(measures) >= 13:
        m13 = measures[12]
        print("=" * 80)
        print("RAW XML ELEMENT TREE FOR MEASURE 13:")
        print("=" * 80)
        
        # Helper function to recursively print elements and nested children
        def recurse_elements(element, depth=0):
            indent = "  " * depth
            text_val = f" -> text: {element.text.strip()}" if element.text and element.text.strip() else ""
            print(f"{indent}<{element.tag}>{text_val}")
            for child in element:
                recurse_elements(child, depth + 1)
                
        recurse_elements(m13)
        print("=" * 80)
    else:
        print(f"⚠️ Score only contains {len(measures)} measures. Cannot find Measure 13.")

if __name__ == "__main__":
    dump_target_measure()
