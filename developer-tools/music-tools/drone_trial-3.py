import os, re, shutil, zipfile, subprocess, time
from pathlib import Path
import xml.etree.ElementTree as ET

SCORE_DIR = Path("./musicscores")
MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\MuseScore4.exe"

PAUSE_TIMES = {"caesura": "2.0", "breath": "1.0"}
# 1. Update your map to use pure integers for MIDI numbers
DRONE_NOTE_MAP = {"c": 48, "d": 50, "e": 52, "f": 53, "f#": 54, "g": 55, "g#": 56, "A": 57, "B": 59, "C": 60}

import xml.etree.ElementTree as ET

def inject_native_musescore4_drone(root_xml, target_pitch=52):
    if isinstance(target_pitch, int):
        midi_val = target_pitch
    elif 'DRONE_NOTE_MAP' in globals() and target_pitch in DRONE_NOTE_MAP:
        midi_val = DRONE_NOTE_MAP[target_pitch]
    else:
        midi_val = 52 
        
    score_node = root_xml.find("Score")
    if score_node is None:
        return False

    # 1. Inject Part 2 Header (Cello) strictly after Part 1
    if score_node.find(".//Part[@id='2']") is None:
        cello_xml_template = """
        <Part id="2">
            <Staff id="2">
                <StaffType group="pitched"/>
                <defaultClef>F</defaultClef>
            </Staff>
            <trackName>Violoncello</trackName>
            <Instrument id="violoncello">
                <longName>Violoncello</longName>
                <shortName>Vc.</shortName>
                <trackName>Violoncello</trackName>
                <instrumentId>strings.cello</instrumentId>
                <clef>F</clef>
                <Channel name="pizzicato">
                    <program value="45"/>
                    <synti>Fluid</synti>
                </Channel>
            </Instrument>
        </Part>
        """
        cello_element = ET.fromstring(cello_xml_template)
        
        part1 = score_node.find("./Part[@id='1']")
        if part1 is not None:
            children = list(score_node)
            part1_index = children.index(part1)
            score_node.insert(part1_index + 1, cello_element)
        else:
            score_node.append(cello_element)

    # 2. Locate Staff 1 to use as a structural template
    staff1 = score_node.find("./Staff[@id='1']")
    if staff1 is None:
        return False
        
    staff2 = score_node.find("./Staff[@id='2']")
    if staff2 is not None:
        score_node.remove(staff2)
        
    staff2 = ET.SubElement(score_node, "Staff", {"id": "2"})
    
    current_sigN = 4
    current_sigD = 4
    is_first_measure = True
    
    for orig_meas in staff1.findall("Measure"):
        dr_meas = ET.SubElement(staff2, "Measure")
        
        # Mirror all native measure attributes safely
        for key, val in orig_meas.attrib.items():
            dr_meas.set(key, val)
            
        dr_voice = ET.SubElement(dr_meas, "voice")
        
        # Track and clone underlying time signatures
        tsig = orig_meas.find(".//TimeSig")
        if tsig is not None:
            sigN_node = tsig.find("sigN")
            sigD_node = tsig.find("sigD")
            if sigN_node is not None and sigD_node is not None:
                current_sigN = int(sigN_node.text)
                current_sigD = int(sigD_node.text)
            
            dr_tsig = ET.SubElement(dr_voice, "TimeSig")
            ET.SubElement(dr_tsig, "sigN").text = str(current_sigN)
            ET.SubElement(dr_tsig, "sigD").text = str(current_sigD)

        # 3. Parse total quarter notes in this measure
        total_quarters = int((current_sigN / current_sigD) * 4)
        if "len" in orig_meas.attrib:
            try:
                len_num, len_denom = map(int, orig_meas.attrib["len"].split('/'))
                total_quarters = int((len_num / len_denom) * 4)
            except ValueError:
                pass

        # 4. Inject 1-quarter note drone chord and pad remaining space with quarter rests
        if total_quarters <= 1:
            remaining_quarters = total_quarters
        else:
            dr_chord = ET.SubElement(dr_voice, "Chord")
            ET.SubElement(dr_chord, "durationType").text = "quarter"
            ET.SubElement(dr_chord, "noStem").text = "1"
            
            if is_first_measure:
                dr_text = ET.SubElement(dr_chord, "StaffText")
                ET.SubElement(dr_text, "text").text = "pizz."
                is_first_measure = False

            dr_note = ET.SubElement(dr_chord, "Note")
            # Write out the dynamically verified midi_val (52 for E3)
            dr_note.text = ""  # Clean node whitespace spacing
            pitch_elem = ET.SubElement(dr_note, "pitch")
            pitch_elem.text = str(midi_val)
            
            # 14 corresponds to natural 'E' in MuseScore Tonal Pitch Class (tpc) architecture
            tpc_elem = ET.SubElement(dr_note, "tpc")
            tpc_elem.text = "14" 
            
            remaining_quarters = total_quarters - 1

        # Fill remaining time signature requirements strictly with quarter rests
        while remaining_quarters > 0:
            dr_rest = ET.SubElement(dr_voice, "Rest")
            ET.SubElement(dr_rest, "durationType").text = "quarter"
            remaining_quarters -= 1

        # Preserve structural layout tags like dotted bar lines at the very end of the voice
        for barline in orig_meas.findall(".//BarLine"):
            dr_barline = ET.SubElement(dr_voice, "BarLine")
            subtype = barline.find("subtype")
            if subtype is not None:
                ET.SubElement(dr_barline, "subtype").text = subtype.text
                
    return True


