import zipfile
import re
from pathlib import Path

# --- DIRECTORY CONFIGURATION ---
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")

def scan_all_epubs_cadence_integrity():
    print("=" * 115)
    print("EPUB CADENCE SENTINEL: MULTI-FILE CORPUS CONTINUITY BATCH ENGINE")
    print("=" * 115)
    
    # Locate ALL epub files in the input folder
    epub_files = list(INPUT_DIR.glob("*.epub"))
    if not epub_files:
        print(f"⚠️ No active .epub files found inside {INPUT_DIR} to validate.")
        return
        
    print(f"Found {len(epub_files)} volume(s) ready for production audit.\n")
    
    total_books_audited = 0
    total_issues_exposed = 0
    
    # MASTER WORKFLOW LOOP: Sweeps across every book container in the folder
    for epub_path in sorted(epub_files):
        print(f"\n🚀 [STARTING AUDIT] Opening Volume Container: {epub_path.name}")
        print("-" * 115)
        total_books_audited += 1
        book_has_issues = False
        
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                internal_files = archive.namelist()
                html_files = [f for f in internal_files if f.lower().endswith(('.html', '.xhtml'))]
                
                for html_file in sorted(html_files):
                    file_name = Path(html_file).name
                    
                    # ONLY validate main narrative/canonical chapters (e.g., Psalms-145.html, Jeremiah-1.html)
                    if not re.search(r'^\w+-\d+\.(html|xhtml)$', file_name, re.IGNORECASE):
                        continue
                        
                    with archive.open(html_file) as f_stream:
                        content = f_stream.read().decode('utf-8', errors='ignore')
                    
                    # Match image tags and alternative layout texts side-by-side
                    img_blocks = re.findall(r'<img[^>]+alt=["\']([^"\']+)["\'][^>]+src=["\']([^"\']+)["\']', content)
                    if not img_blocks:
                        continue
                        
                    # Step 1: Group image lines dynamically by their explicit verse parameters
                    verse_groups = {}
                    for alt_text, src_filename in img_blocks:
                        verse_match = re.search(r':(\d+)$', alt_text.strip())
                        if verse_match:
                            v_num = verse_match.group(1)
                            if v_num not in verse_groups:
                                verse_groups[v_num] = []
                            verse_groups[v_num].append(src_filename)
                    
                    # Step 2: Validate the cadential endpoint of every verse cluster
                    for v_num, svg_list in verse_groups.items():
                        final_svg_filename = svg_list[-1]
                        
                        base_dir_prefix = Path(html_file).parent
                        resolved_path = (base_dir_prefix / final_svg_filename).as_posix()
                        
                        zip_target = resolved_path if resolved_path in internal_files else final_svg_filename
                        if zip_target not in internal_files:
                            continue
                            
                        with archive.open(zip_target) as svg_stream:
                            svg_text = svg_stream.read().decode('utf-8', errors='ignore')
                            
                        # --- TEXT-BASED DETECTION ENGINE ---
                        has_rest = 'class="Rest"' in svg_text or "class='Rest'" in svg_text
                        has_barline = 'class="BarLine"' in svg_text or "class='BarLine'" in svg_text
                        has_clef = 'class="Clef"' in svg_text or "class='Clef'" in svg_text
                        
                        # --- INTERMEDIARY MULTI-LINE ASSET VALIDATOR ---
                        if len(svg_list) > 1:
                            for intermediate_svg in svg_list[:-1]:
                                inter_resolved = (base_dir_prefix / intermediate_svg).as_posix()
                                inter_target = inter_resolved if inter_resolved in internal_files else intermediate_svg
                                if inter_target in internal_files:
                                    with archive.open(inter_target) as inter_stream:
                                        inter_text = inter_stream.read().decode('utf-8', errors='ignore')
                                    
                                    # An early rest indicates the batch file over-allocated verse lines
                                    if 'class="Rest"' in inter_text or "class='Rest'" in inter_text:
                                        total_issues_exposed += 1
                                        book_has_issues = True
                                        print(f"   💥 [PHANTOM LINE ERROR] {file_name} -> Verse {v_num}:")
                                        print(f"      -> Mid-Verse File '{intermediate_svg}' already contains a structural closing rest.")
                                        print(f"      [!] The subsequent file '{final_svg_filename}' likely belongs to the NEXT verse.")
                        
                        # Final boundary validation check
                        if not (has_rest or has_barline or has_clef):
                            total_issues_exposed += 1
                            book_has_issues = True
                            print(f"   ⚠️  [CADENCE ERROR] {file_name} -> Verse {v_num}:")
                            print(f"      -> Final Layout Asset: '{final_svg_filename}'")
                            print(f"      [!] File terminates without a standard resting cadence, BarLine, or Clef structure.")
                
                if not book_has_issues:
                    print(f"   🟢 SUCCESS: '{epub_path.name}' parsed cleanly with perfect cadential alignment.")
                    
        except Exception as e:
            print(f"💥 Critical execution block failure processing {epub_path.name}: {e}")
            
    print("\n" + "=" * 115)
    print(f"📋 GLOBAL PRODUCTION AUDIT COMPLETE:")
    print(f"   Total Books Checked: {total_books_audited}")
    print(f"   Total Layout Exceptions Uncovered: {total_issues_exposed}")
    if total_issues_exposed == 0:
        print("   🏆 ALL STAGED VOLUMES IMMACULATE: Ready for publication compile.")
    print("=" * 115)

if __name__ == "__main__":
    scan_all_epubs_cadence_integrity()
