import os
import re
import shutil
import zipfile
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

def change_staff1_to_mezzo_soprano(root_xml):
    score_node = root_xml.find("Score")
    if score_node is None:
        return False
        
    part1 = score_node.find(".//Part")
    if part1 is None:
        return False
        
    inst = part1.find("Instrument")
    if inst is None:
        return False
        
    # 1. FORCE CORE ID ATTRIBUTE OVERWRITE FROM PIANO TO MEZZO
    inst.set("id", "mezzo-soprano")
    
    # 2. Update remaining tracking elements safely
    for tag, text in [("longName", "Mezzo-soprano"), ("shortName", "M-S."), ("trackName", "Mezzo-soprano")]:
        node = inst.find(tag)
        if node is not None: node.text = text
        else: ET.SubElement(inst, tag).text = text
    
    inst_id = inst.find("instrumentId")
    if inst_id is not None: 
        inst_id.text = "voice.mezzo-soprano"
    else:
        ET.SubElement(inst, "instrumentId").text = "voice.mezzo-soprano"

    channel = inst.find("Channel")
    if channel is not None:
        program = channel.find("program")
        if program is not None:
            program.set("value", "52")
        else:
            ET.SubElement(channel, "program", {"value": "52"})
            
    return True

def run_flexible_geographic_trial():
    print("Initiating Case-Agnostic Geographic Performance Trial...")
    print(f"Scanning base directory: {SCORE_DIR.resolve()}\n")
    
    if not SCORE_DIR.exists():
        print(f"❌ Error: Cannot locate base directory '{SCORE_DIR}'. Make sure you run this from the repository folder.")
        return

    # Verify that the MuseScore program file actually exists at the defined path location before starting
    if not os.path.exists(MUSESCORE_PATH):
        print(f"❌ Critical Error: MuseScore executable not found at: {MUSESCORE_PATH}")
        print("   Please check your MuseScore 4 shortcut target properties and update the MUSESCORE_PATH variable.")
        return

    trial_targets = [
        {"book_keyword": "genesis", "chapter": "001", "folder_keyword": "genesis"},
        {"book_keyword": "psalms", "chapter": "001", "folder_keyword": "psalms"}
    ]

    processed_count = 0
    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir()]

    for target in trial_targets:
        matched_folder = None
        for subdir in subdirs:
            if target["folder_keyword"] in subdir.name.lower():
                matched_folder = subdir
                break

        if not matched_folder:
            print(f"⚠️ Could not find a folder matching '{target['folder_keyword']}' inside musicscores/ - Skipping.")
            continue

        print(f"Scanning matched folder '{matched_folder.name}' for {target['book_keyword'].upper()}-{target['chapter']}...")
        
        found_any_match_in_folder = False
        for file_path in matched_folder.iterdir():
            if not file_path.is_file():
                continue
                
            filename_lower = file_path.name.lower()
            
            # Match files that start with our book and chapter prefix using a flexible hyphen check
            prefix_match = f"^{target['book_keyword']}-{target['chapter']}"
            if re.match(prefix_match, filename_lower) and filename_lower.endswith(".mscz") and not filename_lower.startswith("temp_"):
                
                found_any_match_in_folder = True
                mp3_output_path = file_path.with_suffix(".mp3")
                # mp3_output_path = file_path.with_name(f"{file_path.stem}_voice.mp3")
                print(f"\n[FOUND FILE] Processing file: {matched_folder.name}/{file_path.name}")
                
                # 🎯 THE UNIQUE SANDBOX FIX: Append a unique timestamp to prevent Windows folder collision locks completely
                import time
                unique_suffix = int(time.time())
                temp_extract_dir = file_path.parent / f"temp_{file_path.stem}_{unique_suffix}"
                temp_extract_dir.mkdir(exist_ok=True)
                
                try:
                    # Unzip the container into our uniquely isolated sandbox directory
                    with zipfile.ZipFile(file_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_extract_dir)
                        
                    mscx_files = list(temp_extract_dir.glob("*.mscx"))
                    if not mscx_files:
                        print(f"   ⚠️ Skipping: Could not locate .mscx file asset inside zip tree.")
                        continue
                        
                    mscx_file_path = mscx_files[0]
                    
                    tree = ET.parse(mscx_file_path)
                    root = tree.getroot()
                    modified = False

                    #if change_staff1_to_mezzo_soprano(root):
                        #print("   -> Voice instrument successfully changed to Mezzo-soprano.")
                        #modified = True

                    # Global search handles monophonic track layouts perfectly
                    for caesura_node in root.findall(".//Caesura") + root.findall(".//caesura"):
                        target_seconds = PAUSE_TIMES["atnah"]
                        pause_node = caesura_node.find("pause")
                        if pause_node is not None:
                            pause_node.text = target_seconds
                        else:
                            new_pause = ET.SubElement(caesura_node, "pause")
                            new_pause.text = target_seconds
                        
                        #print(f"   -> Found Atnah Caesura. Injected pause duration: {target_seconds}s")
                        modified = True

                    for breath_node in root.findall(".//BreathMark") + root.findall(".//breathMark") + root.findall(".//Breath"):
                        target_seconds = PAUSE_TIMES["zaqef_qatan"]
                        pause_node = breath_node.find("pause")
                        if pause_node is not None:
                            pause_node.text = target_seconds
                        else:
                            new_pause = ET.SubElement(breath_node, "pause")
                            new_pause.text = target_seconds
                            
                        #print(f"   -> Found Zaqef-Qatan BreathMark. Injected pause duration: {target_seconds}s")
                        modified = True

                    if modified:
                        tree.write(mscx_file_path, encoding="utf-8", xml_declaration=True)
                        
                        temp_mscz_path = file_path.with_name(f"temp_trial_{file_path.name}")
                        with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                            for file_to_pack in temp_extract_dir.rglob("*"):
                                if file_to_pack.is_file():
                                    relative_archive_path = file_to_pack.relative_to(temp_extract_dir)
                                    zip_write.write(file_to_pack, relative_archive_path)

                        print(f"   Running MuseScore compiler engine to generate MP3...")
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
                        try:
                            # Use the error handler to cleanly force-remove locked folder assets
                            shutil.rmtree(temp_extract_dir, onexc=remove_readonly)
                        except Exception as rm_err:
                            # If Windows absolutely refuses to let go, log a warning and move on instead of crashing
                            print(f"   ⚠️ Cleanup deferred for temporary folder: {rm_err}")
                        
        if not found_any_match_in_folder:
            print(f"   ℹ️ Looked through folder contents but found no file starting with '{target['book_keyword'].upper()}-{target['chapter']}.mscz'")

    print(f"\nTrial Complete. Total performance tracks rendered successfully: {processed_count}")

if __name__ == "__main__":
    run_flexible_geographic_trial()
