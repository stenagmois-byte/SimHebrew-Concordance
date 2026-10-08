# ==============================================================================
# batch_verse_agogic_compiler.py - Production Global Verse Agogic Compiler
# ==============================================================================
import os
import re
import json
import time
import shutil
import zipfile
import subprocess
from pathlib import Path
import xml.etree.ElementTree as ET

try:
    import mido
except ImportError:
    print("❌ Error: 'mido' library is missing. Install with: pip install mido")
    exit(1)

# ==============================================================================
# CONFIGURATION PARAMETERS
# ==============================================================================
SCORE_DIR = Path("./musicscores")
AUDIO_DIR = SCORE_DIR / "audio"
MAP_PATH = SCORE_DIR.parent / "book_map.json"

MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore4.exe"
FLUIDSYNTH_CMD = "fluidsynth"
FFMPEG_CMD = "ffmpeg"
SOUNDFONT_PATH = Path("FluidR3_GM.sf2")

# General MIDI Instrument Program
# 52 = Choir Aahs (Default Vocal)
# 1  = Acoustic Grand Piano
PLAYBACK_PROGRAM = 52  

# Agogic & Cadence Timing Parameters
SINGLE_SYLLABLE_ORNAMENT_SCALE = 1.80  # 1.8x expansion for single-syllable 8th/triplet ornaments

# Atnah / Ole ve-Yored (Major Mid-Verse Caesura)
ATNAH_NOTE_HOLD = 2.20                 # 2.2x hold on Atnah note
ATNAH_SILENCE_BEATS = 5                # ~2.5s silence for mid-verse reflection

# Zaqef-Qatan / Comma Breaths (Minor Breath Mark)
ZAQEF_NOTE_HOLD = 1.40                 # 1.4x hold on Breath note
ZAQEF_SILENCE_BEATS = 2                # ~1s silence after comma

# Silluq (Final Verse Resolution)
FINAL_VERSE_NOTE_HOLD = 2.20           # 2.2x hold on final verse note

OVERWRITE_EXISTING = False              # Overwrites old verse MP3s with new agogic audio


# ==============================================================================
# CORE ANALYSIS & MIDI PATCHING ROUTINES
# ==============================================================================
def analyze_mscx_syllable_ornaments(mscx_path):
    """
    Scans a verse .mscx XML file to identify single-syllable ornaments, 
    Atnah caesuras, and Breath mark commas.
    """
    tree = ET.parse(mscx_path)
    root = tree.getroot()
    
    ornament_note_indices = set()
    atnah_note_indices = set()
    zaqef_note_indices = set()
    
    global_note_idx = 0
    last_chord_idx = None
    current_syllable_group = []

    for elem in root.iter():
        tag_lower = elem.tag.lower()
        
        # 1. Track Chords and Syllable Melismas
        if tag_lower == "chord":
            last_chord_idx = global_note_idx

            text_nodes = elem.findall(".//text") + elem.findall(".//Text")
            lyric_text = "".join([t.text for t in text_nodes if t.text]).strip()
            has_text = bool(lyric_text and lyric_text not in ("_", "-", "—"))

            dur = (elem.findtext("durationType") or elem.findtext("durationtype") or "").strip().lower()
            has_tuplet = elem.find(".//Tuplet") is not None or elem.find(".//tuplet") is not None
            is_fast = dur in ("eighth", "8th", "16th", "32nd", "64th") or has_tuplet

            if has_text:
                if len(current_syllable_group) >= 2:
                    fast_indices = [idx for idx, fast in current_syllable_group if fast]
                    if len(fast_indices) >= 2:
                        for idx in fast_indices:
                            ornament_note_indices.add(idx)
                
                current_syllable_group = [(global_note_idx, is_fast)]
            else:
                current_syllable_group.append((global_note_idx, is_fast))

            global_note_idx += 1

        # 2. Track Breath Marks (Atnah vs Comma Breaths)
        elif tag_lower == "breath":
            symbol_nodes = elem.findall(".//symbol") + elem.findall(".//Symbol")
            symbol_text = "".join([s.text for s in symbol_nodes if s.text]).strip().lower()
            
            if "caesura" in symbol_text:
                if last_chord_idx is not None:
                    atnah_note_indices.add(last_chord_idx)
            elif "breathmarkcomma" in symbol_text or "comma" in symbol_text:
                if last_chord_idx is not None:
                    zaqef_note_indices.add(last_chord_idx)

    # Flush final group at end of verse
    if len(current_syllable_group) >= 2:
        fast_indices = [idx for idx, fast in current_syllable_group if fast]
        if len(fast_indices) >= 2:
            for idx in fast_indices:
                ornament_note_indices.add(idx)

    return ornament_note_indices, atnah_note_indices, zaqef_note_indices


