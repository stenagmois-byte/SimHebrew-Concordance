import os
import zipfile
import xml.etree.ElementTree as ET
from music21 import converter, note

# Main musicscores directory path (one level up from analysis_scripts)
BASE_DIR = "../"

print("==========================================================")
print("  SCANNING ALL 929 CHAPTERS FOR THE DIVINE 'C -> A' BREAK ")
print("==========================================================\n")

# Loop through every directory under musicscores
for root_dir, dirs, files in os.walk(BASE_DIR):
    # Skip the analysis folder itself
    if "analysis_scripts" in root_dir:
        continue
        
    for filename in sorted(files):
        if filename.lower().endswith('.mxl'):
            file_path = os.path.join(root_dir, filename)
            
            try:
                # Load file into music21
                score = converter.parse(file_path)
                all_notes = list(score.recurse().getElementsByClass(note.Note))
                
                # Scan note sequence for direct C -> A jump
                for i in range(len(all_notes) - 1):
                    current_pitch = all_notes[i].pitch.name
                    next_pitch = all_notes[i+1].pitch.name
                    
                    if current_pitch == 'C' and next_pitch == 'A':
                        book_name = os.path.basename(root_dir)
                        print(f"🚨 EXCEPTION FOUND in Book: {book_name} | File: {filename}")
                        
                        # Grab surrounding word context if lyrics exist
                        words = []
                        context_window = all_notes[max(0, i-2) : min(len(all_notes), i+4)]
                        for n in context_window:
                            lyric = "/".join([l.text for l in n.lyrics if l.text]) if n.lyrics else "_"
                            words.append(f"{n.pitch.nameWithOctave}({lyric})")
                        
                        print(f"   Context: {' -> '.join(words)}\n")
                        
            except Exception:
                # Silently skip any file errors to keep the scan moving smoothly
                continue
