import os
import re
import json
import time
import zipfile
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

# --- Configuration Paths ---
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore4.exe"
REPO_ROOT = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance")
SCORE_DIR = REPO_ROOT / "musicscores"
AUDIO_DIR = SCORE_DIR / "audio"

PAUSE_TIMES = {
    "atnah": "1.5",
    "zaqef_qatan": "1.0"
}

def run_global_book_based_audio_compiler():
    print("🚀 Launching Production-Ready Book-Based Global Verse Compiler...")
    if not os.path.exists(MUSESCORE_PATH):
        print(f"❌ Error: MuseScore executable missing at {MUSESCORE_PATH}")
        return

    MAP_PATH = SCORE_DIR.parent / "book_map.json"
    if not MAP_PATH.exists():
        print(f"❌ Error: Central layout map missing at {MAP_PATH}")
        return

    with open(MAP_PATH, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    processed_verses_count = 0
    
    # Identify active source volumes (ignoring the audio output folder)
    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir() and d.name.upper() != "AUDIO"]
    mapped_folders = set(book_map.values())

    for folder_name in sorted(mapped_folders):
        matched_folder = next((d for d in subdirs if d.name.lower() == folder_name.lower()), None)
        if not matched_folder:
            continue

        print(f"\n📂 Scanning Source Volume: [{matched_folder.name}]")

        for f_path in matched_folder.iterdir():
            if not f_path.is_file() or f_path.suffix.lower() != ".mscz":
                continue
            if f_path.name.startswith("temp_"):
                continue

            # Accept both hyphen and underscore chapter naming schemes
            match = re.match(r"^([0-9a-zA-Z_-]+)-(\d{3})", f_path.name.lower())
            if not match:
                match = re.match(r"^([0-9a-zA-Z_-]+)_(\d{3})", f_path.name.lower())
            if not match:
                continue
                
            raw_prefix = match.group(1).replace("-", "_")
            book_prefix = raw_prefix.upper() 
            chapter_num = int(match.group(2))

            expected_folder = book_map.get(book_prefix)
            if not expected_folder or expected_folder.lower() != matched_folder.name.lower():
                continue

            # 🎯 BOOK-BASED DIRECTORY NORMALIZATION
            # Convert internal "2_SAMUEL" style keys to website display-matching "2 SAMUEL" or "HOSEA"
            web_folder_name = book_prefix.replace("_", " ").upper()
            book_audio_out_dir = AUDIO_DIR / web_folder_name
            book_audio_out_dir.mkdir(parents=True, exist_ok=True)

            print(f"   📄 Processing Chapter: {f_path.name} ➔ Routing to /audio/{web_folder_name}/")
            
            unique_suffix = int(time.time())
            temp_extract_dir = f_path.parent / f"temp_{f_path.stem}_{unique_suffix}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            try:
                # 1. Unzip the container
                with zipfile.ZipFile(f_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                    
                mscx_files = list(temp_extract_dir.glob("*.mscx"))
                if not mscx_files:
                    continue
                    
                mscx_file_path = mscx_files[0]
                tree = ET.parse(mscx_file_path)
                root = tree.getroot()

                # 2. Inject Breathing Delays
                for caesura_node in root.findall(".//Caesura") + root.findall(".//caesura"):
                    new_pause = caesura_node.find("pause")
                    if new_pause is None:
                        new_pause = ET.SubElement(caesura_node, "pause")
                    new_pause.text = PAUSE_TIMES["atnah"]

                for breath_node in root.findall(".//BreathMark") + root.findall(".//breathMark") + root.findall(".//Breath"):
                    new_pause = breath_node.find("pause")
                    if new_pause is None:
                        new_pause = ET.SubElement(breath_node, "pause")
                    new_pause.text = PAUSE_TIMES["zaqef_qatan"]

                # 3. Analyze Verse Measure Boundaries via Rests
                score_node = root.find("Score")
                if score_node is None:
                    continue
                staff1 = score_node.find("./Staff[@id='1']")
                if staff1 is None:
                    continue
                
                measures = staff1.findall("Measure")
                verse_buckets = []
                current_verse_measures = []
                
                for meas in measures:
                    current_verse_measures.append(meas)
                    if meas.find(".//Rest") is not None:
                        verse_buckets.append(current_verse_measures)
                        current_verse_measures = []
                if current_verse_measures:
                    verse_buckets.append(current_verse_measures)

                # 4. Generate standalone verse scores and call MuseScore compiler
                for idx, verse_measures in enumerate(verse_buckets, start=1):
                    # Format filename perfectly to match webpage array links: e.g., "2_Samuel_1_1.mp3"
                    formatted_book_name = book_prefix.replace("_", " ").title().replace(" ", "_")
                    verse_file_name = f"{formatted_book_name}_{chapter_num}_{idx}.mp3"
                    mp3_out_path = book_audio_out_dir / verse_file_name

                    if mp3_out_path.exists():
                        continue

                    verse_root = ET.fromstring(ET.tostring(root))
                    verse_score = verse_root.find("Score")
                    
                    for v_staff in verse_score.findall("Staff"):
                        for old_meas in list(v_staff):
                            v_staff.remove(old_meas)
                    
                    staff1_target = verse_score.find("./Staff[@id='1']")
                    for orig_meas in verse_measures:
                        cloned_meas = ET.fromstring(ET.tostring(orig_meas))
                        
                        # Scrub malicious IDs causing rendering glitches
                        for parent in cloned_meas.iter():
                            eid_node = parent.find("eid")
                            if eid_node is not None:
                                parent.remove(eid_node)
                        staff1_target.append(cloned_meas)

                    # Export temporary files for the compiler compilation phase
                    v_prefix = f"temp_v_{idx}_{unique_suffix}"
                    sliced_mscx = temp_extract_dir / f"{v_prefix}.mscx"
                    verse_tree = ET.ElementTree(verse_root)
                    verse_tree.write(sliced_mscx, encoding="utf-8", xml_declaration=True)
                    
                    temp_mscz_path = f_path.with_name(f"{v_prefix}.mscz")
                    with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                        zip_write.write(sliced_mscx, sliced_mscx.name)

                    # Execute subprocess compile operation
                    cmd = [MUSESCORE_PATH, "-o", str(mp3_out_path), str(temp_mscz_path)]
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if temp_mscz_path.exists():
                        os.remove(temp_mscz_path)

                    if result.returncode == 0:
                        processed_verses_count += 1
                    else:
                        print(f"      ❌ MuseScore rendering breakdown on verse {idx}: {result.stderr}")

            except Exception as e:
                print(f"   ❌ Critical tracking fault on {f_path.name}: {e}")
            finally:
                time.sleep(0.1)
                if temp_extract_dir.exists():
                    def remove_readonly(func, path, excinfo):
                        import stat
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    shutil.rmtree(temp_extract_dir, onerror=remove_readonly)

    print(f"\n🎉 Job complete! Processed and added {processed_verses_count} verse tracks across book directories.")

if __name__ == "__main__":
    run_global_book_based_audio_compiler()
