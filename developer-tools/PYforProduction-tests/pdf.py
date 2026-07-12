import os
import subprocess
import time
import zipfile
from pathlib import Path
from xml.etree import ElementTree

# Workspace targeting
INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
PDF_OUTPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Paperback_PDFs")
CALIBRE_CONVERTER = Path(r"C:\Program Files\Calibre2\ebook-convert.exe")

def strip_epub_structural_cover(original_epub_path, temp_epub_path):
    """
    Clones the EPUB while modifying the internal metadata index (.opf file) 
    to completely hide any trace of cover declarations from Calibre's parser.
    """
    try:
        with zipfile.ZipFile(original_epub_path, 'r') as src, zipfile.ZipFile(temp_epub_path, 'w', zipfile.ZIP_DEFLATED) as dst:
            
            opf_file_name = None
            for name in src.namelist():
                if name.endswith('.opf'):
                    opf_file_name = name
                    break
                    
            if not opf_file_name:
                return False

            opf_content = src.read(opf_file_name)
            namespaces = {'opf': 'http://idpf.org'}
            ElementTree.register_namespace('', 'http://idpf.org')
            root = ElementTree.fromstring(opf_content)
            
            cover_item_ids = set()
            
            # Remove cover metadata tags
            metadata = root.find(".//opf:metadata", namespaces)
            if metadata is not None:
                for meta in metadata.findall(".//opf:meta[@name='cover']", namespaces):
                    cover_item_ids.add(meta.get('content'))
                    metadata.remove(meta)
            
            # Unmark items in the manifest
            manifest = root.find(".//opf:manifest", namespaces)
            if manifest is not None:
                for item in manifest.findall(".//opf:item", namespaces):
                    item_id = item.get('id')
                    href = item.get('href', '').lower()
                    properties = item.get('properties', '').lower()
                    
                    if item_id in cover_item_ids or 'cover' in item_id.lower() or 'cover' in properties or 'cover' in href or 'titlepage' in href:
                        cover_item_ids.add(item_id)
                        if 'cover-image' in properties:
                            item.set('properties', properties.replace('cover-image', '').strip())

            # Drop cover references from the reading Spine
            spine = root.find(".//opf:spine", namespaces)
            if spine is not None:
                for itemref in spine.findall(".//opf:itemref", namespaces):
                    idref = itemref.get('idref')
                    if idref in cover_item_ids or 'cover' in idref.lower() or 'titlepage' in idref.lower():
                        spine.remove(itemref)

            # Wipe out the Guide landmarks block
            guide = root.find(".//opf:guide", namespaces)
            if guide is not None:
                for reference in guide.findall(".//opf:reference", namespaces):
                    ref_type = reference.get('type', '').lower()
                    ref_href = reference.get('href', '').lower()
                    if 'cover' in ref_type or 'cover' in ref_href or 'titlepage' in ref_href:
                        guide.remove(reference)
                if len(guide) == 0:
                    root.remove(guide)

            updated_opf_content = ElementTree.tostring(root, encoding='utf-8', xml_declaration=True)

            # Copy files while skipping loose raw cover pages
            for item in src.infolist():
                if item.filename == opf_file_name:
                    dst.writestr(item, updated_opf_content)
                else:
                    filename_lower = os.path.basename(item.filename).lower()
                    if filename_lower in ['titlepage.xhtml', 'cover.xhtml', 'titlepage.html', 'cover.html']:
                        continue
                    dst.writestr(item, src.read(item.filename))
                    
        return True
    except Exception as e:
        print(f"  [Notice] Structural index rewrite bypassed ({e}). Using native layout.")
        return False

