import json
import html
import re
from pathlib import Path

def compute_hebrew_gematria(text_string):
    """
    Computes absolute Hebrew gematria values stripped of vowels (niqqud) and teamim.
    Returns a tuple of (total_gematria, hover_breakdown_string)
    """
    gematria_table = {
        'א': 1, 'ב': 2, 'ג': 3, 'ד': 4, 'ה': 5, 'ו': 6, 'ז': 7, 'ח': 8, 'ט': 9,
        'י': 10, 'כ': 20, 'ל': 30, 'מ': 40, 'נ': 50, 'ס': 60, 'ע': 70, 'פ': 80, 'צ': 90,
        'ק': 100, 'ר': 200, 'ש': 300, 'ת': 400,
        'ך': 20, 'ם': 40, 'ן': 50, 'ף': 80, 'ץ': 90
    }
    # Strip cantillation marks, vowels, and special characters (keep pure consonants and spaces)
    clean_text = re.sub(r'[^\u05d0-\u05ea\s]', '', text_string)
    words = clean_text.split()
    
    total_score = 0
    breakdown_parts = []
    
    for word in words:
        word_sum = sum(gematria_table.get(char, 0) for char in word)
        total_score += word_sum
        if word_sum > 0:
            breakdown_parts.append(f"{word}: {word_sum}")
            
    hover_title = " + ".join(breakdown_parts) + f" = {total_score}" if breakdown_parts else "0"
    return total_score, hover_title

