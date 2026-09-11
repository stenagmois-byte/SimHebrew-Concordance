import json
import os
import html
import re

# The definitive consonantal decoder map
HEBREW_DECIMAL_GEMATRIA = {
    1488: 1, 1489: 2, 1490: 3, 1491: 4, 1492: 5, 1493: 6, 1494: 7, 1495: 8, 1496: 9,
    1497: 10, 1499: 20, 1498: 20, 1500: 30, 1502: 40, 1501: 40, 1504: 50, 1503: 50,
    1505: 60, 1506: 70, 1508: 80, 1507: 80, 1510: 90, 1509: 90, 1511: 100, 1512: 200,
    1513: 300, 1514: 400
}

# The strict Masoretic Tanakh canonical sequence
BOOK_SEQUENCE = {
    "01": "Genesis", "02": "Exodus", "03": "Leviticus", "04": "Numbers", "05": "Deuteronomy",
    "06": "Joshua", "07": "Judges", "08": "1 Samuel", "09": "2 Samuel", "10": "1 Kings",
    "11": "2 Kings", "12": "Isaiah", "13": "Jeremiah", "14": "Ezekiel", "15": "Hosea",
    "16": "Joel", "17": "Amos", "18": "Obadiah", "19": "Jonah", "20": "Micah",
    "21": "Nahum", "22": "Habakkuk", "23": "Zephaniah", "24": "Haggai", "25": "Zechariah",
    "26": "Malachi", "27": "Psalms", "28": "Proverbs", "29": "Job", "30": "Song of Songs",
    "31": "Ruth", "32": "Lamentations", "33": "Ecclesiastes", "34": "Esther", "35": "Daniel",
    "36": "Ezra", "37": "Nehemiah", "38": "1 Chronicles", "39": "2 Chronicles"
}

def calculate_word_gematria(hebrew_word):
    unescaped = html.unescape(hebrew_word)
    return sum(HEBREW_DECIMAL_GEMATRIA[ord(c)] for c in unescaped if ord(c) in HEBREW_DECIMAL_GEMATRIA)

def get_lowest_common_factors(n):
    if n <= 1: return []
    factors = set()
    d = 2
    temp = n
    while d * d <= temp:
        while (temp % d) == 0:
            factors.add(d)
            temp //= d
        d += 1
    if temp > 1:
        factors.add(temp)
    return sorted(list(factors))

def format_verse_label(key_string):
    parts = key_string.split('_')
    book_num = parts[0]
    ch_num = str(int(parts[1]))
    v_num = str(int(parts[2]))
    book_name = BOOK_SEQUENCE.get(book_num, f"Book {book_num}")
    return f"{book_name} {ch_num}:{v_num}"

def invert_json_data(json_file_path):
    print("Reading interlin.json...")
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    verse_aggregates = {}
    
    for item in data.get("items", []):
        key = item.get("k", "")
        hebrew_text = item.get("h", "")
        
        if not key or not hebrew_text:
            continue
            
        verse_key = "_".join(key.split("_")[:3])
        word_weight = calculate_word_gematria(hebrew_text)
        
        if verse_key not in verse_aggregates:
            verse_aggregates[verse_key] = {
                'words': [],
                'total_sum': 0,
                'book_num': key.split("_")[0],
                'chapter_num': str(int(key.split("_")[1])),
                'verse_num': str(int(key.split("_")[2]))
            }
            
        verse_aggregates[verse_key]['words'].append(hebrew_text)
        verse_aggregates[verse_key]['total_sum'] += word_weight

    gematria_registry = {}
    all_unique_factors = set()
    all_present_books = set()  # <-- NEW TRACKING VARIABLES

    for v_key, info in verse_aggregates.items():
        total_sum = info['total_sum']
        if total_sum == 0:
            continue
            
        if total_sum not in gematria_registry:
            gematria_registry[total_sum] = []
            
        full_verse_text = " ".join(info['words'])
        label = format_verse_label(v_key)
        book_name = BOOK_SEQUENCE.get(info['book_num'], info['book_num'])
        all_present_books.add(book_name)  # <-- NEW: Capture book name
        
        dynamic_link = f"ornament_chapter.html?book={book_name}&chapter={info['chapter_num']}"
        
        gematria_registry[total_sum].append({
            'label': label,
            'book': book_name,        # <-- NEW: Link book name to individual records
            'text': full_verse_text,
            'link': dynamic_link
        })

    processed_groups = []

    for sum_val, recs in gematria_registry.items():
        if len(recs) > 1:
            factors = get_lowest_common_factors(sum_val)
            max_factor = max(factors) if factors else 0
            
            for f in factors:
                all_unique_factors.add(f)
                
            # <-- NEW: Collect all books in this specific matching group
            group_books = " ".join(f"[{r['book']}]" for r in recs)
            
            processed_groups.append({
                'sum_val': sum_val,
                'max_factor': max_factor,
                'factors': factors,
                'group_books': group_books, # <-- NEW
                'records': recs
            })

    processed_groups.sort(key=lambda x: x['max_factor'], reverse=True)
    sorted_unique_factors = sorted(list(all_unique_factors))

    sorted_books = [BOOK_SEQUENCE[k] for k in sorted(BOOK_SEQUENCE.keys()) if BOOK_SEQUENCE[k] in all_present_books]

    # <-- UPDATED CALL: Pass the sorted books to the html generator
    build_output_page(processed_groups, sorted_unique_factors, sorted_books)