def generate_custom_paperback_pdfs():
    print("=" * 85)
    print("SAFE SEQUENTIAL PAPERBACK PDF PRODUCTION GENERATOR - FORCE STRIPPED COVERS")
    print("=" * 85)
    
    if not CALIBRE_CONVERTER.exists():
        print(f"[Critical Error] Calibre engine not found at:\n{CALIBRE_CONVERTER}")
        return
        
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    epub_files = list(INPUT_DIR.glob("*.epub"))
    epub_files = [f for f in epub_files if not f.name.endswith(".temp.epub")]
    
    if not epub_files:
        print("No master .epub files found in the Input folder.")
        return
        
    print(f"Found {len(epub_files)} volumes. Starting synchronized background printing...")
    start_time = time.time()
    
    header_html = """<header><table style="width: 100%;"><tbody><tr><td style="width: 30%; font-family: 'Georgia', serif; font-size: 10px;">The Music of the Bible</td><td style="text-align: right; font-family: 'Georgia', serif; font-size: 10px;">_SECTION_&emsp;&emsp;&emsp;&emsp;</td></tr></tbody></table></header>"""
    footer_html = """<footer><div style="align: left; width: 92%; text-align: center; font-family: 'Georgia', serif; font-size: 10px;">_PAGENUM_</div></footer>"""
    
    chapter_detect_xpath = "//*[((name()='h1' or name()='h2') and re:test(., '\\s*((chapter|book|section|part)\\s+)|((prolog|prologue|epilogue)(\\s+|$))', 'i')) or @class = 'chapter']"
    pagebreak_before_xpath = "//*[name()='h1' or name()='h2']"

    for idx, epub_path in enumerate(epub_files, start=1):
        pdf_path = PDF_OUTPUT_DIR / epub_path.with_suffix(".pdf").name
        temp_epub_path = epub_path.with_suffix(".temp.epub")
        
        print(f"\n[{idx}/{len(epub_files)}] Printing: {epub_path.name}")
        
        # 1. Strip files internally 
        clean_success = strip_epub_structural_cover(epub_path, temp_epub_path)
        conversion_source = temp_epub_path if clean_success else epub_path
        
        # 2. Convert with explicit command override
        command = [
            str(CALIBRE_CONVERTER),
            str(conversion_source),
            str(pdf_path),
            
            # --- Cover Destruction Override ---
            "--cover=",                       # Force Calibre to register a blank null cover value
            
            # --- Page Configuration & Layout Fix ---
            "--pdf-page-margin-left=72.0",    
            "--pdf-page-margin-right=38.0",   
            "--pdf-page-margin-top=54.0",     
            "--pdf-page-margin-bottom=54.0",  
            
            # --- Typography & Font Specifications ---
            "--pdf-default-font-size=13",     
            "--pdf-mono-font-size=11",
            "--pdf-standard-font=serif",
            "--pdf-serif-family=Georgia",      
            "--pdf-mono-family=Courier New",
            "--minimum-line-height=120",      
            "--embed-all-fonts",              
            
            # --- Headers, Footers & Running Page Assets ---
            f"--pdf-header-template={header_html}",
            f"--pdf-footer-template={footer_html}",
            
            # --- Chapter Traversal & Pagination Break Controls ---
            f"--chapter={chapter_detect_xpath}",
            "--chapter-mark=pagebreak",       
            f"--page-breaks-before={pagebreak_before_xpath}"
        ]
        
        try:
            result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                print(f"  [Success] Successfully saved print-ready: {pdf_path.name}")
            else:
                print(f"  [Warning] Pipeline notification details:")
                err_lines = result.stderr.strip().splitlines()
                last_err = err_lines[-1] if err_lines else "Unknown CLI exception"
                print(f"  -> {last_err}")
                
            print("  -> Cooling motherboard sensors for 5 seconds...")
            time.sleep(5)
            
        except Exception as e:
            print(f"  [Error] Processing interruption on {epub_path.name}: {e}")
            
        finally:
            if temp_epub_path.exists():
                try:
                    temp_epub_path.unlink()
                except Exception:
                    pass
            
    total_time = (time.time() - start_time) / 60
    print("\n" + "=" * 85)
    print(f"PRINT COMPILATION RUN FINALIZED. Elapsed Time: {total_time:.1f} minutes")
    print("=" * 85)

if __name__ == "__main__":
    generate_custom_paperback_pdfs()
