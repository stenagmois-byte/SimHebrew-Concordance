import os
import re

MUSIC_DIR = "./musicscores"

# Global explicit lookup mapping to guarantee absolute canonical sequence grouping
CANONICAL_ORDERS = [
    # The Five Scrolls
    "SONG", "RUTH", "LAMENTATIONS", "QOHELET", "ESTHER",
    
    # The Twelve
    "HOSEA", "JOEL", "AMOS", "OBADIAH", "JONAH", "MICAH", 
    "NAHUM", "HABAKKUK", "ZEPHANIAH", "HAGGAI", "ZECHARIAH", "MALACHI",
    
    # Daniel-Ezra-Nehemiah
    "DANIEL", "EZRA", "NEHEMIAH",
    
    # Samuel (Adding both numeric database string and batch file alpha variants)
    "1_SAMUEL", "A_SAMUEL", "2_SAMUEL", "B_SAMUEL",
    
    # Kings
    "1_KINGS", "A_KINGS", "2_KINGS", "B_KINGS",
    
    # Chronicles
    "1_CHRONICLES", "A_CHRONICLES", "2_CHRONICLES", "B_CHRONICLES"
]

def get_sorting_tuple(filename):
    prefix_underscore = filename.replace('.json', '').upper()
    
    # 1. Isolate the numeric chapter index at the end
    match = re.search(r'_(\d+)$', prefix_underscore)
    chapter_int = int(match.group(1)) if match else 0
    
    # 2. Isolate the book text component string
    book_code_text = prefix_underscore[:match.start()] if match else prefix_underscore
        
    # Check if the filename contains any of our strict canonical tokens
    for idx, rule in enumerate(CANONICAL_ORDERS):
        if rule in book_code_text:
            return (idx, chapter_int)
            
    # Fallback default: alphabetize by file prefix text, then by chapter
    return (book_code_text, chapter_int)

def build_html_matrices():
    print("🚀 Running Subdirectory Index Compilation Engine (Universal Prefix Support)...")
    
    if not os.path.exists(MUSIC_DIR):
        print(f"Error: Cannot find '{MUSIC_DIR}' directory relative to this script.")
        return

    for root, dirs, files in os.walk(MUSIC_DIR):
        if not files:
            continue
            
        json_files = [f for f in files if f.endswith('.json')]
        if not json_files:
            continue
            
        book_name = os.path.basename(root)
        
        # Sort entirely by parsing the intrinsic file naming tokens
        json_files.sort(key=get_sorting_tuple)
        
        print(f"📊 Compiling grid array for: {book_name} ({len(json_files)} Chapters)")
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="../qstyles.css">
  <title>{book_name} - Music Scores</title>
</head>
<body>

  <div class="nav"><a href="../index.html">← Back to Volume Directory</a></div>

  <h1>{book_name}</h1>
  <p>Algorithmic database extractions, verified MuseScore notation lines, and digital cantillation contour matrix alignments.</p>

  <table class="atable">
    <thead>
      <tr>
        <td class="tdch1" style="text-align: right; padding-right: 15px;">Text Location</td>
        <td class="tdch2">MuseScore File (.mscz)</td>
        <td class="tdch3">MusicXML Data Tree</td>
        <td class="tdch4">JSON Data Tree</td>
        <td class="tdch5">Cantillation Contour Map</td>
      </tr>
    </thead>
    <tbody>"""

        current_book_context = ""

        for json_file in json_files:
            prefix_underscore = json_file.replace('.json', '')
            prefix_hyphen = prefix_underscore.replace('_', '-')
            
            match = re.search(r'_(\d+)$', prefix_underscore)
            if match:
                chapter_code = match.group(1)
                chapter_num = chapter_code.lstrip('0')
                if not chapter_num:
                    chapter_num = "0"
                isolated_book = prefix_underscore[:match.start()]
            else:
                chapter_code = ""
                chapter_num = prefix_underscore
                isolated_book = prefix_underscore

            # Clean and present display strings to the front-facing user
            if isolated_book.upper() != current_book_context.upper() or chapter_code == "001":
                current_book_context = isolated_book
                
                # Transform both alpha batch and leading numeric styles to elegant UI text
                display_label = isolated_book.upper()
                display_label = re.sub(r'^[A1]_', '1 ', display_label)
                display_label = re.sub(r'^[B2]_', '2 ', display_label)
                display_label = display_label.replace('_', ' ').title()
                
                if "Song" in display_label: 
                    display_label = "Song of Songs"
            else:
                display_label = chapter_num

            mscz_file   = f"{prefix_hyphen}.mscz"
            xml_file    = f"{prefix_hyphen}.xml"
            matrix_file = f"{prefix_underscore}_matrix.html"
            
            html_content += f"""
      <tr>
        <td class="tdcl1" style="text-align: right; padding-right: 15px; font-weight: bold;">{display_label}</td>
        <td class="tdcl2"><a href="./{mscz_file}">🎼 Download Score</a></td>
        <td class="tdcl3"><a href="./{xml_file}">💻 View XML Tree</a></td>
        <td class="tdcl4"><a href="./{json_file}">📄 View JSON</a></td>
        <td class="tdcl5"><a href="./{matrix_file}">📊 View Contour Matrix</a></td>
      </tr>"""

        html_content += """
    </tbody>
  </table>

  <footer>
    <p>Qualum Publishing · Verified via Database Extraction Engine</p>
  </footer>

  <script>
  document.addEventListener("DOMContentLoaded", () => {
      const links = document.querySelectorAll("a");
      links.forEach(link => {
          let linkText = link.textContent.trim();
          if (linkText.includes("Back") || link.closest('.nav')) return;

          const colorClass = getGematriaMenuClass(linkText);
          if (colorClass) {
              link.classList.add(colorClass);
              link.style.display = "inline-block";
              link.style.padding = "3px 8px";
              link.style.margin = "2px 2px";
              link.style.borderRadius = "4px";
              link.style.textDecoration = "none";
          }
      });
  });

  function getGematriaMenuClass(text) {
      if (!text) return '';
      let score = 0;
      for (let i = 0; i < text.length; i++) { score += text.charCodeAt(i); }
      return 'gem-' + ['low', 'mid-low', 'mid', 'mid-high', 'high'][score % 5];
  }
  </script>
</body>
</html>"""

        output_file = os.path.join(root, "index.html")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

    print("✅ Complete! All indices successfully generated in perfect sequence loops.")

if __name__ == "__main__":
    build_html_matrices()
