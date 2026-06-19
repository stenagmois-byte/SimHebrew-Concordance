import os
import re
import xml.etree.ElementTree as ET

def scan_mscz_alignment(file_path):
    """
    Scans a MuseScore XML file specifically for Hebrew text elements
    that are floating out of alignment due to untouched Auto-place stacking.
    """
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing {os.path.basename(file_path)}: {e}")
        return

    # Find all measures in the score
    measures = root.findall(".//Measure")
    floating_text_exceptions = []

    for idx, measure in enumerate(measures):
        # Scan ALL potential text containers in the measure
        text_nodes = measure.findall(".//StaffText") + measure.findall(".//Text") + measure.findall(".//RehearsalMark")
        
        for node in text_nodes:
            text_elem = node.find("text")
            text_val = "".join(node.itertext()).strip() if text_elem is None else (text_elem.text or "").strip()
            
            # Clean up the token to inspect content
            words = text_val.split()
            if not words:
                continue
                
            # Filter out standalone numbers (verse markers) or specific layout codes if necessary
            # We want to primarily target actual Hebrew prose strings
            is_verse_marker = re.match(r'^\d+', words[0])
            
            # --- AUTO-PLACE ALIGNMENT EVALUATION ---
            autoplace_node = node.find("autoPlace")
            pos_y_node = node.find(".//pos/y") if node.find(".//pos/y") is not None else node.find("pos/y")
            
            # If autoPlace is missing or explicit "1", it is active
            is_autoplace_active = autoplace_node is None or autoplace_node.text == "1"
            y_offset = float(pos_y_node.text) if pos_y_node is not None else 0.0

            # If Auto-place is active and nobody has manually offset it (y == 0),
            # MuseScore is likely forcing it to lines 2, 3, or 4 to avoid a collision.
            if is_autoplace_active and y_offset == 0.0:
                # We skip reporting pure verse numbers to keep the list focused on text prose alignment
                if not is_verse_marker:
                    floating_text_exceptions.append({
                        "measure": idx + 1,
                        "text": text_val
                    })

    # Display findings for this file
    display_name = os.path.basename(file_path)
    if floating_text_exceptions:
        print(f"\n⚠️  {display_name:<50} | Found {len(floating_text_exceptions)} potentially misaligned text items:")
        for item in floating_text_exceptions:
            print(f"   └─ Measure {item['measure']:<3} | Content: {item['text']}")
    else:
        # Keep the terminal clean if the post-edit alignment is perfect
        pass

# Example usage to run on your target directory or specific files
if __name__ == "__main__":
    # You can update this to loop through your active 10-chapter workspace folder
    target_score = r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance\musicscores\your_test_file.mscx"
    
    if os.path.exists(target_score):
        print("Starting post-edit Hebrew alignment verification...")
        scan_mscz_alignment(target_score)
    else:
        print("Please configure the target_score path to run the alignment scan.")
