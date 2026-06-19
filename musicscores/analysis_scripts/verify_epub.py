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
        print(f"⚠️ No active .epub found inside {INPUT_DIR} to extract folder context.")
        return None
    
    epub_stem = epubs[0].stem
    match = re.split(r'[\s\-]', epub_stem)
    base_book_name = match[0].strip() if match else epub_stem
    
    if MUSIC_SCORES_BASE.exists():
        for item in MUSIC_SCORES_BASE.iterdir():
            if item.is_dir() and item.name.lower() == base_book_name.lower():
                print(f"🎯 EPUB Target '{epub_stem}' successfully mapped to GitHub folder: '{item.name}'")
                return item.name
                
    return base_book_name

def verify_single_file(mscz_path, display_path):
    filename = os.path.basename(mscz_path)
    try:
        with zipfile.ZipFile(mscz_path, 'r') as archive:
            mscx_files = [f for f in archive.namelist() if f.lower().endswith('.mscx')]
            if not mscx_files:
                return f"❌ [ERROR] No internal .mscx file found inside {filename}"
            with archive.open(mscx_files[0]) as file_stream:
                mscx_content = file_stream.read().decode('utf-8', errors='ignore')
        
        root = ET.fromstring(mscx_content)
        measures = root.findall(".//Measure")
        if not measures:
            measures = [elem for elem in root.iter() if elem.tag.lower() == 'measure']
            
        if not measures:
            return f"⚠️ [SKIPPED] No musical measures detected in {filename}"
        
        file_errors = []
        total_verses_found = 0
        verse_marker_indices = {}
        coordinate_profiles = {}
        
        # Step 1: Map verse text landmarks and positions
        for idx, measure in enumerate(measures):
            text_nodes = measure.findall(".//StaffText") + measure.findall(".//Text") + measure.findall(".//RehearsalMark")
            for node in text_nodes:
                text_elem = node.find("text")
                text_val = "".join(node.itertext()).strip() if text_elem is None else (text_elem.text or "").strip()
                
                words = text_val.split()
                if words:
                    first_token = words[0]
                    if re.match(r'^\d+', first_token):
                        verse_marker_indices[idx] = text_val
                        total_verses_found += 1
                        
                        # --- 2D COORDINATE EXTRACTION ---
                        pos_x = node.find(".//pos/x") if node.find(".//pos/x") is not None else node.find("pos/x")
                        pos_y = node.find(".//pos/y") if node.find(".//pos/y") is not None else node.find("pos/y")
                        
                        x_val = float(pos_x.text) if pos_x is not None else 0.0
                        y_val = float(pos_y.text) if pos_y is not None else 0.0
                        
                        coord_key = (x_val, y_val)
                        if coord_key not in coordinate_profiles:
                            coordinate_profiles[coord_key] = []
                        coordinate_profiles[coord_key].append((idx + 1, text_val))
                        break

        # Step 2: Run Timeline Verification Walk + Break Checks
        active_verse_label = "Start of Score"
        
        for idx, measure in enumerate(measures):
            if idx in verse_marker_indices:
                active_verse_label = verse_marker_indices[idx]
                
            musical_elements = [el for el in measure.iter() if el.tag.lower() in ['chord', 'rest']]
            has_rest_here = any(el.tag.lower() == 'rest' for el in musical_elements)
            
            layout_break = measure.find(".//LayoutBreak")
            subtype = measure.find(".//LayoutBreak/subtype")
            
            if layout_break is None:
                layout_break = next((el for el in measure if el.tag.lower() == 'layoutbreak'), None)
                if layout_break is not None:
                    subtype = next((child for child in layout_break if child.tag.lower() == 'subtype'), None)

            subtype_text = subtype.text.strip().lower() if subtype is not None and subtype.text else ""
            has_valid_layout_break = (layout_break is not None) and (subtype_text in ["line", "page"])
            
            if has_rest_here:
                is_at_end_of_score = (idx == len(measures) - 1)
                is_followed_by_new_verse = (idx + 1) in verse_marker_indices
                
                if is_at_end_of_score:
                    file_errors.append(f"   ↳ Extra trailing rest found at the absolute end of the file (Verse [{active_verse_label}])")
                elif not is_followed_by_new_verse:
                    file_errors.append(
                        f"   ↳ Misplaced internal rest found inside Verse [{active_verse_label}] "
                        f"(Absolute bar index: {idx + 1}). It is not followed by a new verse marker."
                    )
                else:
                    if not has_valid_layout_break:
                        file_errors.append(
                            f"   ↳ MISSING SYSTEM BREAK: Measure {idx + 1} (End of Verse [{active_verse_label}]) "
                            f"has its rest but is missing its formatting line/page break tag."
                        )
            else:
                is_followed_by_new_verse = (idx + 1) in verse_marker_indices
                if is_followed_by_new_verse:
                    next_verse_label = verse_marker_indices[idx + 1]
                    file_errors.append(
                        f"   ↳ Missing cadential rest at the end of Verse [{active_verse_label}] "
                        f"(Absolute bar index: {idx + 1}, immediately before Verse [{next_verse_label}])"
                    )

        # Step 3: Parse Alignment Deviations
        alignment_issues = []
        if len(coordinate_profiles) > 1:
            baseline_coords = max(coordinate_profiles, key=lambda k: len(coordinate_profiles[k]))
            for coords, tracking_list in coordinate_profiles.items():
                if coords == baseline_coords:
                    continue
                for m_idx, v_str in tracking_list:
                    clean_v = v_str.replace('\n', ' ').strip()
                    short_v = clean_v[:30] + "..." if len(clean_v) > 30 else clean_v
                    alignment_issues.append(
                        f"   ↳ TEXT ALIGNMENT WARNING: Verse [{short_v}] at Measure {m_idx} has custom coordinates "
                        f"X: {coords[0]}, Y: {coords[1]} (Expected baseline standard: X: {baseline_coords[0]}, Y: {baseline_coords[1]})"
                    )

        if not file_errors and not alignment_issues:
         #   print(f"✅ {display_path:<60} | Verses Tracked: {total_verses_found:<3} | Perfect Layout")
            return True
        else:
            print(f"❌ {display_path:<60} | Verses Tracked: {total_verses_found:<3} | Issues Found:")
            for err in file_errors:
                print(err)
            for align_err in alignment_issues:
                print(align_err)
            return False
            
    except Exception as e:
        import traceback
        print(f"💥 {filename:<60} | Processing crash: {e}")
        traceback.print_exc()
        return False

