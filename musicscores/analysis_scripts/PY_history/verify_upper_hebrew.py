import os
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
MUSIC_SCORES_BASE = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores")

def get_active_book_folder():
    if not INPUT_DIR.exists(): return None
    epubs = list(INPUT_DIR.glob("*.epub"))
    if not epubs: return None
    epub_stem = epubs[0].stem
    match = epub_stem.split(" - ")[0].strip() if " - " in epub_stem else epub_stem.strip()
    if MUSIC_SCORES_BASE.exists():
        for item in MUSIC_SCORES_BASE.iterdir():
            if item.is_dir() and match.lower() in item.name.lower():
                return item.name
    return match

def scan_caesura_collisions(mscz_path, display_path):
    filename = os.path.basename(mscz_path)
    try:
        with zipfile.ZipFile(mscz_path, 'r') as archive:
            mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            if not mscx_files: return
            with archive.open(mscx_files[0]) as file_stream:
                mscx_content = file_stream.read().decode('utf-8', errors='ignore')
        
        root = ET.fromstring(mscx_content)
        measures = root.findall(".//Measure") or [el for el in root.iter() if el.tag.lower() == 'measure']
        
        print(f"\n💨 Scanning Caesura Alignment Lifts: {display_path}")
        print("-" * 80)
        
        collision_count = 0
        
        for m_idx, measure in enumerate(measures, start=1):
            # Find the sequential children inside the voice block
            voice = measure.find(".//voice")
            if voice is None:
                continue
                
            # Iterate through the elements exactly in the order they appear on the timeline
            elements = list(voice)
            for idx, elem in enumerate(elements):
                if elem.tag == "Breath":
                    symbol = elem.find("symbol")
                    if symbol is not None and symbol.text == "caesura":
                        
                        # Peek ahead to see if the next element is a StaffText block
                        if idx + 1 < len(elements) and elements[idx + 1].tag == "StaffText":
                            text_node = elements[idx + 1]
                            text_val = "".join(text_node.itertext()).strip()
                            
                            # Check if you already manually fixed it (turned off autoplace or adjusted y)
                            no_auto_place = text_node.find("noAutoPlace")
                            pos_y = text_node.find(".//pos/y") or text_node.find("pos/y")
                            
                            is_fixed = (no_auto_place is not None and no_auto_place.text == "1") or (pos_y is not None)
                            
                            if not is_fixed:
                                collision_count += 1
                                print(f"  ❌ HIDDEN LIFT FOUND: Measure {m_idx:<3} | Word follows a Caesura directly!")
                                print(f"     Affected Word: \"{text_val}\"")
                                
        if collision_count == 0:
            print("  ✅ All Caesuras Clear: No un-remedied text lifts detected.")
            
    except Exception as e:
        print(f"💥 Error scanning: {e}")

def main():
    clean_book_folder = get_active_book_folder()
    if not clean_book_folder: return
    target_volume_dir = MUSIC_SCORES_BASE / clean_book_folder
    
    mscz_files = sorted(list(target_volume_dir.glob("*.mscz")) + list(target_volume_dir.glob("*.MSCZ")))
    for file_path in mscz_files:
        relative_display = os.path.relpath(file_path, MUSIC_SCORES_BASE)
        scan_caesura_collisions(file_path, relative_display)

if __name__ == "__main__":
    main()