def run_flexible_geographic_trial():
    print("Initiating Case-Agnostic Geographic Performance Trial...")
    if not os.path.exists(MUSESCORE_PATH):
        print(f"❌ Error: Executable missing at {MUSESCORE_PATH}"); return

    targets = [
        {"book": "genesis", "chapter": "001", "folder": "genesis", "pitch": "e"},
        {"book": "psalms", "chapter": "001", "folder": "psalms", "pitch": "f#"}
    ]
    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir()]

    for t in targets:
        m_folder = next((s for s in subdirs if t["folder"] in s.name.lower()), None)
        if not m_folder: continue

        for f_path in m_folder.iterdir():
            if not f_path.is_file() or f_path.suffix.lower() != ".mscz": continue
            if not re.match(f"^{t['book']}-{t['chapter']}", f_path.name.lower()): continue

            mp3_out = f_path.with_suffix(".mp3")
            print(f"\n[TARGET MATCH] Processing: {m_folder.name}/{f_path.name}")
            
            t_dir = f_path.parent / f"temp_inspect_{f_path.stem}"
            if t_dir.exists(): shutil.rmtree(t_dir, ignore_errors=True)
            t_dir.mkdir(exist_ok=True)
            
            try:
                with zipfile.ZipFile(f_path, 'r') as z: z.extractall(t_dir)
                mscx_file = next(t_dir.glob("*.mscx"), None)
                if not mscx_file: continue
                
                tree = ET.parse(mscx_file); root = tree.getroot(); modified = False

                # Update Breath & Caesura Playback Pauses
                for b_node in root.findall(".//Breath"):
                    sym = b_node.find("symbol")
                    sym_txt = sym.text.lower() if (sym is not None and sym.text) else ""
                    p_val = PAUSE_TIMES["caesura"] if "caesura" in sym_txt else PAUSE_TIMES["breath"]
                    
                    p_node = b_node.find("pause")
                    if p_node is not None: p_node.text = p_val
                    else: ET.SubElement(b_node, "pause").text = p_val
                    modified = True

                # Inject Cello Drone
                if inject_native_musescore4_drone(root, t["pitch"]): modified = True

                if modified:
                    tree.write(mscx_file, encoding="utf-8", xml_declaration=True)
                    t_mscz = f_path.with_name(f"temp_trial_{f_path.name}")
                    
                    with zipfile.ZipFile(t_mscz, 'w', zipfile.ZIP_DEFLATED) as zw:
                        for p in t_dir.rglob("*"):
                            if p.is_file(): zw.write(p, p.relative_to(t_dir))

                    print("   Running MuseScore4.exe audio compiler...")
                    cmd = [MUSESCORE_PATH, "-o", str(mp3_out), str(t_mscz)]
                    res = subprocess.run(cmd, capture_output=True, text=True)
                    
                    if res.returncode == 0:
                        print(f"   ✅ MP3 Audio Generated Natively: {mp3_out.name}")
                    else:
                        print(f"   ❌ MuseScore Error: {res.stderr}")
            except Exception as e:
                print(f"   ❌ Parsing Exception: {e}")
            finally:
                time.sleep(0.5)
                print(f"   📁 Code inspection path left active at: {t_dir}")

if __name__ == "__main__":
    run_flexible_geographic_trial()
