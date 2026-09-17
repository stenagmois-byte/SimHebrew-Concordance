from pathlib import Path
import re
import zipfile

# Define directory where your completed EPUBs sit
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
OUTPUT_SQL = INPUT_DIR / "update_dgmtext_svg_counts.sql"

# Mapping of the EPUB file names to the specific book codes allowed in that volume.
VOLUME_BOOK_FILTER = {
    "The Book of Job.epub": {"JOB"},
    "The Five Scrolls.epub": {"SONG", "RUTH", "LAM", "ECCL", "ESTHER"},
    "The Twelve.epub": {"HOS", "JOEL", "AMOS", "OBAD", "JONAH", "MIC", "NAH", "HAB", "ZEPH", "HAG", "ZECH", "MAL"},
    "Samuel.epub": {"1_SAMUEL", "2_SAMUEL"},
    "Kings.epub": {"1_KINGS", "2_KINGS"},
    "Chronicles.epub": {"1_CHRON", "2_CHRON"}
}

def analyze_and_generate_sql_updates():
    epub_files = list(INPUT_DIR.glob("*.epub"))
    if not epub_files:
        print("No EPUB files found in the Input directory.")
        return

    # Master tracking dictionary: counts[book_cd][chapter_cd][verse_cd] = set of sequences
    verse_sequences = {}

    # Pattern to handle codes starting with numbers separated by a hyphen or underscore
    svg_pattern = re.compile(r'((?:\d[-_])?[A-Za-z]+)-(\d{3})-(\d+)(?:-(\d+))?\.svg$', re.IGNORECASE)

    for epub_path in epub_files:
        epub_name = epub_path.name
        allowed_books = VOLUME_BOOK_FILTER.get(epub_name)

        if allowed_books is None:
            print(f"Processing generic volume: {epub_name} (Extracting all books)")
        else:
            print(f"Processing structured volume: {epub_name} (Filtering for: {', '.join(allowed_books)})")

        with zipfile.ZipFile(epub_path, 'r') as zip_ref:
            for internal_file_path in zip_ref.namelist():
                filename = Path(internal_file_path).name
                match = svg_pattern.search(filename)
                
                if match:
                    # Normalize code formatting (e.g., "2-SAMUEL" -> "2_SAMUEL")
                    book_cd = match.group(1).replace('-', '_').upper()
                    
                    # Apply boundary cross-reference filter rule
                    if allowed_books is not None and book_cd not in allowed_books:
                        continue
                        
                    # Format as 3-character strings with high-order zeros (e.g., "001")
                    chapter_cd = f"{int(match.group(2)):03d}"
                    verse_cd = f"{int(match.group(3)):03d}"
                    
                    sequence_str = match.group(4)
                    sequence_num = int(sequence_str) if sequence_str else 1
                    
                    # Initialize dictionary maps securely
                    if book_cd not in verse_sequences:
                        verse_sequences[book_cd] = {}
                    if chapter_cd not in verse_sequences[book_cd]:
                        verse_sequences[book_cd][chapter_cd] = {}
                    if verse_cd not in verse_sequences[book_cd][chapter_cd]:
                        verse_sequences[book_cd][chapter_cd][verse_cd] = set()
                        
                    verse_sequences[book_cd][chapter_cd][verse_cd].add(sequence_num)

    # Begin compiling the pure Oracle SQL Update payload
    sql_lines = [
        "-- Oracle Database In-Place Update Script",
        "-- Generated automatically from EPUB manifest counts",
        "SET DEFINE OFF;",
        "",
        "-- Suppress audit trigger processing dynamically before starting batch execution",
        "ALTER TABLE DGMTEXT DISABLE ALL TRIGGERS;\n"
    ]

    # Generate isolated SQL Update statements sequentially
    for book_cd in sorted(verse_sequences.keys()):
        for chapter_cd in sorted(verse_sequences[book_cd].keys()):
            for verse_cd in sorted(verse_sequences[book_cd][chapter_cd].keys()):
                svg_count = len(verse_sequences[book_cd][chapter_cd][verse_cd])
                
                # Format update using text matching strings padded with high order zeros
                sql_update = (
                    f"UPDATE DGMTEXT SET SVG_COUNT = {svg_count} "
                    f"WHERE book_cd = '{book_cd}' "
                    f"AND chapter_cd = '{chapter_cd}' "
                    f"AND verse_cd = '{verse_cd}';"
                )
                sql_lines.append(sql_update)

    sql_lines.append("\n-- Re-enable audit triggers post operational tracking run")
    sql_lines.append("ALTER TABLE DGMTEXT ENABLE ALL TRIGGERS;")
    sql_lines.append("\nCOMMIT;")
    sql_lines.append("/")

    with open(OUTPUT_SQL, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sql_lines))

    print(f"\nSuccess! SQL execution updates script saved to: {OUTPUT_SQL.name}")

if __name__ == "__main__":
    analyze_and_generate_sql_updates()
