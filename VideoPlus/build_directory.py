import csv
import re
import urllib.parse

def convert_spreadsheet_to_markdown(csv_filename, output_md_filename):
    # Internet Archive base folder identifier for the Biblical Chant Library
    base_url = "https://archive.org/download/iconea2008_202508/"
    
    # Chronological grouping maps for organized structural headings
    book_headers = {
        'GENESIS': ('📜 Pentateuch (Torah)', 'Genesis'),
        'EXODUS': ('📜 Pentateuch (Torah)', 'Exodus'),
        'NUMBERS': ('📜 Pentateuch (Torah)', 'Numbers'),
        'DEUTERONOMY': ('📜 Pentateuch (Torah)', 'Deuteronomy'),
        '2 SAMUEL': ('👑 Historical Books & Prophets (Nevi\'im)', '2 Samuel'),
        '2 KINGS': ('👑 Historical Books & Prophets (Nevi\'im)', '2 Kings'),
        'ISAIAH': ('👑 Historical Books & Prophets (Nevi\'im)', 'Isaiah'),
        'EZEKIEL': ('👑 Historical Books & Prophets (Nevi\'im)', 'Ezekiel'),
        'AMOS': ('👑 Historical Books & Prophets (Nevi\'im)', 'Amos'),
        'PSALMS': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Psalms (Tehillim)'),
        'SONG': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Song of Songs'),
        'RUTH': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Ruth'),
        'LAMENTATIONS': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Lamentations'),
        'ECCLESIASTES': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Ecclesiastes'),
        'ESTHER': ('🎼 Poetic Books & Scrolls (Ketuvim)', 'Esther'),
        '1 CHRONICLES': ('🎼 Poetic Books & Scrolls (Ketuvim)', '1 Chronicles')
    }

    data_by_group = {}

    # Read the data file cleanly while skipping empty rows
    with open(csv_filename, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not any(row):  
                continue
                
            raw_ref = row[0].strip()
            folder_path = row[1].strip() if len(row) > 1 else ""
            track_name = row[2].strip() if len(row) > 2 else ""
            
            if not raw_ref:
                continue

            # Identify which biblical book header matches our row row string
            matched_book_key = None
            for key in book_headers:
                if raw_ref.upper().startswith(key):
                    matched_book_key = key
                    break
            
            # Map tracking metadata blocks cleanly
            if matched_book_key:
                group_title, book_title = book_headers[matched_book_key]
                reference = raw_ref.replace(matched_book_key, "").strip()
                reference = re.sub(r'\.(MP3|WMV)$', '', reference, flags=re.IGNORECASE)
                if not reference:
                    reference = "Full Book Excerpts"
            else:
                group_title, book_title = ("📻 Miscellaneous Tracks & Radio Promos", "Radio Broadcasts")
                reference = re.sub(r'\.(MP3|WMV)$', '', raw_ref, flags=re.IGNORECASE)
                
            # Process subfolder paths into descriptive artist classifications
            path_parts = [p for p in folder_path.replace('\\\\', '/').replace('\\', '/').split('/') if p]
            if len(path_parts) >= 2:
                artist_album = f"{path_parts[1]} ({path_parts[2]})" if len(path_parts) > 2 else path_parts[1]
            elif len(path_parts) == 1:
                artist_album = path_parts[0]
            else:
                artist_album = "Unknown Recording"

            # Reconstruct the precise Archive URL string path with web percent-encoding
            clean_folder = folder_path.replace('\\\\', '/').replace('\\', '/').strip('/')
            full_archive_path = f"{clean_folder}/{track_name}" if track_name else clean_folder
            encoded_path = urllib.parse.quote(full_archive_path)
            performance_link = f"{base_url}{encoded_path}"

            # Structure elements sequentially into categories
            if group_title not in data_by_group:
                data_by_group[group_title] = {}
            if book_title not in data_by_group[group_title]:
                data_by_group[group_title][book_title] = []
                
            data_by_group[group_title][book_title].append([reference, artist_album, track_name, performance_link])

    # Generate the Markdown file output
    with open(output_md_filename, mode='w', encoding='utf-8') as out:
        out.write("# 🎼 Biblical Chant Performance Directory\n\n")
        out.write("This directory acts as an organized link index pointing to public file layers on the Archive.\n\n")
        
        for group, books in data_by_group.items():
            out.write(f"## {group}\n\n")
            for book, rows in books.items():
                if group != "📻 Miscellaneous Tracks & Radio Promos":
                    out.write(f"### {book}\n\n")
                
                out.write("| Reference | Album / Artist | Track Name | Performance Link |\n")
                out.write("| :--- | :--- | :--- | :--- |\n")
                for row in rows:
                    out.write(f"| {row[0]} | {row[1]} | {row[2]} | [Listen on Archive.org]({row[3]}) |\n")
                out.write("\n---\n\n")

    print(f"Success! '{output_md_filename}' has been created with all compiled rows.")

# Run the parser automatically using your files
convert_spreadsheet_to_markdown("list of available performances by book.csv", "PERFORMANCES.md")
