import os
import re
import shutil
import zipfile
from pathlib import Path
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM
from PIL import Image  # Script 2's crucial low-colour optimizer

# ==========================================
# CONFIGURATION CONSTANTS
# ==========================================
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
OUTPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Output")
TARGET_CLASSES = [".heb-text", ".heb-large", ".heb-larger"]
RTL_STYLES = "direction: rtl; unicode-bidi: embed;"

def setup_directories():
    if not INPUT_DIR.exists():
        raise FileNotFoundError(f"Input directory not found at: {INPUT_DIR}")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def flatten_svg_to_optimized_png(temp_dir):
    """Converts SVGs to 3x high-res, then scales down to an 8-bit gray palette format."""
    svg_mapping = {}
    
    for svg_path in temp_dir.rglob("*.svg"):
        png_path = svg_path.with_suffix(".png")
        try:
            # 1. High-Resolution Vector Evaluation
            drawing = svg2rlg(str(svg_path))
            if drawing is None:
                continue
            
            scaling_factor = 3.0
            drawing.width *= scaling_factor
            drawing.height *= scaling_factor
            drawing.scale(scaling_factor, scaling_factor)
            
            # Write temporary 24-bit image via ReportLab
            renderPM.drawToFile(drawing, str(png_path), fmt="PNG")
            
            # 2. Low-Colour Palette Post-Processing Optimization (From Script 2)
            with Image.open(png_path) as img:
                grayscale_img = img.convert("L")
                low_color_img = grayscale_img.quantize(colors=8, dither=Image.Dither.NONE)
                low_color_img.save(png_path, "PNG", optimize=True)
            
            rel_svg = svg_path.relative_to(temp_dir).as_posix()
            rel_png = png_path.relative_to(temp_dir).as_posix()
            svg_mapping[rel_svg] = rel_png
            
            svg_path.unlink()
        except Exception as e:
            print(f"  [Error] Failed converting {svg_path.name}: {e}")
            
    return svg_mapping

def update_manifest_and_html(temp_dir, svg_mapping):
    for file_path in list(temp_dir.rglob("*.html")) + list(temp_dir.rglob("*.xhtml")) + list(temp_dir.rglob("*.opf")):
        if not file_path.is_file():
            continue
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        modified = False
        for rel_svg, rel_png in svg_mapping.items():
            svg_name = os.path.basename(rel_svg)
            png_name = os.path.basename(rel_png)
            if svg_name in content:
                content = content.replace(svg_name, png_name)
                if file_path.suffix == ".opf":
                    content = content.replace('media-type="image/svg+xml"', 'media-type="image/png"')
                modified = True
        if modified:
            file_path.write_text(content, encoding="utf-8")

def modify_css_classes_safely(temp_dir):
    """Safely injects RTL styling into targeted Hebrew classes only if missing (From Script 1)."""
    for css_path in temp_dir.rglob("*.css"):
        content = css_path.read_text(encoding="utf-8", errors="ignore")
        modified = False
        
        for target_class in TARGET_CLASSES:
            if target_class in content:
                # Isolate the selector block content to verify properties
                class_blocks = content.split(target_class)
                already_has_rtl = False
                
                if len(class_blocks) > 1:
                    inner_block = class_blocks[1].split("}")[0]
                    if "direction:" in inner_block or "rtl" in inner_block:
                        already_has_rtl = True
                
                # Only inject via regex substitute if properties are missing
                if not already_has_rtl:
                    pattern = re.compile(r"(" + re.escape(target_class) + r"\s*\{)")
                    content = pattern.sub(f"\\1 {RTL_STYLES} ", content)
                    modified = True
                
        if modified:
            css_path.write_text(content, encoding="utf-8")

def prune_nav_html(temp_dir):
    for nav_path in temp_dir.rglob("nav.html"):
        content = nav_path.read_text(encoding="utf-8", errors="ignore")
        target_line = "<p> For the full set of Introductory Paragraphs, please refer to the JOB Volume.</p>"
        if target_line in content:
            content = content.replace(target_line, "")
            nav_path.write_text(content, encoding="utf-8")
        else:
            pattern = re.compile(
                r"<p\b[^>]*>\s*For\s+the\s+full\s+set\s+of\s+Introductory\s+Paragraphs,\s+please\s+refer\s+to\s+the\s+JOB\s+Volume\.\s*</p>", 
                re.IGNORECASE
            )
            content, count = pattern.subn("", content)
            if count > 0:
                nav_path.write_text(content, encoding="utf-8")

def package_epub(source_dir, output_epub_path):
    with zipfile.ZipFile(output_epub_path, 'w', zipfile.ZIP_DEFLATED) as epub:
        mimetype_path = source_dir / "mimetype"
        if mimetype_path.exists():
            epub.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        for root, _, files in os.walk(source_dir):
            for file in files:
                full_path = Path(root) / file
                rel_path = full_path.relative_to(source_dir)
                if rel_path.as_posix() == "mimetype":
                    continue
                epub.write(full_path, rel_path.as_posix())

def process_volume(epub_path):
    print(f"\nProcessing: {epub_path.name}")
    temp_extract_dir = OUTPUT_DIR / f"temp_{epub_path.stem}"
    
    with zipfile.ZipFile(epub_path, 'r') as zip_ref:
        zip_ref.extractall(temp_extract_dir)
        
    svg_map = flatten_svg_to_optimized_png(temp_extract_dir)
    if svg_map:
        update_manifest_and_html(temp_extract_dir, svg_map)
        print(f"  [Success] Quantized {len(svg_map)} music sheets down to 8-bit palette.")
        
    modify_css_classes_safely(temp_extract_dir)
    prune_nav_html(temp_extract_dir)
    
    final_epub_path = OUTPUT_DIR / epub_path.name
    package_epub(temp_extract_dir, final_epub_path)
    shutil.rmtree(temp_extract_dir)

def main():
    setup_directories()
    epub_files = list(INPUT_DIR.glob("*.epub"))
    if not epub_files:
        print("No .epub files found to process.")
        return
    print(f"Found {len(epub_files)} volumes. Running optimized production script...")
    for epub_file in epub_files:
        process_volume(epub_file)
    print("\nAll tasks completed successfully!")

if __name__ == "__main__":
    main()
