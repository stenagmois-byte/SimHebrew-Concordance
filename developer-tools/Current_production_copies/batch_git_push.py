# ==============================================================================
# batch_git_push.py - Overnight Book-by-Book Git Commit & Push Automation
# ==============================================================================
import os
import subprocess
import time
from pathlib import Path

# Path to audio folder
AUDIO_DIR = Path("musicscores/audio")
MAX_RETRIES = 5       # Max retries if network drops during git push
RETRY_DELAY = 15      # Wait 15 seconds before retrying network upload

def run_cmd(cmd):
    """Executes a shell command and returns success status."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0, res.stdout + res.stderr

def main():
    if not AUDIO_DIR.exists():
        print(f"❌ Error: Could not find audio directory at {AUDIO_DIR.resolve()}")
        return

    # Find all subdirectories inside musicscores/audio/
    book_dirs = [d for d in AUDIO_DIR.iterdir() if d.is_dir()]
    print(f"📚 Found {len(book_dirs)} book folders to process...\n")

    for idx, book_path in enumerate(sorted(book_dirs), start=1):
        book_name = book_path.name
        print(f"--------------------------------------------------")
        print(f"[{idx}/{len(book_dirs)}] Processing Book: {book_name}")
        print(f"--------------------------------------------------")

        # 1. Stage the MP3 files for this specific book
        add_pattern = f'musicscores/audio/{book_name}/*.mp3'
        print(f"  📥 Staging files: {add_pattern}")
        run_cmd(f'git add "{add_pattern}"')

        # 2. Check if there are changes to commit
        status_ok, status_out = run_cmd("git status --porcelain")
        if not status_out.strip():
            print(f"  ℹ️ No new changes found for {book_name}. Skipping...")
            continue

        # 3. Create the local commit
        commit_msg = f"Add agogic verse MP3s for {book_name}"
        print(f"  📝 Committing: '{commit_msg}'")
        commit_ok, commit_out = run_cmd(f'git commit -m "{commit_msg}"')
        
        if not commit_ok:
            print(f"  ⚠️ Commit skipped or nothing to commit.")
            continue

        # 4. Push with automatic network retry loop
        pushed = False
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"  🚀 Uploading to GitHub (Attempt {attempt}/{MAX_RETRIES})...")
            push_ok, push_out = run_cmd("git push")
            
            if push_ok:
                print(f"  ✅ Successfully pushed {book_name}!")
                pushed = True
                break
            else:
                print(f"  ⚠️ Push failed (Network drop/timeout). Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

        if not pushed:
            print(f"  ❌ Could not push {book_name} after {MAX_RETRIES} attempts. Moving to next book...")

        # Small pause between books to let network sockets settle
        time.sleep(2)

    print("\n==================================================")
    print("🎉 Overnight Batch Commit & Push Complete!")
    print("==================================================")

if __name__ == "__main__":
    main()