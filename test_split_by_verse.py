import xml.etree.ElementTree as ET
import zipfile
import shutil
from pathlib import Path

import xml.etree.ElementTree as ET
import zipfile
import shutil
from pathlib import Path

def slice_mscz_by_verse_rests(mscz_path, output_dir):
    """
    Parses a master chapter .mscz file, identifies verse boundaries by locating 
    the trailing measure rest delimiters, and exports self-contained files.
    """
    mscz_path = Path(mscz_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # 1. Setup localized workspace
    temp_dir = mscz_path.parent / f"temp_slice_{mscz_path.stem}"
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(exist_ok=True)
    
    try:
        with zipfile.ZipFile(mscz_path, 'r') as z:
            z.extractall(temp_dir)
        mscx_file = next(temp_dir.glob("*.mscx"), None)
        if not mscx_file:
            return False
            
        tree = ET.parse(mscx_file)
        root = tree.getroot()
        score_node = root.find("Score")
        if score_node is None:
            return False
            
        staff1 = score_node.find("./Staff[@id='1']")
        if staff1 is None:
            return False
            
        measures = staff1.findall("Measure")
        
        # 2. Iterate and group measures by trailing rest markers
        verse_buckets = []
        current_verse_measures = []
        
        for meas in measures:
            current_verse_measures.append(meas)
            
            # Check if this specific measure holds a structural Rest node
            if meas.find(".//Rest") is not None:
                # The trailing rest indicates the end of the current verse phrase
                verse_buckets.append(current_verse_measures)
                current_verse_measures = []
        
        # Catch the final verse of the chapter (which has no trailing rest, ending on a double bar instead)
        if current_verse_measures:
            verse_buckets.append(current_verse_measures)
            
        # 3. Re-serialize each accumulated measure bucket into its own standalone score
        for index, verse_measures in enumerate(verse_buckets, start=1):
            verse_root = ET.fromstring(ET.tostring(root))
            verse_score = verse_root.find("Score")
            
            # Clear old template measures
            for v_staff in verse_score.findall("Staff"):
                for old_meas in list(v_staff):
                    v_staff.remove(old_meas)
            
            # Re-inject the isolated measures for this specific verse sequence
            staff1_target = verse_score.find("./Staff[@id='1']")
            for orig_meas in verse_measures:
                cloned_meas = ET.fromstring(ET.tostring(orig_meas))
                
                # 🎯 FIXED ELEMENT SCRUBBER: Find any node that contains an <eid> element and delete it safely
                for parent in cloned_meas.iter():
                    eid_node = parent.find("eid")
                    if eid_node is not None:
                        parent.remove(eid_node)
                        
                staff1_target.append(cloned_meas)
                
            # 4. Pack back into a compressed .mscz file container
            verse_prefix = f"{mscz_path.stem}_V{str(index).zfill(3)}"
            sliced_mscx = temp_dir / f"{verse_prefix}.mscx"
            
            verse_tree = ET.ElementTree(verse_root)
            verse_tree.write(sliced_mscx, encoding="utf-8", xml_declaration=True)
            
            output_mscz = output_dir / f"{verse_prefix}.mscz"
            with zipfile.ZipFile(output_mscz, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                zip_out.write(sliced_mscx, sliced_mscx.name)
                for prop_file in temp_dir.glob("*.json"):
                    zip_out.write(prop_file, prop_file.name)
                    
            print(f"   ✅ Successfully sliced structural verse segment: {output_mscz.name}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Slicing Exception encountered: {e}")
        return False
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import os

    # 1. Define paths matching your project directory topology
    REPO_ROOT = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance")
    TEST_MSCZ = REPO_ROOT / "musicscores" / "Genesis" / "GENESIS-001.mscz"
    TEST_OUTPUT_DIR = REPO_ROOT / "musicscores" / "Genesis" / "test_sliced_verses"

    print("🔍 Launching local structural rest-splitting validation simulation...")
    print(f"   Input Target: {TEST_MSCZ}")
    print(f"   Destination Directory: {TEST_OUTPUT_DIR}\n")

    if not TEST_MSCZ.exists():
        print(f"❌ Error: Could not find target test file at {TEST_MSCZ}")
    else:
        # 2. Execute the verification slice function
        success = slice_mscz_by_verse_rests(TEST_MSCZ, TEST_OUTPUT_DIR)
        
        if success:
            print("\n🎉 Slicing validation complete!")
            # List generated files to verify the count matches Genesis 1's 31 verses
            generated_files = list(TEST_OUTPUT_DIR.glob("*.mscz"))
            print(f"   📁 Total unique verse assets created on disk: {len(generated_files)}")
            for f in sorted(generated_files)[:5]: # Print first 5 as a sample
                print(f"      ➔ {f.name}")
            if len(generated_files) > 5:
                print("      ... [truncated] ...")
        else:
            print("\n❌ Slicing process encountered structural errors.")
