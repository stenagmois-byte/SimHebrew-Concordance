import os
import zipfile
import shutil
from pathlib import Path

# Definitive Path Mapping
EPUB_INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
GITHUB_MUSIC_DIR = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores")

def run_volume_svg_injector():
    print("=" * 115)
    print("EPUB ASSISTANT: PRODUCTION WORKSPACE INJECTOR (FLEXIBLE NAME SCAN)")
    print("=" * 115)
    
    if not EPUB_INPUT_DIR.exists():
        print(f"🚨 Production input folder not found at: {EPUB_INPUT_DIR}")
        return

    # Step 1: Scan GitHub workspace for active SVG files waiting for deployment
    staged_svgs_by_volume = {}
    print("Scanning GitHub repository for staged, renamed SVG files...")
    for svg_path in GITHUB_MUSIC_DIR.rglob("*.svg"):
        relative_parts = svg_path.relative_to(GITHUB_MUSIC_DIR).parts
        if relative_parts:
            volume_name = relative_parts[0]  # e.g., "The Twelve"
            if volume_name not in staged_svgs_by_volume:
                staged_svgs_by_volume[volume_name] = []
            staged_svgs_by_volume[volume_name].append(svg_path)
            
    if not staged_svgs_by_volume:
        print("🟢 No staged SVG files found anywhere in the GitHub musicscores directory. Nothing to do!")
        return

    # Step 2: Match staged volumes against EPUB files in your Kindle Input folder
    epub_files = list(EPUB_INPUT_DIR.glob("*.epub"))
    print(f"Found {len(epub_files)} template EPUB files in staging input folder.\n")
    
    for epub_path in epub_files:
        epub_name_base = epub_path.stem  # e.g., "The Twelve - D. Robert MacDonald"
        
        # Find if ANY of our active GitHub folder names exist inside this EPUB filename string
        matched_volume_folder = None
        for volume_folder in staged_svgs_by_volume.keys():
            if volume_folder.lower() in epub_name_base.lower():
                matched_volume_folder = volume_folder
                break
                
        # RULE: If no staged SVG folder matches this EPUB name, skip completely!
        if matched_volume_folder is None:
            print(f" ⏭️ [Skipping] {epub_path.name} (No matching staged SVGs found in GitHub folders)")
            continue
            
        active_svgs = staged_svgs_by_volume[matched_volume_folder]
        print(f" ⚙️ [Processing Volume] {epub_path.name} -> Deploying {len(active_svgs)} updated score sheets from '{matched_volume_folder}'...")
        
        # Create a clean temporary directory to unpack the EPUB container
        temp_extract_dir = EPUB_INPUT_DIR / f"temp_extract_{matched_volume_folder}"
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        os.makedirs(temp_extract_dir, exist_ok=True)
        
        try:
            # Unzip EPUB container into memory workspace
            with zipfile.ZipFile(epub_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
                
            injections_made = 0
            
            # Step 3: Surgically locate and replace the targets inside the EPUB asset tree
            for svg_src_path in active_svgs:
                filename = svg_src_path.name
                file_injected = False
                
                # Search the unzipped EPUB for the old file matching this exact name
                target_dest_paths = list(temp_extract_dir.rglob(filename))
                if target_dest_paths:
                    for target_dest in target_dest_paths:
                        shutil.copy2(svg_src_path, target_dest)
                    file_injected = True
                else:
                    # Fallback if it's a completely new page layout name
                    images_folders = [d for d in temp_extract_dir.rglob("*") if d.is_dir() and d.name.lower() in ["images", "image", "media"]]
                    if images_folders:
                        shutil.copy2(svg_src_path, images_folders[0] / filename)
                        file_injected = True
                
                # FIX: Increment counter exactly once per successful unique source file processed
                if file_injected:
                    injections_made += 1

            # Step 4: Re-compile the updated files back into a pristine compressed EPUB archive
            if injections_made > 0:
                final_epub_path = epub_path
                temp_zip_path = epub_path.with_suffix(".epub.tmp")
                
                with zipfile.ZipFile(temp_zip_path, 'w', zipfile.ZIP_DEFLATED) as epub_zip:
                    mimetype_path = temp_extract_dir / "mimetype"
                    if mimetype_path.exists():
                        epub_zip.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
                        
                    for root, _, files in os.walk(temp_extract_dir):
                        for file in files:
                            full_file = Path(root) / file
                            rel_file = full_file.relative_to(temp_extract_dir)
                            if rel_file.as_posix() == "mimetype":
                                continue
                            epub_zip.write(full_file, rel_file.as_posix())
                            
                # Safely commit swap to disk
                os.remove(final_epub_path)
                os.rename(temp_zip_path, final_epub_path)
                print(f" ✅ [Success] Successfully injected and compiled {injections_made} SVGs into {epub_path.name}")
                
                # Step 5: Clean House - Delete the processed SVGs from GitHub so they don't deploy twice
                for svg_src_path in active_svgs:
                    try:
                        svg_src_path.unlink()
                    except Exception:
                        pass
                print(f" 🧹 [Cleared] Cleaned staging SVGs out of GitHub repository directory.")
            else:
                print(" ⚠️ No asset matches found inside the internal EPUB framework.")
                
        except Exception as e:
            print(f" 🚨 [Compilation Failure] Processing aborted for {epub_path.name}: {e}")
        finally:
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
                
    print("\n" + "=" * 115)
    print("WORKFLOW COMPLETE. Your staging folders are clean and target files are updated!")
    print("=" * 115)

if __name__ == "__main__":
    run_volume_svg_injector()
