import os
import shutil
import zipfile
from pathlib import Path

# Define directories
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
DOWNLOAD_DIR = Path(r"C:\Users\Bob\Downloads")

# Mapping short file prefixes to full formal book names for the H1 tag
BOOK_NAMES = {
    "Job": "The Book of Job",
    "Song": "The Song of Songs",
    "Ruth": "The Book of Ruth",
    "Lam": "The Book of Lamentations",
    "Eccl": "The Book of Ecclesiastes",
    "Esther": "The Book of Esther",
    "Hos": "Hosea",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obad": "Obadiah",
    "Jonah": "Jonah",
    "Mic": "Micah",
    "Nah": "Nahum",
    "Hab": "Habakkuk",
    "Zeph": "Zechariah",
    "Hag": "Haggai",
    "Zech": "Zechariah",
    "Mal": "Malachi"
    # Add any other prefixes here if needed (e.g., "1_SAMUEL", "2_KINGS")
}

def sync_h4_headings_and_inject_h1():
    # Find the single EPUB in the Input directory
    epub_files = list(INPUT_DIR.glob("*.epub"))
    
    if not epub_files:
        print("No EPUB file found in the Input directory.")
        return
    if len(epub_files) > 1:
        print("Multiple EPUB files found. Please leave only one file to process.")
        return
        
    epub_path = epub_files[0]
    print(f"Syncing headings for eBook: {epub_path.name}")
    
    temp_extract_dir = INPUT_DIR / "temp_extracted_epub"
    backup_epub_path = epub_path.with_suffix(".epub.bak")
    
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)

    # 1. Backup and extract the current production EPUB
    shutil.copy2(epub_path, backup_epub_path)
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)

    try:
        # 2. Iterate through files inside the EPUB archive
        for html_file_path in temp_extract_dir.rglob("*"):
            if html_file_path.suffix not in ['.html', '.xhtml']:
                continue
                
            file_name = html_file_path.name
            name_parts = html_file_path.stem.split('-')
            
            # Match only target chapter files formatted like: bookname-nnn.html
            if len(name_parts) < 2 or not name_parts[-1].isdigit():
                continue

            book_prefix = name_parts[0]            # e.g., "Job"
            chapter_num = int(name_parts[-1])      # e.g., 1

            downloaded_file_path = DOWNLOAD_DIR / file_name

            # Skip if there is no corresponding new file in downloads folder
            if not downloaded_file_path.exists():
                print(f"  Skipping: No matching download file found for {file_name}")
                continue

            print(f"  Syncing H4 headings in Chapter: {file_name}")

            # Read the original file to isolate your carefully hand-written H4 tag set
            with open(html_file_path, "r", encoding="utf-8") as f:
                original_text = f.read()

            h4_start_idx = original_text.find('<h4 class="other-head"')
            if h4_start_idx == -1:
                print(f"    Warning: <h4 class='other-head'> not found in original {file_name}. Skipping copy.")
                continue
                
            h4_end_idx = original_text.find('</h4>', h4_start_idx) + len('</h4>')
            exact_old_h4_string = original_text[h4_start_idx:h4_end_idx]

            # Read the fresh new downloaded file
            with open(downloaded_file_path, "r", encoding="utf-8") as f:
                new_file_text = f.read()

            # Find the new, generic H4 tag set inside the downloaded file to replace it
            new_h4_start_idx = new_file_text.find('<h4 class="other-head"')
            if new_h4_start_idx != -1:
                new_h4_end_idx = new_file_text.find('</h4>', new_h4_start_idx) + len('</h4>')
                exact_new_h4_string = new_file_text[new_h4_start_idx:new_h4_end_idx]
                
                # Replace the generic H4 with your custom hand-made H4 text block directly
                modified_html_text = new_file_text.replace(exact_new_h4_string, exact_old_h4_string)
            else:
                print(f"    Warning: <h4 class='other-head'> not found in incoming download {file_name}.")
                modified_html_text = new_file_text

            # --- DYNAMIC CHAPTER 1 H1 INJECTION ---
            if chapter_num == 1:
                # Double-check if H1 is already there to avoid duplicate formatting loops
                if modified_html_text.find('<h1 class="nopageafter"') == -1:
                    full_book_name = BOOK_NAMES.get(book_prefix, book_prefix)
                    correct_h1 = f'<h1 class="nopageafter" id="{book_prefix}-000">{full_book_name}</h1>'
                    
                    body_idx = modified_html_text.find('<body>')
                    if body_idx != -1:
                        print(f"    -> Injecting H1 header for Chapter 1 into {file_name}")
                        insert_point = body_idx + len('<body>')
                        modified_html_text = (
                            modified_html_text[:insert_point] + 
                            "\n  " + correct_h1 + 
                            modified_html_text[insert_point:]
                        )

            # Overwrite the internal file with the perfectly merged text string
            with open(html_file_path, "w", encoding="utf-8") as f:
                f.write(modified_html_text)

        # 3. Re-zip the modified tree folder structure back into the clean EPUB file path
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zip_write:
            for root, dirs, files in os.walk(temp_extract_dir):
                for file in files:
                    full_path = Path(root) / file
                    archive_name = full_path.relative_to(temp_extract_dir)
                    zip_write.write(full_path, archive_name)
                    
        print(f"\nSuccessfully processed file syncs and additions for: {epub_path.name}")
        if backup_epub_path.exists():
            os.remove(backup_epub_path)
            
    except Exception as e:
        print(f"An error occurred during editing operations: {e}")
        print("Restoring pristine archive backup file...")
        shutil.copy2(backup_epub_path, epub_path)
        
    finally:
        # Clean up files completely
        if temp_extract_dir.exists():
            shutil.rmtree(temp_extract_dir)
        if backup_epub_path.exists():
            try:
                os.remove(backup_epub_path)
            except FileNotFoundError:
                pass

if __name__ == "__main__":
    sync_h4_headings_and_inject_h1()
