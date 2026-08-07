import subprocess
import re

def detect_audio_boundaries(input_video):
    # -50dB threshold, requiring at least 0.5 seconds of silence to trigger
    command = [
        'ffmpeg', '-i', input_video, 
        '-af', 'silencedetect=noise=-50dB:d=0.5', 
        '-f', 'null', '-'
    ]
    
    result = subprocess.run(command, stderr=subprocess.PIPE, text=True)
    stderr_output = result.stderr

    # 1. Find where the opening silence ends (Music Starts)
    # Looks for the very first 'silence_end' line
    start_match = re.search(r'silence_end: (\d+(\.\d+)?)', stderr_output)
    music_start = float(start_match.group(1)) if start_match else 0.0

    # 2. Find where the closing silence begins (Music Stops)
    # Looks for the very last 'silence_start' line
    end_matches = re.findall(r'silence_start: (\d+(\.\d+)?)', stderr_output)
    music_end = float(end_matches[-1][0]) if end_matches else None

    return music_start, music_end

def trim_video(input_video, output_video, start_time, end_time):
    command = [
        'ffmpeg', '-y',
        '-ss', str(start_time),     # Dynamic start time
        '-to', str(end_time),       # Dynamic end time
        '-i', input_video,
        '-c:v', 'libx264',          # Re-encoding guarantees frames match audio
        '-c:a', 'aac', 
        output_video
    ]
    subprocess.run(command, check=True)
    print(f"Successfully trimmed! Extracted audio from {start_time}s to {end_time}s.")

# Execution
video_file = 'JOSHUA_009_024.mp4'
start_ts, end_ts = detect_audio_boundaries(video_file)

if end_ts:
    trim_video(video_file, 'trimmed_JOSHUA_009_024.mp4', start_time=start_ts, end_time=end_ts)
else:
    print("Could not reliably detect the end of the music.")
