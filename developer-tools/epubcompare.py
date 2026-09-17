import difflib
import re
import zipfile
from pathlib import Path

# 1. Define paths to both files
# Ensure the Calibre Library path matches your local setup if your active folder name varies
CALIBRE_LIB_PATH = Path(r"C:\Users\Bob\KindleProject\Input\Genesis - D. Robert MacDonald.epub") 
ICLOUD_ARCHIVE_PATH = Path(r"J:\Calibre Library\D. Robert MacDonald\Genesis (124)\Genesis - D. Robert MacDonald.epub")

def clean_and_stream_html(zip_ref, internal_path):
    """Reads an internal HTML file from a zip, skipping heavy SVG tags to isolate text differences."""
    cleaned_lines = []
    with zip_ref.open(internal_path) as f:
        # Decode ignoring binary/anomalous characters safely
        content = f.read().decode('utf-8', errors='ignore')
        
        for line in content.splitlines():
            stripped = line.strip()
            # Skip massive inline SVG vector nodes, matrices, paths, and points
            if any(marker in stripped.lower() for marker in ["<path", "<svg", "<g", "d=", "m=", "polygon", "points="]):
                continue
            if stripped:
                cleaned_lines.append(stripped)
    return cleaned_lines

def compare_epubs():
    if not CALIBRE_LIB_PATH.exists():
        print(f"Error: Active file not found at:\n{CALIBRE_LIB_PATH}")
        return
    if not ICLOUD_ARCHIVE_PATH.exists():
        print(f"Error: iCloud backup file not found at:\n{ICLOUD_ARCHIVE_PATH}")
        return

    print("Analyzing and comparing EPUB text archives...")
    print(f"  [Active Workspace]: {CALIBRE_LIB_PATH.name}")
    print(f"  [iCloud Backup   ]: {ICLOUD_ARCHIVE_PATH.name}\n")

    # Open both zipped EPUB files simultaneously
    with zipfile.ZipFile(CALIBRE_LIB_PATH, 'r') as active_zip, \
         zipfile.ZipFile(ICLOUD_ARCHIVE_PATH, 'r') as icloud_zip:
         
        # Gather all internal file names
        active_files = set(active_zip.namelist())
        icloud_files = set(icloud_zip.namelist())
        
        # Check if any chapters exist in one but not the other
        missing_in_icloud = active_files - icloud_files
        missing_in_active = icloud_files - active_files
        
        if missing_in_icloud:
            print(f"Notice: Files present in workspace but missing in iCloud: {missing_in_icloud}")
        if missing_in_active:
            print(f"Notice: Files present in iCloud but missing in workspace: {missing_in_active}")

        # Target only files that exist in both, filtering down to HTML/XHTML components
        common_chapters = sorted([
            f for f in active_files & icloud_files 
            if Path(f).suffix in ['.html', '.xhtml']
        ])

        total_changes_found = 0

        for internal_path in common_chapters:
            filename = Path(internal_path).name
            
            # Extract clean, SVG-free text lines from both archives
            active_lines = clean_and_stream_html(active_zip, internal_path)
            icloud_lines = clean_and_stream_html(icloud_zip, internal_path)

            # Generate standard unified difference stream
            diff = difflib.unified_diff(
                icloud_lines,    # Original state (From iCloud)
                active_lines,    # New state (Your workspace)
                fromfile=f"iCloud/{filename}",
                tofile=f"Active/{filename}",
                lineterm="",
                n=1              # Shows 1 line of unchanged text around modifications for brief context
            )

            diff_list = list(diff)
            if diff_list:
                total_changes_found += len(diff_list)
                print(f"\n==================================================")
                print(f" DIFFERENCES DETECTED IN: {filename}")
                print(f"==================================================")
                for line in diff_list:
                    print(line)

        if total_changes_found == 0:
            print("✨ Match verified! Text strings, verse properties, and headers are identical between both directories.")
        else:
            print(f"\nComparison processing complete. Found structural differences across the chapters.")

if __name__ == "__main__":
    import sys
    # Force the standard output stream to use UTF-8 instead of system cp1252
    sys.stdout.reconfigure(encoding='utf-8') 
    
    compare_epubs()