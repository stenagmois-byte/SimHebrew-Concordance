import re
import zipfile
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
INPUT_DIR = Path(r"C:/Users/Bob/KindleProject/Input")

def check_epub_sequences():
    print("=" * 95)
    print("EPUB CHAPTER SEQUENCE INTEGRITY CHECKER (CALIBRE STRIPPED VERSION)")
    print("=" * 95)
    
    if not INPUT_DIR.exists():
        print(f"❌ ERROR: Input folder {INPUT_DIR} does not exist.")
        return
    
    epubs = list(INPUT_DIR.glob("*.epub"))
    if not epubs:
        print(f"⚠️ No .epub files found inside {INPUT_DIR} to verify.")
        return
        
    print(f"📦 Found {len(epubs)} EPUB file(s) to scan.\n")
    
    total_failures = 0

    for epub_path in sorted(epubs):
        print(f"📖 Scanning: {epub_path.name}")
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                html_files = [f for f in archive.namelist() if f.lower().endswith(('.html', '.xhtml'))]
            
            book_chapters = {}
            
            for file_path in html_files:
                filename = Path(file_path).name  # Extract just the file name
                
                # 1. Clean up Calibre suffix metadata if it leaked into the internal file names
                clean_filename = re.sub(r"\s*-\s*D\.\s*Robert\s*MacDonald", "", filename, flags=re.IGNORECASE)
                
                # 2. Match complex prefixes (e.g., '1-Samuel', 'The Psalms', 'Jeremiah') followed by the chapter number
                # Looks for: [Book Name] [Separator] [Digits] .html
                match = re.match(r"^(.+?)[-\s_](\d+)\.(html|xhtml)$", clean_filename, re.IGNORECASE)
                
                if match:
                    book_name = match.group(1).strip()
                    chapter_num = int(match.group(2))
                    
                    if book_name not in book_chapters:
                        book_chapters[book_name] = []
                    book_chapters[book_name].append(chapter_num)

            if not book_chapters:
                print("   ⚠️ No matching 'Book-Chapter.html' patterns found. Check if files use a completely different naming format.")
                print("-" * 95)
                continue

            epub_has_issue = False
            
            # Validate sequences per distinct book group found inside this volume
            for book, chapters in book_chapters.items():
                chapters.sort()
                
                # Check for duplicate chapter file entries
                duplicates = set([ch for ch in chapters if chapters.count(ch) > 1])
                if duplicates:
                    epub_has_issue = True
                    print(f"   ❌ DUPLICATE CHAPTERS: [{book}] has multiple files for chapters: {list(duplicates)}")

                # Check for skipped integers in the sequence map
                if chapters:
                    start_ch = chapters[0]
                    end_ch = chapters[-1]
                    expected_sequence = list(range(start_ch, end_ch + 1))
                    
                    missing_chapters = [ch for ch in expected_sequence if ch not in chapters]
                    if missing_chapters:
                        epub_has_issue = True
                        print(f"   ❌ SEQUENCE BREAK: [{book}] jumps unevenly from chapter {start_ch} to {end_ch}.")
                        print(f"      Missing expected chapter files: {missing_chapters}")
                        
                    if start_ch != 1:
                        print(f"   ⚠️ NOTE: [{book}] sequence initializes at chapter {start_ch} instead of 1.")

            if not epub_has_issue:
                print("   ✅ Perfect chapter sequence.")
            else:
                total_failures += 1
                
        except Exception as e:
            print(f"   💥 Crash analyzing archive: {e}")
            total_failures += 1
            
        print("-" * 95)

    print(f"SCAN COMPLETE. EPUBs with sequence anomalies: {total_failures} / {len(epubs)}")
    print("=" * 95)

if __name__ == "__main__":
    check_epub_sequences()