def patch_and_scale_midi(input_mid, output_mid, ornament_indices, atnah_indices, zaqef_indices, program_number=PLAYBACK_PROGRAM):
    """
    Patches verse MIDI track with agogic multipliers and post-pause silence.
    """
    mid = mido.MidiFile(input_mid)
    
    atnah_silence_ticks = mid.ticks_per_beat * ATNAH_SILENCE_BEATS
    zaqef_silence_ticks = mid.ticks_per_beat * ZAQEF_SILENCE_BEATS

    for i, track in enumerate(mid.tracks):
        note_events = [msg for msg in track if msg.type in ('note_on', 'note_off')]
        if not note_events:
            continue

        new_track = mido.MidiTrack()
        for msg in track:
            if msg.type != 'program_change':
                new_track.append(msg)
                
        channels_used = {msg.channel for msg in track if hasattr(msg, 'channel')}
        for ch in channels_used:
            new_track.insert(0, mido.Message('program_change', program=program_number, channel=ch, time=0))

        note_ons = [msg for msg in new_track if msg.type == 'note_on' and msg.velocity > 0]
        num_notes = len(note_ons)

        note_counter = 0
        active_holds = {}

        for idx, msg in enumerate(new_track):
            if msg.type == 'note_on' and msg.velocity > 0:
                current_idx = note_counter
                note_counter += 1

                is_final_verse_note = (note_counter == num_notes)
                is_atnah_note = current_idx in atnah_indices
                is_zaqef_note = current_idx in zaqef_indices
                is_ornament = current_idx in ornament_indices

                mult = 1.0
                hold_type = None

                if is_final_verse_note:
                    mult = FINAL_VERSE_NOTE_HOLD
                elif is_atnah_note:
                    mult = ATNAH_NOTE_HOLD
                    hold_type = 'atnah'
                elif is_zaqef_note:
                    mult = ZAQEF_NOTE_HOLD
                    hold_type = 'zaqef'
                elif is_ornament:
                    mult = SINGLE_SYLLABLE_ORNAMENT_SCALE

                if mult > 1.0:
                    active_holds[msg.note] = (mult, hold_type)

            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                if msg.note in active_holds:
                    mult, hold_type = active_holds.pop(msg.note)
                    msg.time = int(msg.time * mult)

                    if (idx + 1) < len(new_track):
                        if hold_type == 'atnah':
                            new_track[idx + 1].time += atnah_silence_ticks
                        elif hold_type == 'zaqef':
                            new_track[idx + 1].time += zaqef_silence_ticks

        mid.tracks[i] = new_track

    mid.save(output_mid)


