import xml.etree.ElementTree as ET
from collections import Counter

def extract_musical_sequence(xml_file_path):
    """
    Parses the music XML tree from your local directory and extracts 
    the sequential list of musical notes/accents.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        return []

    sequence = []
    
    # Traverses the note elements in the chapter file
    for note in root.iter('note'):
        # Skip rest markings to keep the track purely melodic
        if note.find('rest') is not None:
            continue
            
        pitch = note.find('pitch')
        if pitch is not None:
            step = pitch.find('step').text if pitch.find('step') is not None else ''
            octave = pitch.find('octave').text if pitch.find('octave') is not None else ''
            alter = pitch.find('alter').text if pitch.find('alter') is not None else ''
            
            # Formulate the explicit pitch token (e.g., "G#4", "E4")
            alter_sign = "#" if alter == "1" else ("b" if alter == "-1" else "")
            note_token = f"{step}{alter_sign}{octave}"
            if step: 
                sequence.append(note_token)
                
    return sequence

def find_structural_motifs(sequence, motif_length=3):
    """
    Filters out static syllable counts by compressing consecutive identical pitches.
    Then, extracts the underlying cadence patterns using a moving window.
    """
    if not sequence:
        return Counter()
        
    # Step 1: Melodic Reduction (Ignore note-holds, isolate the step intervals)
    reduced_sequence = [sequence[0]]
    for note in sequence[1:]:
        if note != reduced_sequence[-1]:
            reduced_sequence.append(note)
            
    print(f"Reduced Sequence Length (Pitch Shifts Only): {len(reduced_sequence)}")
    print(f"First 10 distinct pitch shifts: {' -> '.join(reduced_sequence[:10])}\n")
    
    # Step 2: Assemble moving window clusters
    if len(reduced_sequence) < motif_length:
        return Counter()
        
    motifs = []
    for i in range(len(reduced_sequence) - motif_length + 1):
        sub_seq = tuple(reduced_sequence[i:i+motif_length])
        motifs.append(sub_seq)
        
    return Counter(motifs)

# ==========================================================================
# LOCAL ENVIRONMENT EXECUTION RUNNER
# ==========================================================================

# Your specific local computer directory path for Psalm 96
xml_path = "C:/Users/Bob/OneDrive/Documents/GitHub/SimHebrew-Concordance/musicscores/The Psalms/PSALMS-096.xml"

print(f"Targeting Local File: {xml_path}")
full_melody = extract_musical_sequence(xml_path)

if full_melody:
    print(f"Total Raw Syllable Ticks: {len(full_melody)}")
    print("-" * 50)

    # Process 3-note pitch shifts
    print("--- Top 5 Recurring 3-Note Pitch Contours ---")
    three_note_shifts = find_structural_motifs(full_melody, motif_length=3)
    for motif, count in three_note_shifts.most_common(5):
        print(f"Contour: {' -> '.join(motif)} | Occurrences: {count}")

    print("\n" + "-" * 50)

    # Process 4-note pitch shifts
    print("--- Top 5 Recurring 4-Note Pitch Contours ---")
    four_note_shifts = find_structural_motifs(full_melody, motif_length=4)
    for motif, count in four_note_shifts.most_common(5):
        print(f"Contour: {' -> '.join(motif)} | Occurrences: {count}")
else:
    print("No notes found. Please check that the file path or XML tag names match your dataset.")