def run_restricted_batch():
    print("=" * 115)
    print("AUTOMATED VERSE VALIDATION & ALIGNMENT INSPECTOR: DEEP RECURSIVE SCALE")
    print("=" * 115)
    
    # 1. Get the complex EPUB file name sitting in your Input folder
    if not INPUT_DIR.exists():
        print(f"❌ ERROR: Input folder {INPUT_DIR} does not exist.")
        return
    
    epubs = list(INPUT_DIR.glob("*.epub"))
    if not epubs:
        print(f"⚠️ No active .epub found inside {INPUT_DIR} to verify.")
        return
    
    # Use the first active epub (e.g., "The Five Scrolls - D. Robert MacDonald.epub")
    epub_stem = epubs[0].stem
    print(f"🎯 Active EPUB Detected: '{epub_stem}'")

    # 2. Extract a smart match token (e.g., "The Five Scrolls" or "The Twelve")
    # If there is a hyphen, split there; otherwise clean up the text string
    if " - " in epub_stem:
        book_match_token = epub_stem.split(" - ")[0].strip().lower()
    else:
        book_match_token = epub_stem.strip().lower()

    print(f"🔍 Deep searching GitHub for music scores matching volume token: '{book_match_token}'...")
    
    # 3. Use rglob to find all .mscz files regardless of how deep they are nested
    all_mscz_files = []
    for mscz_path in MUSIC_SCORES_BASE.rglob("*.mscz"):
        # Skip backup and tool directories safely
        if "_PRE_PATCH_BACKUP" in mscz_path.parts or "analysis_scripts" in mscz_path.parts:
            continue
            
        # Get the relative path starting from inside your \musicscores folder
        rel_path_str = str(mscz_path.relative_to(MUSIC_SCORES_BASE)).lower()
        
        # If the file path contains "the twelve", "the five scrolls", etc., it belongs to this run!
        if book_match_token in rel_path_str:
            all_mscz_files.append(mscz_path)
            
    if not all_mscz_files:
        print(f"🔍 No targeted .mscz files discovered matching volume token '{book_match_token}'.")
        print(f"   Searched globally inside: {MUSIC_SCORES_BASE}")
        return
        
    print(f"✅ Found {len(all_mscz_files)} file(s) for active volume segment. Processing verification...\n")
    print("-" * 115)
    
    failures = 0
    # Sort the Path objects cleanly before running the loops
    for full_path in sorted(all_mscz_files):
        relative_display = os.path.relpath(full_path, MUSIC_SCORES_BASE)
        success = verify_single_file(str(full_path), relative_display)
        if success is False:
            failures += 1
            
    print("-" * 115)
    print(f"RESTRICTED SCAN COMPLETE. Files requiring review: {failures} / {len(all_mscz_files)}")
    print("=" * 115)

if __name__ == "__main__":
    run_restricted_batch()
