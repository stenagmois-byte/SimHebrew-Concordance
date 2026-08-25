import os
import re
import shutil
import zipfile
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

# 🌐 Workstation Architecture Configuration Parameters
# Assumes you run this script from the parent folder of 'musicscores'
SCORE_DIR = Path("./musicscores")
# Update this path to point directly to your workstation's MuseScore 4 executable file
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore.exe"

# 🎯 Your Agogic Playback Pause Time Metrics (In Seconds)
PAUSE_TIMES = {
    "atnah": "2.0",        # The Caesura pauses playback for 2.0s
    "zaqef_qatan": "1.0"   # The Breath Mark pauses playback for 1.0s
}

# 🗺️ THE MASTER GEOGRAPHY MAP: Translates books directly to their actual folders with spaces
BOOK_FOLDER_MAP = {
    "GENESIS": "Genesis",
    "EXODUS": "Exodus",
    "LEVITICUS": "Leviticus",
    "NUMBERS": "Numbers",
    "DEUTERONOMY": "Deuteronomy",
    "JOSHUA": "Joshua-Judges",
    "JUDGES": "Joshua-Judges",
    "1 SAMUEL": "Samuel",
    "2 SAMUEL": "Samuel",
    "1 KINGS": "Kings",
    "2 KINGS": "Kings",
    "ISAIAH": "Isaiah",
    "JEREMIAH": "Jeremiah",
    "EZEKIEL": "Ezekiel",
    "HOSEA": "The Twelve", "JOEL": "The Twelve", "AMOS": "The Twelve", "OBADIAH": "The Twelve",
    "JONAH": "The Twelve", "MICAH": "The Twelve", "NAHUM": "The Twelve", "HABAKKUK": "The Twelve",
    "ZEPHANIAH": "The Twelve", "HAGGAI": "The Twelve", "ZECHARIAH": "The Twelve", "MALACHI": "The Twelve",
    "PSALMS": "The Psalms",
    "PROVERBS": "Proverbs",
    "JOB": "Job",
    "SONG": "The Five Scrolls", "RUTH": "The Five Scrolls", "LAMENTATIONS": "The Five Scrolls", "QOHELET": "The Five Scrolls", "ESTHER": "The Five Scrolls",
    "DANIEL": "Daniel-Ezra-Nehemiah", "EZRA": "Daniel-Ezra-Nehemiah", "NEHEMIAH": "Daniel-Ezra-Nehemiah",
    "1 CHRONICLES": "Chronicles", "2 CHRONICLES": "Chronicles"
}

