import re
from pathlib import Path

INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")

def check_svg_dimensions():
    print("=" * 75)
    print("SVG CANVAS PROFILE AUDIT (Identifying Multi-line vs Single-line)")
    print("=" * 75)
    
    # Target books to inspect side-by-side
    target_books = ["Chronicles", "Exodus", "Isaiah", "Kings"]
    
    for epub_path in INPUT_DIR.glob("*.epub"):
        # Match only the specific books we want to cross-reference
        if not any(book in epub_path.name for book in target_books):
            continue
            
        import zipfile
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                svg_files = [f for f in archive.namelist() if f.lower().endswith('.svg')]
                if not svg_files:
                    continue
                
                total_height = 0
                sample_count = min(len(svg_files), 50) # Sample the first 50 SVGs
                
                for i in range(sample_count):
                    # Read raw XML text of the SVG file directly from the zip
                    svg_content = archive.read(svg_files[i]).decode('utf-8', errors='ignore')
                    
                    # Look for the viewBox="0 0 width height" attribute
                    viewbox_match = re.search(r'viewBox=["\']\s*0\s+0\s+\d+\s+(\d+)\s*["\']', svg_content)
                    if viewbox_match:
                        total_height += int(viewbox_match.group(1))
                    else:
                        # Fallback for explicit height attributes
                        height_match = re.search(r'height=["\'](\d+)(?:px)?["\']', svg_content)
                        if height_match:
                            total_height += int(height_match.group(1))
                
                avg_height = total_height / sample_count if sample_count > 0 else 0
                
                print(f"Book: {epub_path.name:<45}")
                print(f"  -> Total SVGs: {len(svg_files)}")
                print(f"  -> Average Canvas Height: {avg_height:.1f} units")
                print(f"  -> Structural Type: {'[OLDER MULTI-LINE]' if avg_height > 200 else '[NEWER SINGLE-LINE]'}\n")
                
        except Exception as e:
            print(f"Error checking {epub_path.name}: {e}")

if __name__ == "__main__":
    check_svg_dimensions()
