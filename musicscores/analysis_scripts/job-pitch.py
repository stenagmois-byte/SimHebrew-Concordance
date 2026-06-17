from music21 import converter, note

# Load Job 3 using the path configuration we established
score = converter.parse("../Job/JOB-003.mxl")

# Flatten the stream to isolate all individual notes (ignoring rests for pitch weight)
all_notes = list(score.recurse().getElementsByClass(note.Note))
total_notes = len(all_notes)

# Count how many times each pitch class appears
pitch_counts = {}
for n in all_notes:
    p_name = n.pitch.name  # e.g., 'A', 'E', 'G'
    pitch_counts[p_name] = pitch_counts.get(p_name, 0) + 1

print("==================================================")
print("     JOB 3: PITCH DISTRIBUTION ANALYSIS           ")
print("==================================================\n")
print(f"Total melodic notes analyzed: {total_notes}")
print("Frequency of each note in the chapter:")

# Sort by most frequent note to see if 'A' dominates the axis
for pitch, count in sorted(pitch_counts.items(), key=lambda item: item[1], reverse=True):
    percentage = (count / total_notes) * 100
    marker = " ◄ (Recitation Axis)" if pitch == 'A' else ""
    print(f"  • Note {pitch}: {count} times ({percentage:.1f}% of total score){marker}")