def generate_ornament_records_page(search_index, output_path="ornament_records-2.html"):
    """
    Generates a highly dynamic standalone HTML subpage that decodes URL query parameters
    (?ornament=revia&pitch=f) using client-side JavaScript, pulling records from a 
    pre-compiled JSON search index embedded directly inside the document.
    """
    # Load your central configuration map to guarantee directory resolution matching your server structure
    try:
        with open("book_map.json", "r", encoding="utf-8") as f:
            book_map = json.load(f)
    except FileNotFoundError:
        book_map = {}

    # Deeply inject gematria scores straight into your search index record nodes on the fly
    for orn, pitches in search_index.items():
        for pitch_lbl, records in pitches.items():
            for rec in records:
                raw_text = rec.get("t", "")
                score, breakdown = compute_hebrew_gematria(raw_text)
                rec["g_val"] = score
                rec["g_hov"] = breakdown
                
                # Fetch the uniform target volume folder string cleanly using uppercase dictionary lookups
                book_key = rec.get("b", "").upper().replace(" ", "_")
                rec["folder"] = book_map.get(book_key, rec.get("b", "").title())

    # Serialize the complete search index map securely to load natively via the browser execution client
    serialized_index = json.dumps(search_index, ensure_ascii=False)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ornament Instance Explorer — Tanach Musical Concordance</title>
    <style>
        body {{ font-family: 'Georgia', serif; margin: 40px auto; max-width: 1150px; color: #222222; line-height: 1.65; background-color: #fffcf4; padding: 0 20px; }}
        .nav {{ margin-bottom: 25px; font-family: sans-serif; font-size: 0.9rem; }}
        .nav a {{ color: #800000; text-decoration: none; font-weight: bold; }}
        .nav a:hover {{ text-decoration: underline; }}
        h1 {{ font-family: sans-serif; color: #800000; font-size: 2.2rem; margin-bottom: 5px; font-weight: normal; }}
        .subtitle {{ font-family: sans-serif; font-size: 1.1rem; color: #555; margin-bottom: 30px; }}
        .subtitle span {{ font-weight: bold; color: #800000; text-transform: uppercase; }}
        table {{ width: 100%; border-collapse: collapse; font-family: sans-serif; font-size: 0.95rem; margin: 20px 0; background-color: #ffffff; box-shadow: 0 1px 4px rgba(0,0,0,0.05); border-top: 2px solid #800000; border-bottom: 2px solid #800000; }}
        th {{ background-color: #f3f0e8; color: #800000; font-weight: bold; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.5px; padding: 12px 10px; border-bottom: 1px solid #800000; }}
        td {{ padding: 12px 10px; border-bottom: 1px solid #eaeaea; color: #444; vertical-align: middle; }}
        tr:hover {{ background-color: #fcfaf2; }}
        .source-cell {{ font-weight: bold; color: #222; width: 180px; }}
        .audio-cell {{ width: 160px; text-align: center; }}
        .gematria-cell {{ font-family: 'Georgia', serif; font-size: 1.05rem; color: #4A4A4A; cursor: help; border-bottom: 1px dotted #800000; display: inline-block; padding-bottom: 2px; width: 60px; text-align: center; }}
        .text-cell {{ direction: rtl; text-align: right; font-size: 1.35rem; font-family: 'Times New Roman', serif; font-weight: bold; padding-right: 20px; }}
        .no-records {{ padding: 40px; text-align: center; font-style: italic; color: #800000; }}
    </style>
</head>
<body>

    <div class="nav">
        <a href="index.html">← Back to Distribution Matrix</a>
    </div>

    <h1 id="pageTitle">Ornament Instance Explorer</h1>
    <div class="subtitle" id="pageSubtitle">Loading concordance parameters...</div>

    <table>
        <thead>
            <tr>
                <th style="text-align: left; padding-left: 15px;">Source Context</th>
                <th>Audio Track</th>
                <th>Gematria</th>
                <th style="text-align: right; padding-right: 20px;">Hebrew Verse Text (Sans Niqqud)</th>
            </tr>
        </thead>
        <tbody id="recordsTableBody">
            <!-- Driven Dynamically by Client Engine -->
        </tbody>
    </table>

    <script>
        // Mount the compiled deep index directly into native memory space
        const SEARCH_INDEX = {serialized_index};

        function initializeExplorer() {{
            const urlParams = new URLSearchParams(window.location.search);
            const targetOrn = (urlParams.get('ornament') || '').trim().lowerCase || (urlParams.get('ornament') || '').trim().toLowerCase();
            const targetPitch = (urlParams.get('pitch') || '').trim();

            if (!targetOrn || !targetPitch) {{
                document.getElementById('pageSubtitle').innerHTML = "⚠️ Error: Missing query arguments.";
                return;
            }}

            document.getElementById('pageTitle').innerHTML = `🔍 Concordance Records: ${{targetOrn.toUpperCase()}}`;
            document.getElementById('pageSubtitle').innerHTML = `Isolating instances matching recitation pitch structural axis: <span>${{targetPitch}}</span>`;

            const tableBody = document.getElementById('recordsTableBody');
            const pitchGroup = SEARCH_INDEX[targetOrn] || {{}};
            const records = pitchGroup[targetPitch] || [];

            if (records.length === 0) {{
                tableBody.innerHTML = `<tr><td colspan="4" class="no-records">❌ No verified instances matching this specific ornament/pitch node cross-section.</td></tr>`;
                return;
            }}

            // Sort records sequentially by book ranking index
            records.sort((a, b) => a.s - b.s || a.c - b.c || a.v - b.v);

            let htmlBuffer = "";
            records.forEach(rec => {{
                // Standardize case boundaries for the structural audio asset lookup engine
                const upperBook = rec.b.toUpperCase().replace(/ /g, "_");
                const padChapter = String(rec.c).padStart(3, '0');
                const padVerse = String(rec.v).padStart(3, '0');
                
                const mp3Url = `../../musicscores/${{rec.folder}}/${{upperBook}}-${{padChapter}}_V${{padVerse}}.mp3`;

                htmlBuffer += `<tr>
                    <td class="source-cell" style="padding-left: 15px;">${{rec.b}} ${{rec.c}}:${{rec.v}}</td>
                    <td class="audio-cell">
                        <audio controls preload="none" style="height: 24px; width: 140px;">
                            <source src="${{mp3Url}}" type="audio/mpeg">
                        </audio>
                    </td>
                    <td style="text-align: center;">
                        <span class="gematria-cell" title="${{html.escape(rec.g_hov)}}">${{rec.g_val}}</span>
                    </td>
                    <td class="text-cell">${{rec.t}}</td>
                </tr>`;
            }});

            tableBody.innerHTML = htmlBuffer;
        }}

        window.onload = initializeExplorer;
    </script>
</body>
</html>
"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"🎉 Standalone Instance Explorer successfully generated at: {output_path}")
