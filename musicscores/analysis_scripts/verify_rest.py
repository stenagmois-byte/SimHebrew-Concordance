import os
import zipfile
import re
import xml.etree.ElementTree as ET

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
            return f"⚠️ [SKIPPED] No musical measures detected in {filename}"
        
        file_errors = []
        total_verses_found = 0
        
        # Step 1: Pre-scan the score to map out exactly which bar indexes contain verse markers
        verse_marker_indices = {}
        active_verse_label = "Start of Score"
        
        for idx, measure in enumerate(measures):
            staff_text_nodes = measure.findall(".//StaffText/text")
            for node in staff_text_nodes:
                text_val = node.text.strip() if node.text else ""
                words = text_val.split()
                if words:
                    first_token = words[0]  # FIXED: Explicitly grabs the first string token!
                    if re.match(r'^\d+', first_token):
                        verse_marker_indices[idx] = text_val
                        total_verses_found += 1
                        break

        # Step 2: Run Timeline Verification Walk
        for idx, measure in enumerate(measures):
            if idx in verse_marker_indices:
                active_verse_label = verse_marker_indices[idx]
                
            has_rest_here = measure.find(".//Rest") is not None
            
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
                is_followed_by_new_verse = (idx + 1) in verse_marker_indices
                if is_followed_by_new_verse:
                    next_verse_label = verse_marker_indices[idx + 1]
                    file_errors.append(
                        f"   ↳ Missing cadential rest at the end of Verse [{active_verse_label}] "
                        f"(Absolute bar index: {idx + 1}, immediately before Verse [{next_verse_label}])"
                    )

        if not file_errors:
            print(f"✅ {display_path:<60} | Verses Tracked: {total_verses_found:<3} | Perfect")
            return True
        else:
            print(f"❌ {display_path:<60} | Verses Tracked: {total_verses_found:<3} | Issues Found:")
            for err in file_errors:
                print(err)
            return False
            
    except Exception as e:
        print(f"💥 {filename:<60} | Processing crash: {e}")
        return False

def run_batch_verification():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    print("=" * 115)
    print("AUTOMATED CADENTIAL REST VALIDATION ENGINE: PEEK-FORWARD LOOKUP")
    print("=" * 115)
    print(f"Base Directory: {parent_dir}\n")
    
    all_mscz_files = []
    for dirpath, _, filenames in os.walk(parent_dir):
        if "_PRE_PATCH_BACKUP" in dirpath or "analysis_scripts" in dirpath:
            continue
        for filename in filenames:
            if filename.lower().endswith('.mscz'):
                all_mscz_files.append(os.path.join(dirpath, filename))
                
    if not all_mscz_files:
        print("🔍 No .mscz files discovered. Check your directory placement.")
        return
        
    print(f"Found {len(all_mscz_files)} volumes/files to verify. Processing...\n")
    print("-" * 115)
    
    failures = 0
    for full_path in sorted(all_mscz_files):
        relative_display = os.path.relpath(full_path, parent_dir)
        success = verify_single_file(full_path, relative_display)
        if success is False:
            failures += 1
            
    print("-" * 115)
    print(f"SCAN COMPLETE. Files requiring review: {failures} / {len(all_mscz_files)}")
    print("=" * 115)

if __name__ == "__main__":
    run_batch_verification()
