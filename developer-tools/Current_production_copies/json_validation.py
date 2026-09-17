import json
from pathlib import Path

# --- Path Configurations ---
REPO_ROOT = Path(r"C:\Users\Bob\OneDrive\Documents\GitHub\SimHebrew-Concordance")
SCORE_DIR = REPO_ROOT / "musicscores"

def run_concordance_json_validator():
    print("🔍 Initializing Structural Array Matrix Soundness Validator...\n")
    
    flagged_count = 0
    total_checked = 0

    # Scan all book directories inside the musicscores environment
    json_files = list(SCORE_DIR.rglob("*.json"))
    
    if not json_files:
        print("❌ Error: No JSON data resource files found in target architecture.")
        return

    for json_path in sorted(json_files):
        # Skip map and config templates
        if "book_map" in json_path.name or "package" in json_path.name:
            continue
            
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # Gracefully handle single objects or nested lists depending on your schema
            records = data if isinstance(data, list) else data.get("verses", [])
            
            for idx, record in enumerate(records, start=1):
                total_checked += 1
                
                # Extract text and music tokens safely
                hebrew_text = record.get("withoutVowels", record.get("text", ""))
                pitches = record.get("pitches", record.get("notes", [])) 
                
                # If your JSON uses a flat string layout for notes, split it up
                if isinstance(pitches, str):
                    pitches = pitches.split()

                word_count = len(hebrew_text.split())
                pitch_count = len(pitches)

                if word_count == 0:
                    continue

                # 🎯 THE ANOMALY FILTER RULE
                # Standard structural chants average 1 to 2.5 pitch tones per word.
                # Anything exceeding 4.5 pitches per word indicates a leaked/corrupt chapter array loop!
                ratio = pitch_count / word_count
                
                if ratio > 4.5:
                    flagged_count += 1
                    location = record.get("location", f"{json_path.stem} V:{idx}")
                    print(f"🚨 ALERT: Data Corruption Mismatch Detected in [{location}]")
                    print(f"   ↳ File Location: {json_path.relative_to(REPO_ROOT)}")
                    print(f"   ↳ Hebrew Text: {word_count} words ↔️ Music Track: {pitch_count} pitches (Ratio: {ratio:.2f} notes/word)")
                    print(f"   ↳ Sample Pitches: {pitches[:10]}...\n")

        except Exception as e:
            print(f"⚠️  Skipping File Parse Error on {json_path.name}: {e}")

    print("──────────────────────────────────────────────────")
    print(f"🏁 Soundness Validation Sweep Concluded.")
    print(f"   Total Unique Verse Nodes Checked: {total_checked}")
    print(f"   Total Structural Malformations Identified: {flagged_count}")

if __name__ == "__main__":
    run_concordance_json_validator()