def run_geographic_trial():
    print("Initiating Geographic Performance Trial (Genesis 1 & Psalm 1)...")
    print(f"Scanning target path directory: {SCORE_DIR.resolve()}\n")
    
    if not SCORE_DIR.exists():
        print(f"❌ Error: Cannot locate directory '{SCORE_DIR}'. Make sure you run this from the parent folder.")
        return

    # 🎯 Define our trial targets explicitly based on your repository naming conventions
    trial_targets = [
        {"book": "GENESIS", "chapter": "001", "folder": BOOK_FOLDER_MAP["GENESIS"]},
        {"book": "PSALMS", "chapter": "001", "folder": BOOK_FOLDER_MAP["PSALMS"]}
    ]

    processed_count = 0

    for target in trial_targets:
        target_folder_path = SCORE_DIR / target["folder"]
        if not target_folder_path.exists():
            print(f"⚠️ Target folder missing: {target_folder_path} - Skipping {target['book']}")
            continue

        print(f"Scanning folder '{target['folder']}' for {target['book']}_{target['chapter']}...")
        
        # Scan files inside the specific target folder
        for mscz_path in target_folder_path.glob("*.mscz"):
            filename = mscz_path.name
            
            # Wildcard verification pattern: catches exact chapters and verse variants (e.g., PSALMS_001_004)
            prefix_pattern = f"^{target['book']}_{target['chapter']}"
            if not re.match(prefix_pattern, filename) or "temp_" in filename:
                continue

            mp3_output_path = mscz_path.with_suffix(".mp3")
            print(f"\n[FOUND MATCH] Modifying playback inside: {target['folder']}/{filename}")
            
            temp_extract_dir = mscz_path.parent / f"temp_{mscz_path.stem}"
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
            temp_extract_dir.mkdir(exist_ok=True)
            
            try:
                # 1. Unzip the container into a safe sandbox directory
                with zipfile.ZipFile(mscz_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract_dir)
                    
                mscx_files = list(temp_extract_dir.glob("*.mscx"))
                if not mscx_files:
                    print(f"   ⚠️ Skipping: Could not locate .mscx file asset inside zip tree.")
                    continue
                    
                mscx_file_path = mscx_files[0]
                
                # 2. Parse the sheet music XML layout structure
                tree = ET.parse(mscx_file_path)
                root = tree.getroot()
                modified = False

                # Walk note components to find embedded pauses
                for note in root.findall(".//Note"):
                    breath_node = note.find("Breath")
                    if breath_node is not None:
                        text_node = note.find(".//text")
                        text_content = text_node.text if (text_node is not None and text_node.text) else ""
                        
                        subtype_node = breath_node.find("subtype")
                        subtype_val = subtype_node.text if subtype_node is not None else ""

                        target_seconds = "0.5" 
                        
                        # 🎯 CASE A: ATNAH CAESURA
                        if "caesura" in subtype_val.lower() or "\u0591" in text_content:
                            target_seconds = PAUSE_TIMES["atnah"]
                            print(f"   -> Detected Atnah Caesura. Injected pause duration: {target_seconds}s")
                        
                        # 🎯 CASE B: ZAQEF-QATAN BREATH
                        elif "breath" in subtype_val.lower() or "\u0594" in text_content:
                            target_seconds = PAUSE_TIMES["zaqef_qatan"]
                            print(f"   -> Detected Zaqef-Qatan Breath. Injected pause duration: {target_seconds}s")
                        
                        # Update explicit pause nodes inside the schema tree
                        pause_node = breath_node.find("pause")
                        duration_node = breath_node.find("duration")
                        
                        if pause_node is not None:
                            pause_node.text = target_seconds
                        elif duration_node is not None:
                            duration_node.text = target_seconds
                        else:
                            new_pause = ET.SubElement(breath_node, "pause")
                            new_pause.text = target_seconds
                            
                        modified = True

                # 3. Save updates into our temporary sandbox container
                if modified:
                    tree.write(mscx_file_path, encoding="utf-8", xml_declaration=True)
                    
                    temp_mscz_path = mscz_path.with_name(f"temp_trial_{filename}")
                    with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                        for file_to_pack in temp_extract_dir.rglob("*"):
                            if file_to_pack.is_file():
                                relative_archive_path = file_to_pack.relative_to(temp_extract_dir)
                                zip_write.write(file_to_pack, relative_archive_path)

                    # 4. Compile the output file track via MuseScore 4
                    print(f"   Running MuseScore compiler engine path to generate MP3...")
                    cmd = [
                        MUSESCORE_PATH,
                        "-o", str(mp3_output_path),
                        str(temp_mscz_path)
                    ]
                    
                    result = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        print(f"   ❌ MuseScore Compilation Error (Exit Code {result.returncode}):")
                        print(result.stderr)
                    else:
                        print(f"   ✅ Performance audio file generated successfully: {mp3_output_path.name}")
                        processed_count += 1
                    
                    if temp_mscz_path.exists():
                        os.remove(temp_mscz_path)
                else:
                    print("   ℹ️ No breath or caesura nodes detected inside this file node tracking layer.")

            except Exception as e:
                print(f"   ❌ Trial Exception hit on parsing: {e}")
                
            finally:
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir)

    print(f"\nTrial Complete. Total performance tracks rendered successfully: {processed_count}")

if __name__ == "__main__":
    run_geographic_trial()
