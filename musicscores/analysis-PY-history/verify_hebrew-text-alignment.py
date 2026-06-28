import zipfile
import xml.etree.ElementTree as ET
import os
import re
from collections import defaultdict

def scan_mscz_alignment(file_path):
    """
    Scans a MuseScore XML file for Hebrew text elements.
    Groups elements by visual layout lines (separated by LayoutBreaks)
    and flags lines where text elements have conflicting Y-offsets.
    """
    try:
        with zipfile.ZipFile(file_path, 'r') as archive:
            mscx_filename = [f for f in archive.namelist() if f.endswith('.mscx')]
            with archive.open(mscx_filename[0]) as xml_file:
                tree = ET.parse(xml_file)
                root = tree.getroot()
    except Exception as e:
        print(f"❌ Error parsing {os.path.basename(file_path)}: {e}")
        return

    measures = root.findall(".//Measure")
    
    current_line_idx = 1
    # Store elements grouped by line index: { line_num: [ {text_info}, ... ] }
    line_groups = defaultdict(list)

    for idx, measure in enumerate(measures):
        measure_num = idx + 1
        
        # 1. Extract all relevant text nodes in this measure
        text_nodes = measure.findall(".//StaffText") + measure.findall(".//Text") + measure.findall(".//RehearsalMark")
        
        for node in text_nodes:
            text_elem = node.find("text")
            text_val = "".join(node.itertext()).strip() if text_elem is None else (text_elem.text or "").strip()
            
            # Clean up and skip empty strings or pure verse markers
            words = text_val.split()
            if not words or re.match(r'^\d+', words[0]):
                continue

            # 2. Determine the explicit Y-offset
            # MuseScore usually nests this under <pos><y>value</y></pos>
            pos_y_node = node.find(".//pos/y") if node.find(".//pos/y") is not None else node.find("pos/y")
            y_offset = float(pos_y_node.text) if pos_y_node is not None else 0.0

            # Append metadata to our current system line group
            line_groups[current_line_idx].append({
                "measure": measure_num,
                "text": text_val,
                "y_offset": y_offset
            })

        # 3. Track Line Breaks / System Breaks
        # If this measure ends with a line break, the NEXT measure starts a new system line
        layout_break = measure.find(".//LayoutBreak")
        if layout_break is not None:
            subtype = layout_break.find("subtype")
            if subtype is not None and subtype.text == "line":
                current_line_idx += 1

    # --- SPEC EVALUATION: Compare Y-offsets within each system line ---
    floating_text_exceptions = []

    for line_num, items in line_groups.items():
        if not items:
            continue
            
        # Get all unique Y-offsets present across this entire system line
        unique_offsets = set(item["y_offset"] for item in items)
        
        # If there is more than 1 unique Y-offset, we have a mismatch conflict!
        if len(unique_offsets) > 1:
            floating_text_exceptions.append({
                "line": line_num,
                "offsets": sorted(list(unique_offsets)),
                "items": items
            })

    # Display findings for this file
    display_name = os.path.basename(file_path)
    if floating_text_exceptions:
        print(f"\n⚠️  {display_name:<50} | Found {len(floating_text_exceptions)} misaligned system lines:")
        for exc in floating_text_exceptions:
            print(f"   └─ Line {exc['line']} has conflicting offsets: {exc['offsets']}")
            for item in exc["items"]:
                print(f"      • Measure {item['measure']:<3} | Y: {item['y_offset']:>5} | Content: {item['text']}")
    else:
        # File perfectly complies with the spec
        print(f"✅ {display_name:<50} | Perfect horizontal alignment.")

