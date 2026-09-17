import os
import re
import shutil
import zipfile
import json
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

# 🌐 Workstation Architecture Configuration Parameters
SCORE_DIR = Path("./musicscores")

# 🎯 FIX THIS PATH: Update this string to match your computer's exact MuseScore 4 path
# (Check your MuseScore shortcut properties -> Target field to get this exactly right)
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore4.exe"

# 🎯 Your Agogic Playback Pause Time Metrics (In Seconds)
PAUSE_TIMES = {
    "atnah": "2.0",        # The Caesura pauses playback for 2.0s
    "zaqef_qatan": "1.0"   # The Breath Mark pauses playback for 1.0s
}

import xml.etree.ElementTree as ET

def run_flexible_geographic_trial():
    print("🚀 Initializing Production-Ready Global Multi-Volume Batch Audio Compiler...")
    if not os.path.exists(MUSESCORE_PATH):
        print(f"❌ Error: MuseScore executable missing at {MUSESCORE_PATH}")
        return

    # =========================================================================
    # STEP 1 & 2: Load the central JSON map and scan available directories
    # =========================================================================
    MAP_PATH = SCORE_DIR.parent / "book_map.json"
    if not MAP_PATH.exists():
        print(f"❌ Error: Central layout map missing at {MAP_PATH}")
        return

    with open(MAP_PATH, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    processed_count = 0
    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir()]

    # Gather all active unique folders defined in your layout map
    mapped_folders = set(book_map.values())

    # =========================================================================
    # STEP 3: Begin global multi-volume loop across your absolute geography
    # =========================================================================
    for folder_name in sorted(mapped_folders):
        # Match against actual physical directories on disk
        matched_folder = next((d for d in subdirs if d.name.lower() == folder_name.lower()), None)
        
        if not matched_folder:
            # Silently skip if a book class isn't present in your current folder slice
            continue

        print(f"\n📂 Entering Production Volume: [{matched_folder.name}]")

        # Process every score found within this structural volume folder
        for f_path in matched_folder.iterdir():
            if not f_path.is_file() or f_path.suffix.lower() != ".mscz":
                continue
            if f_path.name.startswith("temp_") or f_path.name.startswith("temp_trial_"):
                continue

                        # 🎯 FIXED REGEX: Accepts either an underscore (_) or a hyphen (-) after the book number
            match = re.match(r"^([0-9a-zA-Z_-]+)-(\d{3})", f_path.name.lower())
            if not match:
                continue
                
            # 🎯 NORMALIZATION: Automatically convert hyphens to underscores 
            # This turns "1-samuel" into "1_SAMUEL" so your JSON lookup works perfectly!
            raw_prefix = match.group(1).replace("-", "_")
            book_prefix = raw_prefix.upper() 
            chapter_num = match.group(2)

            # Defensive verification: Ensure this file prefix belongs in this specific directory
            expected_folder = book_map.get(book_prefix)
            if not expected_folder or expected_folder.lower() != matched_folder.name.lower():
                continue

            # Establish the strict case-sensitive file naming scheme for GitHub
            mp3_out = matched_folder / f"{book_prefix}-{chapter_num}.mp3"


            if mp3_out.exists():
                print(f"   ⏩ Skipping: {f_path.name} (MP3 already generated)")
                continue

            print(f"   📄 Processing Score Chapter: {f_path.name}")
            
            # 🎯 THE UNIQUE SANDBOX FIX: Append a unique timestamp to prevent Windows folder locks
            import time
            unique_suffix = int(time.time())
            temp_extract_dir = f_path.parent / f"temp_{f_path.stem}_{unique_suffix}"
            temp_extract_dir.mkdir(exist_ok=True)
            
            try:
                # Unzip the container into our uniquely isolated sandbox directory
                with zipfile.ZipFile(f_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                    
                mscx_files = list(temp_extract_dir.glob("*.mscx"))
                if not mscx_files:
                    print(f"   ⚠️ Skipping: Could not locate .mscx file asset inside zip tree.")
                    continue
                    
                mscx_file_path = mscx_files[0]
                
                tree = ET.parse(mscx_file_path)
                root = tree.getroot()
                modified = False

                # Global search handles monophonic track layouts perfectly
                for caesura_node in root.findall(".//Caesura") + root.findall(".//caesura"):
                    target_seconds = PAUSE_TIMES["atnah"]
                    pause_node = caesura_node.find("pause")
                    if pause_node is not None:
                        pause_node.text = target_seconds
                    else:
                        new_pause = ET.SubElement(caesura_node, "pause")
                        new_pause.text = target_seconds
                    modified = True

                for breath_node in root.findall(".//BreathMark") + root.findall(".//breathMark") + root.findall(".//Breath"):
                    target_seconds = PAUSE_TIMES["zaqef_qatan"]
                    pause_node = breath_node.find("pause")
                    if pause_node is not None:
                        pause_node.text = target_seconds
                    else:
                        new_pause = ET.SubElement(breath_node, "pause")
                        new_pause.text = target_seconds
                    modified = True

                if modified:
                    tree.write(mscx_file_path, encoding="utf-8", xml_declaration=True)
                    
                    temp_mscz_path = f_path.with_name(f"temp_trial_{f_path.name}")
                    with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                        for file_to_pack in temp_extract_dir.rglob("*"):
                            if file_to_pack.is_file():
                                relative_archive_path = file_to_pack.relative_to(temp_extract_dir)
                                zip_write.write(file_to_pack, relative_archive_path)

                    print(f"   Running MuseScore compiler engine to generate MP3...")
                    cmd = [
                        MUSESCORE_PATH,
                        "-o", str(mp3_out),
                        str(temp_mscz_path)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"   ❌ MuseScore Compilation Error (Exit Code {result.returncode}):")
                        print(result.stderr)
                    else:
                        print(f"   ✅ Performance audio file generated successfully: {mp3_out.name}")
                        processed_count += 1
                    
                    if temp_mscz_path.exists():
                        os.remove(temp_mscz_path)
                else:
                    print("   ℹ️ No breath or caesura nodes detected inside this file.")

            except Exception as e:
                print(f"   ❌ Trial Exception hit on parsing: {e}")
                
            finally:
                # Give Windows a brief moment to release file handles
                time.sleep(0.5)
                
                if temp_extract_dir.exists():
                    def remove_readonly(func, path, excinfo):
                        import stat
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    shutil.rmtree(temp_extract_dir, onerror=remove_readonly)

    print(f"\n🎉 Global compilation batch completed successfully. Processed {processed_count} new multi-volume tracks.")

if __name__ == "__main__":
    run_flexible_geographic_trial()
