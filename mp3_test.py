import os
import re
import shutil
import zipfile
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

# 🌐 Workstation Architecture Configuration Parameters
SCORE_DIR = Path("./musicscores")
# Update this path to point directly to your workstation's MuseScore 4 executable file
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore.exe"

# 🎯 Your Agogic Playback Pause Time Metrics (In Seconds)
PAUSE_TIMES = {
    "atnah": "2.0",        # The Caesura pauses playback for 2.0s
    "zaqef_qatan": "1.0"   # The Breath Mark pauses playback for 1.0s
}

def run_targeted_agogic_trial():
    print("Initiating Targeted Case-Insensitive Performance Trial...")
    print(f"Scanning target path directory: {SCORE_DIR.resolve()}")
    
    processed_count = 0

    # Safety check: Verify the parent folder actually exists before cycling layers
    if not SCORE_DIR.exists():
        print(f"❌ Error: Cannot locate directory '{SCORE_DIR}'. Are you sure you are in the parent folder?")
        return

    for mscz_path in SCORE_DIR.glob("**/*"):
        # We target all files matching .mscz extension case-insensitively
        if mscz_path.suffix.lower() != ".mscz":
            continue
            
        filename_lower = mscz_path.name.lower()
        
        # 🎯 CASE-INSENSITIVE TARGETING RULE:
        # Catches GENESIS_001.mscz, Genesis_001.MSCZ, psalms_001.mscz, etc.
        is_target = "genesis_001" in filename_lower or "psalms_001" in filename_lower
        
        if not is_target or mscz_path.name.startswith("._") or "temp_" in mscz_path.name:
            continue

        mp3_output_path = mscz_path.with_suffix(".mp3")
        print(f"\n[FOUND TARGET] Processing file: {mscz_path.name}")
        print(f"   Location path: {mscz_path.parent}")
        
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
                print(f"   ⚠️ Skipping: Could not locate underlying .mscx file asset inside zip tree.")
                continue
                
            mscx_file_path = mscx_files[0]
            
            # 2. Parse the sheet music xml code layout structure
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
                
                temp_mscz_path = mscz_path.with_name(f"temp_trial_{mscz_path.name}")
                with zipfile.ZipFile(temp_mscz_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
                    for file_to_pack in temp_extract_dir.rglob("*"):
                        if file_to_pack.is_file():
                            relative_archive_path = file_to_pack.relative_to(temp_extract_dir)
                            zip_write.write(file_to_pack, relative_archive_path)

                # 4. Compile the output file track via MuseScore
                print(f"   Running MuseScore compiler engine path to generate MP3...")
                cmd = [
                    MUSESCRE_PATH,
                    "-o", str(mp3_output_path),
                    str(temp_mscz_path)
                ]
                
                # 🎯 LIVE DEBUG UNLEASHED: Removed the suppression wrappers so you see errors directly!
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

    print(f"\nTrial Complete. Total performance tracks rendered: {processed_count}")

if __name__ == "__main__":
    run_targeted_agogic_trial()
