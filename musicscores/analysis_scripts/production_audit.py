import os, re, zipfile
from pathlib import Path
from bs4 import BeautifulSoup

INPUT_DIR = Path("./musicscores")

def run_production_audit():
    for epub_path in sorted(INPUT_DIR.glob("*.epub")):
        print(f"\n🚀 [AUDIT] Opening: {epub_path.name}")
        with zipfile.ZipFile(epub_path, 'r') as archive:
            # Gather and filter main narrative chapter files
            html_files = [f for f in archive.namelist() if re.search(r'^\w+-\d+\.(html|xhtml)$', Path(f).name, re.IGNORECASE)]
            if not html_files: continue
            
            # Identify the absolute final chapter of the book container
            max_chap = max(html_files, key=lambda f: int(re.search(r'-(\d+)\.', Path(f).name).group(1) if re.search(r'-(\d+)\.', Path(f).name) else 0))
            
            for html_file in sorted(html_files):
                content = archive.read(html_file).decode('utf-8', errors='ignore')
                img_blocks = re.findall(r'<img[^>]+alt=["\']([^"\']+)["\'][^>]+src=["\']([^"\']+)["\']', content)
                
                # Group images dynamically by verse number
                verse_groups = {}
                for alt, src in img_blocks:
                    v_match = re.search(r':(\d+)$', alt.strip())
                    if v_match: verse_groups.setdefault(v_match.group(1), []).append(src)
                
                final_v = sorted(verse_groups.keys(), key=int)[-1] if verse_groups else None
                
                for v_num, svg_list in verse_groups.items():
                    for idx, svg_name in enumerate(svg_list):
                        # Resolve zip path prefix securely
                        zip_tgt = (Path(html_file).parent / svg_name).as_posix()
                        if zip_tgt not in archive.namelist(): zip_tgt = svg_name
                        if zip_tgt not in archive.namelist(): continue
                        
                        # High-velocity XML parsing via BeautifulSoup
                        soup = BeautifulSoup(archive.read(zip_tgt), 'xml')
                        
                        has_rest = bool(soup.select('[class*="Rest"]'))
                        has_cadence = has_rest or bool(soup.select('[class*="BarLine"], [class*="Clef"]'))
                        is_last_line = (idx == len(svg_list) - 1)
                        
                        # Rule 1: Text Margin Clipping Check
                        for txt in soup.find_all('text', x=True):
                            if float(txt['x']) > 760:
                                print(f"   ⚠️ [CLIP] {Path(html_file).name} v{v_num} -> '{txt.text}' out of bounds at x={txt['x']}")
                        
                        # Rule 2: Slur Lowering Lyrics Collision Check
                        for path in soup.select('path[class*="Slur"]'):
                            y_vals = [float(y) for y in re.findall(r'[-+]?\d*\.\d+|\d+', path.get('d', ''))[1::2]]
                            if y_vals and max(y_vals) > 120:
                                print(f"   ⚠️ [COLLISION] {Path(html_file).name} v{v_num} -> Slur dips to y={max(y_vals)}")

                        # Rule 3 & 4: Enforce Rests and Verse Cadence Configurations
                        if not is_last_line and has_rest:
                            print(f"   💥 [PHANTOM] {Path(html_file).name} v{v_num} -> Mid-verse file '{svg_name}' has a rest.")
                        if is_last_line:
                            if html_file == max_chap and v_num == final_v and has_rest:
                                print(f"   ⚠️ [EXCEPTION] {Path(html_file).name} v{v_num} -> Final book verse should NOT have a rest.")
                            elif not (html_file == max_chap and v_num == final_v) and not has_cadence:
                                print(f"   ⚠️ [CADENCE] {Path(html_file).name} v{v_num} -> Terminates without rest/barline.")

if __name__ == "__main__":
    run_production_audit()
