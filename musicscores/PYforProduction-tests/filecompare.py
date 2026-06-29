import zipfile
from pathlib import Path

# Explicitly targeting your active workspace directories
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
OUTPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Output")

def audit_workspace_epub_sizes():
    print("=" * 110)
    print(f"{'Volume File Name':<30} | {'SVG Count':<9} | {'SVG Size':<11} | {'PNG Count':<9} | {'PNG Size':<11} | {'Comparison Status'}")
    print("-" * 110)
    
    total_svg_bytes = 0
    total_png_bytes = 0
    compared_books_count = 0
    
    # 1. Look through the Input directory to establish a baseline for your SVG versions
    for svg_epub_path in INPUT_DIR.glob("*.epub"):
        filename = svg_epub_path.name
        png_epub_path = OUTPUT_DIR / filename
        
        # Verify that a matching converted PNG epub exists in the Output directory
        if not png_epub_path.exists():
            continue
            
        compared_books_count += 1
        
        # 2. Count and calculate total uncompressed bytes of internal SVGs
        svg_count = 0
        svg_bytes = 0
        try:
            with zipfile.ZipFile(svg_epub_path, 'r') as archive:
                for item in archive.infolist():
                    if item.filename.lower().endswith('.svg'):
                        svg_count += 1
                        svg_bytes += item.file_size
        except Exception as e:
            print(f"[Error reading Input EPUB {filename}]: {e}")
            continue
            
        # 3. Count and calculate total uncompressed bytes of internal PNGs
        png_count = 0
        png_bytes = 0
        try:
            with zipfile.ZipFile(png_epub_path, 'r') as archive:
                for item in archive.infolist():
                    if item.filename.lower().endswith('.png'):
                        png_count += 1
                        png_bytes += item.file_size
        except Exception as e:
            print(f"[Error reading Output EPUB {filename}]: {e}")
            continue
            
        # Accumulate metrics for grand library summary lines
        total_svg_bytes += svg_bytes
        total_png_bytes += png_bytes
        
        # Convert raw byte totals into clean Megabyte (MB) displays
        svg_mb = svg_bytes / (1024 * 1024)
        png_mb = png_bytes / (1024 * 1024)
        
        # Evaluate how heavily the formats diverged for this specific file layout
        if svg_mb > 0:
            ratio = png_mb / svg_mb
            if ratio > 1.0:
                status = f"PNG is {ratio:.1f}x LARGER"
            elif ratio < 1.0:
                # Calculates inverted ratio savings (e.g. 136M vs 210M)
                savings = (1.0 - ratio) * 100
                status = f"PNG is {savings:.1f}% SMALLER"
            else:
                status = "Sizes are identical"
        else:
            status = "No vector data found"
            
        print(f"{filename:<30} | {svg_count:<9} | {svg_mb:>8.1f} MB | {png_count:<9} | {png_mb:>8.1f} MB | {status}")
        
    print("-" * 110)
    if compared_books_count > 0:
        grand_svg_mb = total_svg_bytes / (1024 * 1024)
        grand_png_mb = total_png_bytes / (1024 * 1024)
        grand_ratio = grand_png_mb / grand_svg_mb if grand_svg_mb > 0 else 0
        
        print(f"{'GRAND WORKSPACE TOTALS':<30} | {'':<9} | {grand_svg_mb:>8.1f} MB | {'':<9} | {grand_png_mb:>8.1f} MB | PNG is total {grand_ratio:.2f}x size")
    else:
        print("No matching .epub files found paired between the Input and Output workspace directories.")
    print("=" * 110)

if __name__ == "__main__":
    audit_workspace_epub_sizes()
