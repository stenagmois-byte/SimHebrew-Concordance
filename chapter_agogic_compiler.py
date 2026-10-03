# ==============================================================================
# batch_agogic_compiler.py - Production Multi-Volume Agogic Compiler
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
MAP_PATH = SCORE_DIR.parent / "book_map.json"  # Falls back to ./book_map.json if needed

MUSESCORE_PATH = r"C:\Program Files\MuseScore 4\bin\musescore4.exe"
FLUIDSYNTH_CMD = "fluidsynth"
FFMPEG_CMD = "ffmpeg"
SOUNDFONT_PATH = Path("FluidR3_GM.sf2")

# --- General MIDI Program Numbers ---
# 52 = Choir Aahs (Default Vocal)
# 53 = Voice Oohs
# 1  = Acoustic Grand Piano (For piano web playback option)
PLAYBACK_PROGRAM = 52  

# --- Agogic & Cadence Timing Parameters ---
SINGLE_SYLLABLE_ORNAMENT_SCALE = 1.80  # 1.8x expansion for single-syllable 8th/triplet ornaments

# Atnah / Ole ve-Yored (Major Mid-Verse Caesura)
ATNAH_NOTE_HOLD = 2.20                 # 2.2x hold on Atnah note
ATNAH_SILENCE_BEATS = 5                # ~2.5s silence for mid-verse reflection

# Zaqef-Qatan (Minor Breath Mark Comma)
ZAQEF_NOTE_HOLD = 1.40                 # 1.4x hold on Zaqef-Qatan note
ZAQEF_SILENCE_BEATS = 2                # ~1s silence after comma

# Silluq (Final Verse Resolution)
FINAL_VERSE_NOTE_HOLD = 2.20           # 2.2x hold on final verse note

OVERWRITE_EXISTING = True              # Set to True to replace existing chapter MP3s


