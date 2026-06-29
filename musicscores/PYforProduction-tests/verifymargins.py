import re
import zipfile
from pathlib import Path

# Target your clean, resynchronized input workspace
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")

def audit_all_viewbox_origins():
    print("=" * 90)
    print("GLOBAL HORIZONTAL VIEWBOX ORIGIN AUDIT (Left-Margin Integrity Check)")
    print("=" * 90)
    print(f"{'Volume File Name':<50} | {'Status / Anomalies Found'}")
    print("-" * 90)
    
    epub_files = list(INPUT_DIR.glob("*.epub"))
    if not epub_files:
        print("No .epub files found in the Input directory.")
        return
        
    for epub_path in epub_files:
        # Avoid re-auditing Isaiah since we already know its history
        if "Isaiah" in epub_path.name:
            continue
            
        try:
            with zipfile.ZipFile(epub_path, 'r') as archive:
                svg_files = [f for f in archive.namelist() if f.lower().endswith('.svg')]
                if not svg_files:
                    continue
                
                non_zero_x_count = 0
                sample_count = min(len(svg_files), 100) # Sample 100 files per book for dense coverage
                example_viewbox = ""
                
                for i in range(sample_count):
                    svg_content = archive.read(svg_files[i]).decode('utf-8', errors='ignore')
                    
                    # Captures all four core view box layout tokens: X, Y, Width, Height
                    match = re.search(r'viewBox=["\']\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*["\']', svg_content)
                    if match:
                        x_start = float(match.group(1))
                        example_viewbox = match.group(0)
                        
                        # Flag if the camera view starts anywhere other than 0.0
                        if x_start != 0.0:
                            non_zero_x_count += 1
                
                if non_zero_x_count > 0:
                    print(f"{epub_path.name:<50} | ⚠️ WARNING: {non_zero_x_count}/{sample_count} sampled SVGs shift margins! ({example_viewbox})")
                else:
                    print(f"{epub_path.name:<50} | ✅ Clean (Left margin starts at 0)")
                    
        except Exception as e:
            print(f"[Error Reading] {epub_path.name}: {e}")
            
    print("=" * 90)
    print("LEFT-MARGIN INTEGRITY CHECK COMPLETE")
    print("=" * 90)

if __name__ == "__main__":
    audit_all_viewbox_origins();