# ==============================================================================
# BATCH VERSE COMPILER ACROSS GEOGRAPHY
# ==============================================================================
def run_global_verse_compiler():
    print("🚀 Initializing Production Agogic Verse Compiler (~23,000 tracks)...")
    
    map_file = MAP_PATH if MAP_PATH.exists() else Path("book_map.json")
    if not map_file.exists():
        print(f"❌ Error: Central layout map missing at {map_file}")
        return

    with open(map_file, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    if not SCORE_DIR.exists():
        print(f"❌ Error: Music scores directory missing at {SCORE_DIR}")
        return

    processed_verses_count = 0
    skipped_count = 0

    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir() and d.name.upper() != "AUDIO"]
    mapped_folders = set(book_map.values())

    for folder_name in sorted(mapped_folders):
        matched_folder = next((d for d in subdirs if d.name.lower() == folder_name.lower()), None)
        if not matched_folder:
            continue

        print(f"\n📂 Entering Production Volume: [{matched_folder.name}]")

        for f_path in matched_folder.iterdir():
            if not f_path.is_file() or f_path.suffix.lower() != ".mscz":
                continue
            if f_path.name.startswith("temp_") or f_path.name.startswith("temp_trial_"):
                continue

            match = re.match(r"^([0-9a-zA-Z_-]+)-(\d{3})", f_path.name.lower())
            if not match:
                match = re.match(r"^([0-9a-zA-Z_-]+)_(\d{3})", f_path.name.lower())
            if not match:
                continue

            raw_prefix = match.group(1).replace("-", "_")
            book_prefix = raw_prefix.upper()
            chapter_num = int(match.group(2))

            expected_folder = book_map.get(book_prefix)
            if not expected_folder or expected_folder.lower() != matched_folder.name.lower():
                continue

            # Route to website directory structure: e.g. /audio/2 SAMUEL/
            web_folder_name = book_prefix.replace("_", " ").upper()
            book_audio_out_dir = AUDIO_DIR / web_folder_name
            book_audio_out_dir.mkdir(parents=True, exist_ok=True)

            formatted_book_name = book_prefix.replace("_", " ").title().replace(" ", "_")

            print(f"   📄 Processing Score: {f_path.name} ➔ /audio/{web_folder_name}/")

            unique_suffix = int(time.time())
            temp_extract_dir = matched_folder / f"temp_{f_path.stem}_{unique_suffix}"
            temp_extract_dir.mkdir(exist_ok=True)

            try:
                # 1. Extract chapter .mscx XML
                with zipfile.ZipFile(f_path, 'r') as z_ref:
                    z_ref.extractall(temp_extract_dir)

                mscx_files = list(temp_extract_dir.glob("*.mscx"))
                if not mscx_files:
                    continue

                mscx_file_path = mscx_files[0]
                tree = ET.parse(mscx_file_path)
                root = tree.getroot()

                # 2. Slice measures into verse buckets split by rests
                score_node = root.find("Score")
                if score_node is None:
                    continue
                staff1 = score_node.find("./Staff[@id='1']")
                if staff1 is None:
                    continue

                measures = staff1.findall("Measure")
                verse_buckets = []
                current_verse_measures = []

                for meas in measures:
                    current_verse_measures.append(meas)
                    has_rest = meas.find(".//Rest") is not None or meas.find(".//rest") is not None
                    if has_rest:
                        verse_buckets.append(current_verse_measures)
                        current_verse_measures = []
                if current_verse_measures:
                    verse_buckets.append(current_verse_measures)

                # 3. Process each verse bucket
                for v_idx, verse_measures in enumerate(verse_buckets, start=1):
                    verse_file_name = f"{formatted_book_name}_{chapter_num}_{v_idx}.mp3"
                    mp3_out_path = book_audio_out_dir / verse_file_name

                    if mp3_out_path.exists() and not OVERWRITE_EXISTING:
                        skipped_count += 1
                        continue

                    # Construct sliced verse XML tree
                    verse_root = ET.fromstring(ET.tostring(root))
                    verse_score = verse_root.find("Score")

                    for v_staff in verse_score.findall("Staff"):
                        for old_meas in list(v_staff):
                            v_staff.remove(old_meas)

                    staff1_target = verse_score.find("./Staff[@id='1']")
                    for orig_meas in verse_measures:
                        cloned_meas = ET.fromstring(ET.tostring(orig_meas))
                        
                        # Strip element IDs to prevent MuseScore render glitches
                        for parent in cloned_meas.iter():
                            eid_node = parent.find("eid")
                            if eid_node is not None:
                                parent.remove(eid_node)
                        staff1_target.append(cloned_meas)

                    v_prefix = f"temp_v_{v_idx}_{unique_suffix}"
                    sliced_mscx = temp_extract_dir / f"{v_prefix}.mscx"
                    verse_tree = ET.ElementTree(verse_root)
                    verse_tree.write(sliced_mscx, encoding="utf-8", xml_declaration=True)

                    # Analyze verse XML for agogic targets
                    ornament_indices, atnah_indices, zaqef_indices = analyze_mscx_syllable_ornaments(sliced_mscx)

                    temp_v_mid = temp_extract_dir / f"{v_prefix}.mid"
                    temp_v_patched_mid = temp_extract_dir / f"{v_prefix}_patched.mid"
                    temp_v_wav = temp_extract_dir / f"{v_prefix}.wav"

                    # Export raw verse MIDI via MuseScore CLI
                    cmd_mid = [MUSESCORE_PATH, "-o", str(temp_v_mid), str(sliced_mscx)]
                    res_mid = subprocess.run(cmd_mid, capture_output=True, text=True)
                    if res_mid.returncode != 0 or not temp_v_mid.exists():
                        print(f"      ❌ MuseScore Verse {v_idx} MIDI Export Failed")
                        continue

                    # Patch MIDI with agogic holds and silences
                    patch_and_scale_midi(
                        temp_v_mid,
                        temp_v_patched_mid,
                        ornament_indices,
                        atnah_indices,
                        zaqef_indices,
                        program_number=PLAYBACK_PROGRAM
                    )

                    # Synthesize via FluidSynth
                    cmd_synth = [
                        FLUIDSYNTH_CMD, "-ni", "-g", "1.0", "-r", "44100",
                        "-R", "1", "-C", "1",
                        "-F", str(temp_v_wav), str(SOUNDFONT_PATH), str(temp_v_patched_mid)
                    ]
                    res_synth = subprocess.run(cmd_synth, capture_output=True, text=True)
                    if res_synth.returncode != 0 or not temp_v_wav.exists():
                        print(f"      ❌ FluidSynth Verse {v_idx} Synthesis Failed")
                        continue

                    # Encode MP3 via FFmpeg
                    cmd_mp3 = [
                        FFMPEG_CMD, "-y", "-i", str(temp_v_wav),
                        "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_out_path)
                    ]
                    res_mp3 = subprocess.run(cmd_mp3, capture_output=True, text=True)
                    if res_mp3.returncode != 0 or not mp3_out_path.exists():
                        print(f"      ❌ FFmpeg Verse {v_idx} Encoding Failed")
                        continue

                    print(f"      🎯 Verse {v_idx}: Ornaments: {len(ornament_indices)} | Atnahs: {len(atnah_indices)} | Breaths: {len(zaqef_indices)} ➔ {mp3_out_path.name}")
                    processed_verses_count += 1

            except Exception as e:
                print(f"   ❌ Exception processing score {f_path.name}: {e}")

            finally:
                time.sleep(0.05)
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)

    print(f"\n🎉 Global Verse Compilation Complete!")
    print(f"   • Replaced/Generated: {processed_verses_count} verse MP3 files")
    print(f"   • Skipped: {skipped_count} existing files")

if __name__ == "__main__":
    run_global_verse_compiler()