# ==============================================================================
# CORE ANALYSIS & MIDI PATCHING ROUTINES
# ==============================================================================
def analyze_mscx_syllable_ornaments(mscx_path):
    """
    Scans the .mscx XML file to identify single-syllable ornaments, Atnah caesuras, 
    and Zaqef-Qatan breath mark commas.
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

        # 2. Track Breath Marks (Atnah / Ole ve-Yored vs Zaqef-Qatan)
        elif tag_lower == "breath":
            symbol_nodes = elem.findall(".//symbol") + elem.findall(".//Symbol")
            symbol_text = "".join([s.text for s in symbol_nodes if s.text]).strip().lower()
            
            if "caesura" in symbol_text:
                if last_chord_idx is not None:
                    atnah_note_indices.add(last_chord_idx)
            elif "breathmarkcomma" in symbol_text or "comma" in symbol_text:
                if last_chord_idx is not None:
                    zaqef_note_indices.add(last_chord_idx)

    # Flush final group at end of score
    if len(current_syllable_group) >= 2:
        fast_indices = [idx for idx, fast in current_syllable_group if fast]
        if len(fast_indices) >= 2:
            for idx in fast_indices:
                ornament_note_indices.add(idx)

    return ornament_note_indices, atnah_note_indices, zaqef_note_indices


def patch_and_scale_midi(input_mid, output_mid, ornament_indices, atnah_indices, zaqef_indices, program_number=PLAYBACK_PROGRAM):
    """
    Patches MIDI track:
    - Sets General MIDI instrument program
    - Expands single-syllable 8th/triplet ornament durations (1.8x)
    - Applies Atnah and Zaqef-Qatan note holds and post-pause silence
    - Holds the final verse note (Silluq) into the trailing rest
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
        active_holds = {}  # {pitch: (multiplier, hold_type)}

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
# BATCH COMPILATION WRAPPER Across GEOGRAPHY
# ==============================================================================
def run_batch_compilation():
    print("🚀 Initializing Production Agogic Batch Audio Compiler...")
    
    map_file = MAP_PATH if MAP_PATH.exists() else Path("book_map.json")
    if not map_file.exists():
        print(f"❌ Error: Central layout map missing at {map_file}")
        return

    with open(map_file, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    if not SCORE_DIR.exists():
        print(f"❌ Error: Music scores directory missing at {SCORE_DIR}")
        return

    processed_count = 0
    skipped_count = 0

    subdirs = [d for d in SCORE_DIR.iterdir() if d.is_dir()]
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
                continue

            raw_prefix = match.group(1).replace("-", "_")
            book_prefix = raw_prefix.upper()
            chapter_num = match.group(2)

            expected_folder = book_map.get(book_prefix)
            if not expected_folder or expected_folder.lower() != matched_folder.name.lower():
                continue

            mp3_out = matched_folder / f"{book_prefix}-{chapter_num}.mp3"

            if mp3_out.exists() and not OVERWRITE_EXISTING:
                print(f"   ⏩ Skipping: {f_path.name} (MP3 already exists)")
                skipped_count += 1
                continue

            print(f"   📄 Processing Chapter: {f_path.name}")
            
            unique_suffix = int(time.time())
            temp_extract_dir = matched_folder / f"temp_{f_path.stem}_{unique_suffix}"
            temp_extract_dir.mkdir(exist_ok=True)

            temp_mid = matched_folder / f"temp_agogic_{f_path.stem}.mid"
            temp_patched_mid = matched_folder / f"temp_agogic_patched_{f_path.stem}.mid"
            temp_wav = matched_folder / f"temp_agogic_{f_path.stem}.wav"

            try:
                # 1. Unzip to read .mscx XML for ornament & breath mark analysis
                with zipfile.ZipFile(f_path, 'r') as z_ref:
                    z_ref.extractall(temp_extract_dir)

                mscx_files = list(temp_extract_dir.glob("*.mscx"))
                if not mscx_files:
                    print(f"   ⚠️ Skipping: Could not locate .mscx inside {f_path.name}")
                    continue

                ornament_indices, atnah_indices, zaqef_indices = analyze_mscx_syllable_ornaments(mscx_files[0])

                print(f"      🎯 Ornaments: {len(ornament_indices)} | Atnahs: {len(atnah_indices)} | Breaths: {len(zaqef_indices)}")
                # 2. Export raw MIDI via MuseScore CLI
                cmd_mid = [MUSESCORE_PATH, "-o", str(temp_mid), str(f_path)]
                res_mid = subprocess.run(cmd_mid, capture_output=True, text=True)
                if res_mid.returncode != 0 or not temp_mid.exists():
                    print(f"   ❌ MuseScore MIDI Export Failed: {res_mid.stderr}")
                    continue

                # 3. Apply Agogic MIDI Patching
                patch_and_scale_midi(
                    temp_mid,
                    temp_patched_mid,
                    ornament_indices,
                    atnah_indices,
                    zaqef_indices,
                    program_number=PLAYBACK_PROGRAM
                )

                # 4. Synthesize Audio via FluidSynth
                cmd_synth = [
                    FLUIDSYNTH_CMD, "-ni", "-g", "1.0", "-r", "44100",
                    "-R", "1", "-C", "1",
                    "-F", str(temp_wav), str(SOUNDFONT_PATH), str(temp_patched_mid)
                ]
                res_synth = subprocess.run(cmd_synth, capture_output=True, text=True)
                if res_synth.returncode != 0 or not temp_wav.exists():
                    print(f"   ❌ FluidSynth Synthesis Failed: {res_synth.stderr}")
                    continue

                # 5. Encode 192k MP3 via FFmpeg (Overwrites target MP3)
                cmd_mp3 = [
                    FFMPEG_CMD, "-y", "-i", str(temp_wav),
                    "-codec:a", "libmp3lame", "-b:a", "192k", str(mp3_out)
                ]
                res_mp3 = subprocess.run(cmd_mp3, capture_output=True, text=True)
                if res_mp3.returncode != 0 or not mp3_out.exists():
                    print(f"   ❌ FFmpeg Encoding Failed: {res_mp3.stderr}")
                    continue

                print(f"      ✅ Successfully generated & replaced: {mp3_out.name}")
                processed_count += 1

            except Exception as e:
                print(f"   ❌ Exception processing {f_path.name}: {e}")

            finally:
                time.sleep(0.1)
                for p in [temp_mid, temp_patched_mid, temp_wav]:
                    if p.exists():
                        try:
                            p.unlink()
                        except Exception:
                            pass
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir, ignore_errors=True)

    print(f"\n🎉 Global Batch Compilation Complete!")
    print(f"   • Replaced/Generated: {processed_count} MP3 files")
    print(f"   • Skipped: {skipped_count} existing files")

if __name__ == "__main__":
    run_batch_compilation()