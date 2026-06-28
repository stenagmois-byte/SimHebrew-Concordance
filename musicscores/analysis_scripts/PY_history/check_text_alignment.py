import os
import zipfile
import re
import xml.etree.ElementTree as ET
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
MUSIC_SCORES_BASE = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores")

def get_active_book_folder():
    """Maps the complex EPUB name in Input to the clean GitHub volume folder."""
    if not INPUT_DIR.exists():
        print(f"❌ ERROR: Input folder {INPUT_DIR} does not exist.")
        return None
    
    epubs = list(INPUT_DIR.glob("*.epub"))
    if not epubs:
        print(f"⚠️ No active .epub found inside {INPUT_DIR}.")
        return None
    
    epub_stem = epubs[0].stem
    match = re.split(r'[\s\-]', epub_stem)
    base_book_name = match[0].strip() if match else epub_stem
    
    if MUSIC_SCORES_BASE.exists():
        for item in MUSIC_SCORES_BASE.iterdir():
            if item.is_dir() and item.name.lower() == base_book_name.lower():
                return item.name
    return base_book_name

def analyze_word_alignment(mscz_path, display_path):
    filename = os.path.basename(mscz_path)
    try:
        with zipfile.ZipFile(mscz_path, 'r') as archive:
            mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            if not mscx_files:
                return
            with archive.open(mscx_files[0]) as file_stream:
                mscx_content = file_stream.read().decode('utf-8', errors='ignore')
        
        root = ET.fromstring(mscx_content)
        measures = root.findall(".//Measure") or [el for el in root.iter() if el.tag.lower() == 'measure']
        
        print(f"\n📊 Text Alignment Profile for: {display_path}")
        print("-" * 80)
        
        manual_adjustments_count = 0
        y_profile_map = {}
        
        for m_idx, measure in enumerate(measures, start=1):
            # Locate all lyric/text elements belonging to the Hebrew words
            # MuseScore stores lyric lines inside <Lyrics> or <StaffText> structures
            text_nodes = measure.findall(".//Lyrics") + measure.findall(".//StaffText")
            
            for node in text_nodes:
                text_elem = node.find("text")
                word_text = "".join(node.itertext()).strip() if text_elem is None else (text_elem.text or "").strip()
                
                if not word_text:
                    continue
                
                # Extract positional shifts
                pos_x = node.find(".//pos/x") if node.find(".//pos/x") is not None else node.find("pos/x")
                pos_y = node.find(".//pos/y") if node.find(".//pos/y") is not None else node.find("pos/y")
                
                # If no custom shift exists, it uses MuseScore's automatic placement (0.0)
                has_manual_nudge = (pos_x is not None or pos_y is not None)
                x_val = float(pos_x.text) if pos_x is not None else 0.0
                y_val = float(pos_y.text) if pos_y is not None else 0.0
                
                if has_manual_nudge:
                    manual_adjustments_count += 1
                    # Clean up string for terminal display
                    clean_word = word_text.replace('\n', ' ').strip()
                    
                    if y_val not in y_profile_map:
                        y_profile_map[y_val] = []
                    y_profile_map[y_val].append((m_idx, clean_word, x_val))
                    
        if manual_adjustments_count == 0:
            print("  ✅ Perfect Uniformity: No manual word displacement offsets found. All text uses default style settings.")
            return

        print(f"  Found {manual_adjustments_count} manually adjusted text elements.")
        print("\n  [HEIGHT PROFILE BREAKDOWN]")
        
        # Sort by vertical deviation so you can spot the highest/lowest words immediately
        for y_offset in sorted(y_profile_map.keys()):
            direction = "RAISED" if y_offset < 0 else "LOWERED"
            print(f"  🔹 Y-Offset: {y_offset:+.2f} ({direction})")
            
            # Print words grouped at this specific vertical profile
            for m_idx, word, x_offset in y_profile_map[y_offset]:
                x_str = f", X-Shift: {x_offset:+.2f}" if x_offset != 0.0 else ""
                print(f"     ↳ Measure {m_idx:<3} | Word: {word:<15} {x_str}")
                
    except Exception as e:
        print(f"💥 Error scanning {filename}: {e}")

def main():
    clean_book_folder = get_active_book_folder()
    if not clean_book_folder:
        print("❌ CRITICAL: Could not determine active project.")
        return
        
    target_volume_dir = MUSIC_SCORES_BASE / clean_book_folder
    print("=" * 90)
    print(f"HEBREW WORD POSITION SCANNER: {clean_book_folder.upper()}")
    print("=" * 90)
    
    mscz_files = sorted(list(target_volume_dir.glob("*.mscz")) + list(target_volume_dir.glob("*.MSCZ")))
    
    if not mscz_files:
        print(f"🔍 No files found in {target_volume_dir}")
        return
        
    for file_path in mscz_files:
        relative_display = os.path.relpath(file_path, MUSIC_SCORES_BASE)
        analyze_word_alignment(file_path, relative_display)
    print("\n--- Alignment Scan Complete ---")

if __name__ == "__main__":
    main()
