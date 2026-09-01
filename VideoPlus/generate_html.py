import csv
import re

def build_accurate_html_directory(csv_filename, output_html_filename):
    # Fixed base URL matching your exact item structure
    base_url = "https://archive.org"
    
    # Chronological grouping maps
    categories = {
        'Torah': ['GENESIS', 'EXODUS', 'NUMBERS', 'DEUTERONOMY'],
        'Prophets': ['2 SAMUEL', '2 KINGS', 'ISAIAH', 'EZEKIEL', 'AMOS'],
        'Writings': ['PSALMS', 'SONG', 'RUTH', 'LAMENTATIONS', 'ECCLESIASTES', 'ESTHER', '1 CHRONICLES']
    }
    
    categorized_data = {'Torah': [], 'Prophets': [], 'Writings': [], 'Miscellaneous': []}

    with open(csv_filename, mode='r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or not any(row):
                continue
                
            raw_ref = row[0].strip()
            folder_path = row[1].strip() if len(row) > 1 else ""
            track_name = row[2].strip() if len(row) > 2 else ""
            
            # Filter out all WMV videos
            if raw_ref.upper().endswith('.WMV') or track_name.upper().endswith('.WMV'):
                continue
                
            if not raw_ref:
                continue

            # Determine category section
            assigned_bucket = 'Miscellaneous'
            matched_key = None
            
            for section, keywords in categories.items():
                for kw in keywords:
                    if raw_ref.upper().startswith(kw):
                        assigned_bucket = section
                        matched_key = kw
                        break
                if matched_key:
                    break

            # Clean the reference label text
            if matched_key:
                clean_ref = raw_ref.replace('.MP3', '').replace('.mp3', '').strip()
            else:
                clean_ref = re.sub(r'\.MP3$', '', raw_ref, flags=re.IGNORECASE)

            # Reconstruct folder paths using forward slashes
            clean_folder = folder_path.replace('\\\\', '/').replace('\\', '/').strip('/')
            
            if clean_folder and track_name:
                full_path = f"/{clean_folder}/{track_name}"
            else:
                full_path = f"/{track_name}" if track_name else f"/{raw_ref}"
            
            # Archive Specific Encoding rule: Convert spaces to '+' instead of '%20'
            archive_encoded_path = full_path.replace(" ", "+")
            final_link = f"{base_url}{archive_encoded_path}"

            categorized_data[assigned_bucket].append({
                'ref': clean_ref,
                'file': track_name if track_name else raw_ref,
                'link': final_link
            })

    # Assemble HTML Output Document Layout Strings
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Biblical Chant Performance Library</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 20px; color: #24292e; }
        h1 { border-bottom: 1px solid #eaecef; padding-bottom: 10px; }
        h2 { margin-top: 30px; color: #0366d6; border-bottom: 1px solid #eaecef; padding-bottom: 5px; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; margin-bottom: 40px; }
        th, td { padding: 10px; border: 1px solid #dfe2e5; text-align: left; }
        th { background-color: #f6f8fa; font-weight: 600; }
        tr:nth-child(even) { background-color: #f8f9fa; }
        a { color: #0366d6; text-decoration: none; font-weight: bold; }
        a:hover { text-decoration: underline; }
        .jump-menu { background: #f1f8ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #c8e1ff; }
    </style>
</head>
<body>

    <h1>🎼 Biblical Chant Performance Directory</h1>
    <p>A static lookup index pointing exclusively to audio performances mapped via the live archive catalog storage layer.</p>

    <div class="jump-menu">
        <strong>⚡ Quick Scroll Navigation:</strong> 
        <a href="#torah">Pentateuch (Torah)</a> | 
        <a href="#prophets">Prophets (Nevi'im)</a> | 
        <a href="#scrolls">Writings & Scrolls (Ketuvim)</a> |
        <a href="#misc">Miscellaneous Broadcasts</a>
    </div>
"""

    sections_mapping = [
        ('torah', 'Torah', '📜 Pentateuch (Torah)'),
        ('prophets', 'Prophets', '👑 Historical Books & Prophets (Nevi\'im)'),
        ('scrolls', 'Writings', '🎼 Poetic Books & Scrolls (Ketuvim)'),
        ('misc', 'Miscellaneous', '📻 Miscellaneous Tracks & Radio Promos')
    ]

    for element_id, key, title in sections_mapping:
        records = categorized_data[key]
        if not records:
            continue
            
        html_content += f'    <h2 id="{element_id}">{title}</h2>\n'
        html_content += '    <table>\n        <thead>\n            <tr>\n                <th>Biblical Reference</th>\n                <th>Track Description</th>\n                <th>Performance Direct Link</th>\n            </tr>\n        </thead>\n        <tbody>\n'
        
        for item in records:
            html_content += f'            <tr>\n                <td><strong>{item["ref"]}</strong></td>\n                <td>{item["file"]}</td>\n                <td><a href="{item["link"]}" target="_blank">Listen on Archive.org ↗</a></td>\n            </tr>\n'
            
        html_content += '        </tbody>\n    </table>\n\n'

    html_content += "</body>\n</html>"

    with open(output_html_filename, mode='w', encoding='utf-8') as out_f:
        out_f.write(html_content)

    print(f"Success! {output_html_filename} compiled with exact player link formats.")

# Run the generator
build_accurate_html_directory("spreadsheet.csv", "PERFORMANCES.html")
