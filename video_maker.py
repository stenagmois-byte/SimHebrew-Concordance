# ==============================================================================
# video_maker.py - Synchronized Video Generator (25 FPS CFR Fixed)
# ==============================================================================
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from PIL import Image

# --- Configuration Paths ---
FFMPEG_CMD = "ffmpeg"

EPUB_PATH = Path(r"C:\Users\Bob\Calibre Library\D. Robert MacDonald\Kindle-epubs\Chronicles-MotB-Kindle.epub")
AUDIO_DIR = Path(r"musicscores\audio\1 CHRONICLES")

BOOK_PREFIX = "1-CHRONICLES"
CHAPTER_NUM = 1

OUTPUT_MP4 = AUDIO_DIR / f"1_Chronicles_{CHAPTER_NUM}.mp4"

AUDIO_TRIM_FILTER = "silenceremove=stop_periods=-1:stop_duration=0.5:stop_threshold=-40dB"

# Standard HD video canvas dimensions for score lines
CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 400


def prepare_white_canvas_image(src_png, dst_png):
    """
    Pastes transparent PNG score lines onto a solid white canvas to prevent
    black-on-black video encoding issues and unify image dimensions.
    """
    with Image.open(src_png) as img:
        img = img.convert("RGBA")
        
        # Calculate scaling to fit cleanly inside canvas with padding
        max_w = CANVAS_WIDTH - 80
        max_h = CANVAS_HEIGHT - 40
        
        aspect = img.width / img.height
        new_w = min(img.width, max_w)
        new_h = int(new_w / aspect)
        
        if new_h > max_h:
            new_h = max_h
            new_w = int(new_h * aspect)
            
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # Create pure white background canvas
        canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), (255, 255, 255))
        
        # Center the score line on the white canvas
        offset_x = (CANVAS_WIDTH - new_w) // 2
        offset_y = (CANVAS_HEIGHT - new_h) // 2
        
        canvas.paste(img_resized, (offset_x, offset_y), img_resized)
        canvas.save(dst_png, "PNG")


def get_trimmed_audio_duration(input_mp3, trimmed_mp3):
    """
    Trims trailing silence from a verse MP3 and parses exact duration from FFmpeg output.
    """
    cmd_trim = [
        FFMPEG_CMD, "-y",
        "-i", str(input_mp3),
        "-af", AUDIO_TRIM_FILTER,
        str(trimmed_mp3)
    ]
    subprocess.run(cmd_trim, capture_output=True, text=True, check=True)

    cmd_info = [FFMPEG_CMD, "-i", str(trimmed_mp3)]
    res = subprocess.run(cmd_info, capture_output=True, text=True)
    
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", res.stderr + res.stdout)
    if match:
        h, m, s = match.groups()
        duration = float(h) * 3600 + float(m) * 60 + float(s)
        if duration > 0:
            return duration

    raise RuntimeError(f"Could not determine duration for: {trimmed_mp3.name}")


def build_video_from_epub():
    print(f"🎬 Building {BOOK_PREFIX} Chapter {CHAPTER_NUM} Video...")
    
    if not EPUB_PATH.exists():
        print(f"❌ Could not find EPUB file at: {EPUB_PATH}")
        return

    # 1. Locate verse MP3s
    verse_mp3s = sorted(
        [f for f in AUDIO_DIR.glob("*.mp3") if re.search(rf"_{CHAPTER_NUM}_\d+\.mp3$", f.name, re.IGNORECASE)],
        key=lambda x: int(re.search(r"_(\d+)\.mp3$", x.name).group(1))
    )

    if not verse_mp3s:
        print(f"❌ No verse MP3 files found in: {AUDIO_DIR}")
        return

    print(f"   Found {len(verse_mp3s)} verse MP3 tracks.")

    temp_dir = AUDIO_DIR / f"temp_epub_vid_{CHAPTER_NUM}"
    temp_dir.mkdir(parents=True, exist_ok=True)
    extracted_img_dir = temp_dir / "extracted_images"
    prepared_img_dir = temp_dir / "prepared_images"
    extracted_img_dir.mkdir(exist_ok=True)
    prepared_img_dir.mkdir(exist_ok=True)

    try:
        print(f"📦 Indexing images from {EPUB_PATH.name}...")
        chapter_str = f"{CHAPTER_NUM:03d}"
        img_pattern = re.compile(rf"{BOOK_PREFIX}-{chapter_str}-(\d+)(?:-(\d+))?\.png$", re.IGNORECASE)

        verse_image_map = {}

        with zipfile.ZipFile(EPUB_PATH, 'r') as z:
            for member in z.namelist():
                filename = Path(member).name
                match = img_pattern.match(filename)
                if match:
                    v_num = int(match.group(1))
                    part_num = int(match.group(2)) if match.group(2) else 1
                    
                    extracted_path = z.extract(member, extracted_img_dir)
                    
                    if v_num not in verse_image_map:
                        verse_image_map[v_num] = []
                    verse_image_map[v_num].append((part_num, Path(extracted_path)))

        print(f"   Mapped images for {len(verse_image_map)} distinct verses.")

        concat_img_manifest = temp_dir / "images_concat.txt"
        concat_audio_manifest = temp_dir / "audio_concat.txt"

        last_valid_img = None

        with open(concat_img_manifest, "w", encoding="utf-8") as f_img, \
             open(concat_audio_manifest, "w", encoding="utf-8") as f_aud:

            for idx, raw_mp3 in enumerate(verse_mp3s, start=1):
                trimmed_mp3 = temp_dir / f"trimmed_{idx}.mp3"
                total_verse_dur = get_trimmed_audio_duration(raw_mp3, trimmed_mp3)

                clean_aud_path = str(trimmed_mp3.resolve()).replace("\\", "/")
                f_aud.write(f"file '{clean_aud_path}'\n")

                if idx in verse_image_map:
                    parts = sorted(verse_image_map[idx], key=lambda x: x)
                    dur_per_part = total_verse_dur / len(parts)

                    for part_num, src_img_path in parts:
                        prep_img_path = prepared_img_dir / f"canvas_v{idx}_p{part_num}.png"
                        prepare_white_canvas_image(src_img_path, prep_img_path)

                        clean_img_path = str(prep_img_path.resolve()).replace("\\", "/")
                        f_img.write(f"file '{clean_img_path}'\n")
                        f_img.write(f"duration {dur_per_part:.3f}\n")
                        last_valid_img = clean_img_path

            if last_valid_img:
                f_img.write(f"file '{last_valid_img}'\n")

        # 3. Concatenate trimmed verse audio
        combined_audio = temp_dir / "full_chapter_audio.mp3"
        cmd_join_audio = [
            FFMPEG_CMD, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_audio_manifest),
            "-c", "copy",
            str(combined_audio)
        ]
        subprocess.run(cmd_join_audio, check=True)

        # 4. Multiplex video with forced 25 FPS CFR
        cmd_mp4 = [
            FFMPEG_CMD, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_img_manifest),
            "-i", str(combined_audio),
            "-vf", "fps=25,scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-tune", "stillimage", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-r", "25",
            "-shortest",
            str(OUTPUT_MP4)
        ]

        print("🎬 Multiplexing verse images and audio into 25 FPS MP4...")
        subprocess.run(cmd_mp4, check=True)
        print(f"✅ Success! Frame-accurate video created at:\n   {OUTPUT_MP4}")

    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    build_video_from_epub()
