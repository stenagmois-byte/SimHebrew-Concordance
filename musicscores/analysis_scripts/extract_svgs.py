import os
import subprocess
import re
from pathlib import Path

# --- HARDCODED SYSTEM PATH CONFIGURATION ---
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
MUSIC_SCORES_BASE = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores")

# Standard install path for MuseScore 4. Update this if you use MuseScore 3!
MUSESCORE_EXE = Path(r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe")

def get_active_book_folder():
    """Maps the active EPUB file inside Input to your clean GitHub directory name."""
    if not INPUT_DIR.exists():
        print(f"❌ ERROR: Input folder {INPUT_DIR} does not exist.")
        return None
    
    epubs = list(INPUT_DIR.glob("*.epub"))
    if not epubs:
        print(f"⚠️ No active .epub found inside {INPUT_DIR} to identify current volume target.")
        return None
    
    epub_stem = epubs[0].stem
    if " - " in epub_stem:
        book_match_token = epub_stem.split(" - ")[0].strip().lower()
    else:
        book_match_token = epub_stem.strip().lower()
        
    if MUSIC_SCORES_BASE.exists():
        for item in MUSIC_SCORES_BASE.iterdir():
            if item.is_dir() and book_match_token in item.name.lower():
                print(f"🎯 Project Detected: '{epub_stem}' mapped to directory: '{item.name}'")
                return item.name
    return None

def run_musescore_export(mscz_path, output_dir):
    """Calls MuseScore via command line to silently export the score to SVGs."""
    # Generate the base name pattern MuseScore uses for image parts
    # e.g., OutputFolder/LEVITICUS-001.svg -> becomes LEVITICUS-001-1.svg, etc.
    base_output_name = output_dir / f"{mscz_path.stem}.svg"
    
    print(f"   👉 Exporting: {mscz_path.name}")
    
    # Complete MuseScore headless command-line instruction arguments
    cmd = [
        str(MUSESCORE_EXE),
        "-o", str(base_output_name),  # Set destination asset path string
        str(mscz_path)                # Source compressed score file
    ]
    
    try:
        # Run process invisibly in the background
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ MuseScore Export Crash on {mscz_path.name}: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"   ❌ SYSTEM CRITICAL: Could not find MuseScore executable at path:\n      '{MUSESCORE_EXE}'")
        print("      Please verify your MuseScore installation path inside the script configuration properties.")
        return False

def main():
    print("=" * 115)
    # Target execution pipeline header initialization
    print("AUTOMATED HEADLESS MUSESCORE EXPORT ENGINE: NATIVE RECURSIVE SVG GENERATOR")
    print("=" * 115)
    
    active_volume = get_active_book_folder()
    if not active_volume:
        print("❌ CRITICAL CLOSE: No valid active volume context could be determined. Exiting.")
        return
        
    # Set up our specific volume search directory
    volume_source_dir = MUSIC_SCORES_BASE / active_volume
    
    # Establish a localized target folder for the raw exported SVGs inside KindleProject
    # This prevents polluting your main workspace directories
    export_destination = INPUT_DIR / "Raw_Exported_SVGs"
    export_destination.mkdir(parents=True, exist_ok=True)
    
    print(f"Source Track: {volume_source_dir}")
    print(f"Export Destination: {export_destination}\n")
    
    # Step 1: Use deep recursive rglob to isolate every matching .mscz file in the active volume folder
    all_scores = []
    for score_path in volume_source_dir.rglob("*.mscz"):
        if "_PRE_PATCH_BACKUP" in score_path.parts or "analysis_scripts" in score_path.parts:
            continue
        all_scores.append(score_path)
        
    if not all_scores:
        print(f"❌ ERROR: No .mscz files discovered inside volume tracker folder structural tree: {volume_source_dir}")
        return
        
    all_scores = sorted(all_scores)
    print(f"Found {len(all_scores)} score chapter file(s) to process. Initializing MuseScore background instance...\n")
    
    success_count = 0
    for score in all_scores:
        if run_musescore_export(score, export_destination):
            success_count += 1
            
    print("-" * 115)
    print(f"🤖 PROCESS FINISHED: Successfully generated raw SVGs for {success_count} / {len(all_scores)} chapters.")
    print(f"   Your pristine assets are waiting inside: '{export_destination}'")
    print("   👉 You can now run your renaming logic on these files without risk!")
    print("=" * 115)

if __name__ == "__main__":
    main()
