import os
import re
import tempfile
import zipfile
from pathlib import Path

INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")

def repair_isaiah_margins():
    print("=" * 70)
    print("STARTING GEOMETRIC MARGIN REPAIR ON ISAIAH VOLUME")
    print("=" * 70)
    
    # Target the exact Isaiah file flagged by our audit
    isaiah_path = INPUT_DIR / "Isaiah - D. Robert MacDonald.epub"
    
    if not isaiah_path.exists():
        print(f"[Error] Could not find Isaiah file at: {isaiah_path}")
        return
        
    temp_dir = Path(tempfile.mkdtemp())
    svgs_repaired = 0
    
    try:
        # 1. Extract only the SVG files to our safe temporary workspace
        with zipfile.ZipFile(isaiah_path, 'r') as src_zip:
            svg_names = [f for f in src_zip.namelist() if f.lower().endswith('.svg')]
            for svg_name in svg_names:
                src_zip.extract(svg_name, temp_dir)
                
        # 2. Adjust the geometric viewing windows of each isolated SVG
        for svg_name in svg_names:
            local_svg_path = temp_dir / svg_name
            svg_text = local_svg_path.read_text(encoding="utf-8", errors="ignore")
            
            # Find the existing viewBox coordinates
            # Matches strings like: viewBox="0 0 3060 287" or viewBox='0 0 3060 287'
            match = re.search(r'viewBox=["\']\s*0\s+0\s+(\d+)\s+(\d+)\s*["\']', svg_text)
            
            if match:
                orig_width = match.group(1)
                
                # THE CORRECTION FIXED STRATEGY:
                # - Shift X-start to -60 (adds 60 units of padding space on the far left for bar numbers)
                # - Expand total width by 60 units to prevent right-side clipping
                # - Force total height to your known good 342 units
                new_width = int(orig_width) + 60
                new_viewbox = f'viewBox="-60 0 {new_width} 342"'
                
                # Replace the old viewBox declaration with our new safe margin layout
                svg_text = re.sub(r'viewBox=["\']\s*0\s+0\s+\d+\s+\d+\s*["\']', new_viewbox, svg_text)
                
                # Also ensure explicit height attributes inside the SVG node match our 342 target
                svg_text = re.sub(r'height=["\']\d+(?:px)?["\']', 'height="342"', svg_text)
                
                local_svg_path.write_text(svg_text, encoding="utf-8")
                svgs_repaired += 1
                
        # 3. Compile everything back into a clean, valid production EPUB
        if svgs_repaired > 0:
            updated_epub_path = isaiah_path.with_suffix(".repaired_epub")
            
            with zipfile.ZipFile(isaiah_path, 'r') as old_zip:
                with zipfile.ZipFile(updated_epub_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    for item in old_zip.infolist():
                        # Keep mimetype stored completely raw per standards
                        compress = zipfile.ZIP_STORED if item.filename == "mimetype" else zipfile.ZIP_DEFLATED
                        
                        if item.filename in svg_names:
                            new_zip.write(temp_dir / item.filename, item.filename, compress_type=compress)
                        else:
                            new_zip.writestr(item, old_zip.read(item.filename), compress_type=compress)
                            
            # Swap our repaired copy with the broken master copy safely
            os.replace(updated_epub_path, isaiah_path)
            print(f"[Success] Repaired margins and heights across {svgs_repaired} files in Isaiah!")
            
    except Exception as e:
        print(f"[Critical Failure] Could not repair Isaiah: {e}")
    finally:
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    repair_isaiah_margins()
