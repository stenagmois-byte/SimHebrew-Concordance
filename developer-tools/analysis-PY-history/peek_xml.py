import os
import xml.etree.ElementTree as ET

FILENAME = "OBADIAH-001.XML"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(SCRIPT_DIR, FILENAME)

if not os.path.exists(FILE_PATH):
    print(f"File not found at: {FILE_PATH}")
else:
    tree = ET.parse(FILE_PATH)
    root = tree.getroot()
    
    print("--- Root Tag & Attributes ---")
    print(f"Tag: {root.tag}")
    print(f"Attribs: {root.attrib}\n")
    
    print("--- Sample Note Structure ---")
    # Grab the first available note to inspect its tags
    first_note = root.find('.//note')
    if first_note is not None:
        def dump_elem(elem, level=0):
            print("  " * level + f"<{elem.tag}> {elem.text.strip() if elem.text else ''}")
            for attr, val in elem.attrib.items():
                print("  " * (level + 1) + f"[@{attr}='{val}']")
            for child in elem:
                dump_elem(child, level + 1)
        dump_elem(first_note)
    else:
        print("No <note> elements found at all! Check your document structure.")