def build_output_page(groups, unique_factors, books):
    out_path = "gematria_verse_twins.html"
    
    html_out = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <link rel="stylesheet" type="text/css" href="qstyles.css"/>
    <title>Inverted JSON Verse Concordance</title>
    <style>
        .filter-panel { 
            position: sticky; 
            top: 0; 
            z-index: 100; 
            background: #fdfaf4; 
            padding: 15px; 
            margin: 0 auto 15px auto; 
            width: calc(100% - 20px); 
            border: 1px solid #800000; 
            border-bottom: 3px solid #800000;
            border-radius: 0 0 5px 5px; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .filter-select { padding: 6px; font-family: monospace; font-size: 14px; margin-right: 15px; border: 1px solid #ccc; border-radius: 4px; }
        .factor-tag { font-family: monospace; font-weight: bold; color: #800000; letter-spacing: 1px; }
        
        /* STICKY TABLE CELL HEADERS */
        .sticky-thead th {
            position: sticky;
            top: 72px; 
            z-index: 90;
            background-color: #f3f0e8;
            color: #800000;
            font-weight: bold;
            padding: 10px;
            border-bottom: 2px solid black;
            text-align: left;
        }
    </style>
</head>
<body>
    <div class="nav" style="margin-left:10px; margin-top:10px;"><a href="matrix.html">Matrix page</a> | <a href="musicscores/index.html">Music Scores page</a></div>
    <h2 style="margin-left:10px;">Co-Inherent Verse Weights Index (JSON Engine)</h2>
    <p style="margin-left:10px; color:#555;">Sorted by <strong>Maximum Prime Factor (Largest First)</strong>. Click references to inspect their dynamic musical profiles.</p>
    
    <!-- STICKY FILTER BAR -->
    <div class="filter-panel">
        <strong style="color:#800000; margin-right:10px;">Filters:</strong>
        
        <select id="factorFilter" class="filter-select" onchange="applyFilters()">
            <option value="">-- All Factors --</option>"""
            
    for f in unique_factors:
        html_out += f'\n            <option value="[{f}]">Factor: [{f}]</option>'
        
    html_out += """
        </select>

        <select id="bookFilter" class="filter-select" onchange="applyFilters()">
            <option value="">-- All Books --</option>"""
            
    for b in books:
        html_out += f'\n            <option value="[{b}]">{b}</option>'
        
    html_out += """
        </select>
        
        <button onclick="clearFilters()" style="padding:6px 12px; background:#800000; color:white; border:none; border-radius:4px; cursor:pointer; font-weight:bold;">Reset View</button>
    </div>

    <table id="concordanceTable" class="btable" style="width: calc(100% - 20px); margin: 0 auto; border-collapse: collapse;">
        <thead class="sticky-thead">
            <tr>
                <th style="width:15%;">Weight (Sum)</th>
                <th style="width:20%;">Factors Bracketed [x]</th>
                <th style="width:65%;">Twin Verse Co-Inherences</th>
            </tr>
        </thead>
        <tbody>"""
        
    for group in groups:
        bracketed_factors = " ".join(f"[{f}]" for f in group['factors'])
        
        html_out += f"""
            <tr class="data-row" data-factors="{bracketed_factors}" data-books="{group['group_books']}" style="border-bottom: 1px solid lightgrey; vertical-align: top;">
                <td style="padding:12px;"><span style="padding:3px 8px; font-weight:bold; color:#800000;">{group['sum_val']}</span></td>
                <td style="padding:12px;" class="factor-tag">{bracketed_factors}</td>
                <td style="padding:12px;">"""
                
        for record in group['records']:
            # FIXED: Removed the regex splitting rules completely.
            # The text now flows as a flexible, standard string block.
            html_out += f"""
                    <div class="verse-entry" data-verse-book="[{record['book']}]" style="margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px dashed #eee;">
                        <a href="{record['link']}" target="_blank" style="font-weight:bold; color:#800000; text-decoration:none; margin-right:15px; display:inline-block; vertical-align:top;">{record['label']} ↗</a>
                        <span class="hebrew" style="font-size:18px; direction:rtl; text-align:right; display:inline-block; width:80%; line-height:1.5;">{record['text']}</span>
                    </div>"""
                    
        html_out += "</td></tr>"
            
    html_out += """
        </tbody>
    </table>

    <!-- JAVASCRIPT REAL-TIME DUAL SELECTION FILTERING -->
    <script>
        function applyFilters() {
            var selectedFactor = document.getElementById("factorFilter").value;
            var selectedBook = document.getElementById("bookFilter").value;
            var rows = document.querySelectorAll(".data-row");
            
            rows.forEach(function(row) {
                var rowFactors = row.getAttribute("data-factors");
                var rowBooks = row.getAttribute("data-books");
                
                var factorMatch = (selectedFactor === "" || rowFactors.includes(selectedFactor));
                var bookMatch = (selectedBook === "" || rowBooks.includes(selectedBook));
                
                if (factorMatch && bookMatch) {
                    row.style.display = ""; 
                    
                    var verseEntries = row.querySelectorAll(".verse-entry");
                    var visibleVerses = 0;
                    
                    verseEntries.forEach(function(verse) {
                        var verseBook = verse.getAttribute("data-verse-book");
                        if (selectedBook === "" || verseBook === selectedBook) {
                            verse.style.display = ""; 
                            visibleVerses++;
                        } else {
                            verse.style.display = "none"; 
                        }
                    });
                    
                    if (visibleVerses === 0) {
                        row.style.display = "none";
                    }
                    
                } else {
                    row.style.display = "none"; 
                }
            });
        }

        function clearFilters() {
            document.getElementById("factorFilter").value = "";
            document.getElementById("bookFilter").value = "";
            applyFilters();
        }
    </script>
</body>
</html>"""
    
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_out)
    print(f"Successfully generated clean searchable index map at: {out_path}")

if __name__ == "__main__":
    invert_json_data("interlin.json")
