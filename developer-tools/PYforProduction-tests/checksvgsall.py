import re
import zipfile
from pathlib import Path

# Target your active workspace input directory
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")

def audit_all_svg_dimensions():
    print("=" * 80)
    print("GLOBAL SVG CANVAS PROFILE AUDIT (All Input Volumes)")
    print("=" * 80)
    
    epub_files = list(INPUT_DIR.glob("*.epub"))
    if not epub_files:
        print("No .epub files found in the Input directory.")
        return
        
    for epub_path in epub_files:
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                # Find all internal SVG image assets
                svg_files = [f for f in archive.namelist() if f.lower().endswith('.svg')]
                if not svg_files:
                    print(f"Book: {epub_path.name:<50} | No SVGs found.")
                    continue
                
                total_height = 0
                sample_count = min(len(svg_files), 50)  # Sample up to 50 SVGs for accuracy
                
                for i in range(sample_count):
                    svg_content = archive.read(svg_files[i]).decode('utf-8', errors='ignore')
                    
                    # Regex extracts the height integer from the viewBox layout bounding coordinates
                    viewbox_match = re.search(r'viewBox=["\']\s*0\s+0\s+\d+\s+(\d+)\s*["\']', svg_content)
                    if viewbox_match:
                        total_height += int(viewbox_match.group(1))
                    else:
                        # Fallback for explicit inline height style declarations
                        height_match = re.search(r'height=["\'](\d+)(?:px)?["\']', svg_content)
                        if height_match:
                            total_height += int(height_match.group(1))
                
                avg_height = total_height / sample_count if sample_count > 0 else 0
                
                # Print a clean, scannable line for each active book volume
                print(f"Book: {epub_path.name:<50}")
                print(f"  -> Total SVGs: {len(svg_files):<6} | Avg Canvas Height: {avg_height:.1f} units")
                
        except Exception as e:
            print(f"[Error reading archive] {epub_path.name}: {e}")
            
    print("=" * 80)
    print("GLOBAL CANVAS AUDIT COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    audit_all_svg_dimensions()
