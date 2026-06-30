import os
import re
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

def find_epub_directory():
    """
    Dynamically scans the terminal execution workspace to locate your EPUB volumes,
    ensuring it runs flawlessly on local systems or remote GitHub branches.
    """
    # Check 1: Is there a 'musicscores' folder right where the terminal is sitting?
    if Path("./musicscores").exists() and list(Path("./musicscores").glob("*.epub")):
        return Path("./musicscores")
        
    # Check 2: Is there a 'musicscores' folder sitting next to the script file?
    script_dir = Path(__file__).resolve().parent
    script_neighbor = script_dir / "musicscores"
    if script_neighbor.exists() and list(script_neighbor.glob("*.epub")):
        return script_neighbor
        
    # Check 3: Are the EPUB files sitting in the exact same directory as the script?
    if list(script_dir.glob("*.epub")):
        return script_dir
        
    # Check 4: Is there a folder containing epubs one level up (parent folder)?
    if list(script_dir.parent.glob("*.epub")):
        return script_dir.parent
        
    return None

def strip_ns(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def run_production_audit():
    # Resolve directory target location-independently
    target_dir = find_epub_directory()
    
    print("=" * 115)
    print("💎 PRODUCTION GEOMETRIC AUDIT ENGINE ACTIVATED")
    
    if not target_dir:
        print("❌ [CRITICAL ERROR] No folder containing .epub files could be located!")
        print("   Please place this script inside or right next to your EPUB volumes folder.")
        print("=" * 115)
        return
        
    print(f"📂 Successfully targeted volume source folder: {target_dir.resolve()}")
    
    epub_files = list(target_dir.glob("*.epub"))
    print(f"📦 Found {len(epub_files)} volume(s) ready for production audit.")
    print("=" * 115)
    
    total_books_audited = 0
    total_issues_exposed = 0
    
    for epub_path in sorted(epub_files):
        print(f"\n🚀 [STARTING AUDIT] Opening Volume Container: {epub_path.name}")
        print("-" * 115)
        total_books_audited += 1
        book_has_issues = False
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                internal_files = archive.namelist()
                html_files = [f for f in internal_files if f.lower().endswith(('.html', '.xhtml'))]
                
                narrative_files = [f for f in html_files if re.search(r'^\w+-\d+\.(html|xhtml)$', Path(f).name, re.IGNORECASE)]
                if not narrative_files:
                    print(f"   ⚠️  Skipping '{epub_path.name}': No standard canonical chapter files detected inside.")
                    continue
                
                def extract_chap_num(f_path):
                    m = re.search(r'-(\d+)\.', Path(f_path).name)
                    return int(m.group(1)) if m else 0
                max_chapter_file = max(narrative_files, key=extract_chap_num)
                
                for html_file in sorted(html_files):
                    file_name = Path(html_file).name
                    
                    if not re.search(r'^\w+-\d+\.(html|xhtml)$', file_name, re.IGNORECASE):
                        continue
                    
                    is_final_chapter_of_book = (html_file == max_chapter_file)
                    
                    with archive.open(html_file) as f_stream:
                        content = f_stream.read().decode('utf-8', errors='ignore')
                    
                    img_blocks = re.findall(r'<img[^>]+alt=["\']([^"\']+)["\'][^>]+src=["\']([^"\']+)["\']', content)
                    if not img_blocks:
                        continue
                        
                    verse_groups = {}
                    for alt_text, src_filename in img_blocks:
                        verse_match = re.search(r':(\d+)$', alt_text.strip())
                        if verse_match:
                            v_num = verse_match.group(1)
                            if v_num not in verse_groups:
                                verse_groups[v_num] = []
                            verse_groups[v_num].append(src_filename)
                    
                    sorted_verses = sorted(verse_groups.keys(), key=int)
                    final_verse_of_chapter = sorted_verses[-1] if sorted_verses else None
                    
                    for v_num, svg_list in verse_groups.items():
                        is_final_verse_of_chapter = (v_num == final_verse_of_chapter)
                        
                        for svg_idx, svg_filename in enumerate(svg_list):
                            is_final_line_of_verse = (svg_idx == len(svg_list) - 1)
                            
                            base_dir_prefix = Path(html_file).parent
                            resolved_path = (base_dir_prefix / svg_filename).as_posix()
                            
                            zip_target = resolved_path if resolved_path in internal_files else svg_filename
                            if zip_target not in internal_files:
                                continue
                                
                            with archive.open(zip_target) as svg_stream:
                                svg_text = svg_stream.read().decode('utf-8', errors='ignore')
                            
                            try:
                                root = ET.fromstring(svg_text)
                            except ET.ParseError:
                                print(f"   💥 [XML CORRUPTION] {file_name} -> File {svg_filename} contains broken SVG XML format.")
                                total_issues_exposed += 1
                                book_has_issues = True
                                continue
                            
                            STAFF_RIGHT_MARGIN = 760 
                            has_rest = False
                            has_barline = False
                            has_clef = False
                            
                            for elem in root.iter():
                                tag = strip_ns(elem.tag)
                                elem_class = elem.attrib.get('class', '')
                                
                                if 'Rest' in elem_class: has_rest = True
                                if 'BarLine' in elem_class: has_barline = True
                                if 'Clef' in elem_class: has_clef = True
                                
                                # Rule 1: Right Margin Hebrew Word Clipping Check
                                if tag == 'text':
                                    try:
                                        x_coord = float(elem.attrib.get('x', 0))
                                        if x_coord > STAFF_RIGHT_MARGIN:
                                            print(f"   ⚠️  [MARGIN CLIPPING RISK] {file_name} -> Verse {v_num}:")
                                            print(f"      -> Text element '{elem.text}' in asset '{svg_filename}' sits at x={x_coord} (Out of bounds).")
                                            total_issues_exposed += 1
                                            book_has_issues = True
                                    except ValueError:
                                        pass

                                # Rule 2: Slur Path Collision Check
                                if tag == 'path' and 'Slur' in elem_class:
                                    path_data = elem.attrib.get('d', '')
                                    y_values = [float(y) for y in re.findall(r'[-+]?\d*\.\d+|\d+', path_data)[1::2]]
                                    if y_values and max(y_values) > 120:  
                                        print(f"   ⚠️  [COLLISION RISK] {file_name} -> Verse {v_num}:")
                                        print(f"      -> Slur path in asset '{svg_filename}' dips into lyric line space (y={max(y_values)}).")
                                        total_issues_exposed += 1
                                        book_has_issues = True
                            
                            # Rule 3: Enforce No Rests Inside Mid-Verse Splitted Lines
                            if not is_final_line_of_verse and has_rest:
                                print(f"   💥 [PHANTOM LINE ERROR] {file_name} -> Verse {v_num}:")
                                print(f"      -> Mid-Verse File '{svg_filename}' prematurely contains a structural closing rest.")
                                total_issues_exposed += 1
                                book_has_issues = True

                            # Rule 4: Enforce End Rests vs Chapter Closures
                            if is_final_line_of_verse:
                                if is_final_verse_of_chapter and is_final_chapter_of_book:
                                    if has_rest:
                                        print(f"   ⚠️  [CADENCE EXCEPTION VIOLATION] {file_name} -> Verse {v_num}:")
                                        print(f"      -> The absolute final verse line of the book chapter ('{svg_filename}') must not contain a trailing rest.")
                                        total_issues_exposed += 1
                                        book_has_issues = True
                                else:
                                    if not (has_rest or has_barline or has_clef):
                                        print(f"   ⚠️  [CADENCE ERROR] {file_name} -> Verse {v_num}:")
                                        print(f"      -> Final Layout Asset: '{svg_filename}' terminates without structural rest/barline.")
                                        total_issues_exposed += 1
                                        book_has_issues = True
                                        
if not book_has_issues:
print(f"   🟢 SUCCESS: '{epub_path.name}' parsed cleanly with perfect geometric alignment.")
except 
Exception as e:print(f"💥 Critical execution block failure processing {epub_path.name}: {e}")
print("\n" + "=" * 115)
print(f"AUDIT COMPLETE. Evaluated {total_books_audited} volumes. Total issues exposed: {total_issues_exposed}")
print("=" * 115)
if name == "main":run_production_audit()