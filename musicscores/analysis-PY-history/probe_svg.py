import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# --- CHANGE THIS TO A VALID PATH ON YOUR PC FOR TESTING ---
TEST_SVG = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores\Joshua-Judges\JOSHUA-013-3-2.svg")

def probe_svg_elements():
    if not TEST_SVG.exists():
        print(f"❌ Test file not found at {TEST_SVG}")
        return
        
    try:
        # SVG files often contain namespaces, so we register them to parse smoothly
        events = "start", "end"
        root = ET.parse(TEST_SVG).getroot()
        
        print("=" * 80)
        print(f"PROBING SVG STRUCTURAL ELEMENT TAGS FOR: {TEST_SVG.name}")
        print("=" * 80)
        
        classes_found = set()
        text_elements = []
        
        # Scan for path classes, symbols, and structural markers
        for elem in root.iter():
            # Track element classes (MuseScore often uses class="Rest", class="BarLine", etc.)
            cls = elem.get("class")
            if cls:
                classes_found.add(cls)
                
            # Track font/symbol usage references
            href = elem.get("{http://w3.org}href") or elem.get("href")
            if href:
                classes_found.add(f"Reference link: {href}")
                
            # Capture raw text node elements if present
            if elem.tag.endswith('text') and elem.text:
                text_elements.append(elem.text.strip())
                
        print("\n🔍 UNIQUE CLASSES AND REFERENCE SYMBOLS DETECTED:")
        for c in sorted(classes_found):
            print(f"   -> {c}")
            
        if text_elements:
            print("\n📝 TEXT EMBEDDED INSIDE SVG:")
            for t in text_elements[:10]:
                print(f"   -> {t}")
        print("=" * 80)
        
    except Exception as e:
        print(f"💥 Failed to probe SVG: {e}")

if __name__ == "__main__":
    probe_svg_elements()
