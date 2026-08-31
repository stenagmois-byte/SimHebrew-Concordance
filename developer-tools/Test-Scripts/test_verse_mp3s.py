import os
import re
import json
import time
import zipfile
import shutil
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

# --- Setup Constants ---
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore4.exe"
REPO_ROOT = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance")
SCORE_DIR = REPO_ROOT / "musicscores"
AUDIO_DIR = SCORE_DIR / "audio"

PAUSE_TIMES = {
    "atnah": "1.5",
    "zaqef_qatan": "1.0"
}

# Strict target test files
TEST_TARGETS = ["2-SAMUEL-001.mscz", "HOSEA-001.mscz"]

def run_targeted_verse_test():
    print("🧪 Launching Isolated Cross-Volume Verification Test Loop...")
    if not os.path.exists(MUSESCORE_PATH):
        print(f"❌ Error: MuseScore missing at {MUSESCORE_PATH}")
        return

    MAP_PATH = SCORE_DIR.parent / "book_map.json"
    if not MAP_PATH.exists():
        print(f"❌ Error: Central layout map missing at {MAP_PATH}")
        return

    with open(MAP_PATH, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    # Scan directories
    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir() and d.name != "audio"]

    for target_name in TEST_TARGETS:
        print(f"\n──────────────────────────────────────────────────")
        print(f"🔍 Searching for Test Target: {target_name}")
        
        # Locate the file dynamically in any sub-folder volume
        found_file = None
        matched_folder = None
        for d in subdirs:
            potential_file = d / target_name
            if potential_file.exists():
                found_file = potential_file
                matched_folder = d
                break
        
        if not found_file:
            print(f"⚠️ Target file {target_name} not found on disk. Skipping.")
            continue

        print(f"📂 Found in Volume Folder: [{matched_folder.name}]")

        # Re-verify layout mapping normalization
        match = re.match(r"^([0-9a-zA-Z_-]+)-(\d{3})", found_file.name.lower())
        if not match:
            continue
            
        raw_prefix = match.group(1).replace("-", "_") # "2-samuel" -> "2_samuel"
        book_prefix = raw_prefix.upper()              # "2_SAMUEL"
        chapter_num = int(match.group(2))

        expected_folder = book_map.get(book_prefix)
        print(f"🗺️  Mapping Lookup: Prefix '{book_prefix}' -> Maps to folder '{expected_folder}'")

        # Establish verified destination paths
        book_audio_out_dir = AUDIO_DIR / matched_folder.name
        book_audio_out_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Destination Folder: {book_audio_out_dir}")

        unique_suffix = int(time.time())
        temp_extract_dir = found_file.parent / f"temp_test_{found_file.stem}_{unique_suffix}"
        temp_extract_dir.mkdir(exist_ok=True)
        
        try:
            with zipfile.ZipFile(found_file, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                
            mscx_files = list(temp_extract_dir.glob("*.mscx"))
            if not mscx_files:
                print("❌ Failed to locate internal score markup file.")
                continue
                
            mscx_file_path = mscx_files[0]
            tree = ET.parse(mscx_file_path)
            root = tree.getroot()

            # Apply breathing injection
            for caesura_node in root.findall(".//Caesura") + root.findall(".//caesura"):
                new_pause = caesura_node.find("pause")
                if new_pause is None: new_pause = ET.SubElement(caesura_node, "pause")
                new_pause.text = PAUSE_TIMES["atnah"]

            for breath_node in root.findall(".//BreathMark") + root.findall(".//breathMark") + root.findall(".//Breath"):
                new_pause = breath_node.find("pause")
                if new_pause is None: new_pause = ET.SubElement(breath_node, "pause")
                new_pause.text = PAUSE_TIMES["zaqef_qatan"]

            # Verse isolation boundary processing
            score_node = root.find("Score")
            staff1 = score_node.find("./Staff[@id='1']")
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

            print(f"✂️  Chapter structural analysis complete: Found {len(verse_buckets)} total verses.")

            # Sample slice execution on Verse 1
            if verse_buckets:
                idx = 1
                # Format book name prefix explicitly for tracking (e.g. "2_Sam_1_1.mp3" or "2Sam_1_1.mp3")
                # Adjust string template formatting here to match exactly what your Concordance lists!
                formatted_book_name = book_prefix.replace("_", " ").title().replace(" ", "_")
                verse_file_name = f"{formatted_book_name}_{chapter_num}_{idx}.mp3"
                mp3_out_path = book_audio_out_dir / verse_file_name

                print(f"🎵 Generated target filename path will be: {verse_file_name}")

                verse_root = ET.fromstring(ET.tostring(root))
                verse_score = verse_root.find("Score")
                for v_staff in verse_score.findall("Staff"):
                    for old_meas in list(v_staff): v_staff.remove(old_meas)
                
                staff1_target = verse_score.find("./Staff[@id='1']")
                for orig_meas in verse_buckets[0]: # Target first verse only for test speed
                    cloned_meas = ET.fromstring(ET.tostring(orig_meas))
                    for parent in cloned_meas.iter():
                        eid_node = parent.find("eid")
                        if eid_node is not None: parent.remove(eid_node)
                    staff1_target.append(cloned_meas)

                v_prefix = f"temp_test_v_{idx}_{unique_suffix}"
                sliced_mscx = temp_extract_dir / f"{v_prefix}.mscx"
                verse_tree = ET.ElementTree(verse_root)
                verse_tree.write(sliced_mscx, encoding="utf-8", xml_declaration=True)
                
                temp_mscz_path = found_file.with_name(f"{v_prefix}.mscz")
                with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                    zip_write.write(sliced_mscx, sliced_mscx.name)

                print(f"🎹 Invoking compilation subprocess test for Verse 1...")
                cmd = [MUSESCORE_PATH, "-o", str(mp3_out_path), str(temp_mscz_path)]
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if temp_mscz_path.exists():
                    os.remove(temp_mscz_path)

                if result.returncode == 0:
                    print(f"✅ Success! Test output written out to: {mp3_out_path}")
                else:
                    print(f"❌ MuseScore failed rendering: {result.stderr}")

        except Exception as e:
            print(f"❌ Structural parser breakdown: {e}")
        finally:
            time.sleep(0.2)
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)

    print("\n🏁 Isolated verification test script execution finalized.")

if __name__ == "__main__":
    run_targeted_verse_test()
