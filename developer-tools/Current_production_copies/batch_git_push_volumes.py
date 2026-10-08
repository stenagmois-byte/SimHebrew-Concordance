# ==============================================================================
# batch_git_push_volumes.py - Volume-by-Volume Staged Commit & Push Script
# ==============================================================================
import json
import os
import subprocess
import time
from pathlib import Path

# Paths
SCORE_DIR = Path("musicscores")
MAP_PATH = Path("book_map.json")

MAX_RETRIES = 5       # Retries if Wi-Fi or GitHub connection drops
RETRY_DELAY = 15      # Pause in seconds before retrying push

def run_cmd(cmd):
    """Executes a shell command and returns success status and output."""
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0, res.stdout + res.stderr

def main():
    if not MAP_PATH.exists():
        print(f"❌ Error: Could not find {MAP_PATH.resolve()}")
        return

    # Load book_map.json to extract all unique volume directory names
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        book_map = json.load(f)

    # Get sorted list of unique volume folders (e.g., 'Chronicles', 'The Twelve', 'Genesis')
    unique_volumes = sorted(list(set(book_map.values())))
    print(f"📦 Found {len(unique_volumes)} unique volume directories in layout map...\n")

    for idx, volume_name in enumerate(unique_volumes, start=1):
        volume_dir = SCORE_DIR / volume_name
        
        print(f"--------------------------------------------------")
        print(f"[{idx}/{len(unique_volumes)}] Processing Volume: {volume_name}")
        print(f"--------------------------------------------------")

        if not volume_dir.exists():
            print(f"  ⚠️ Directory not found on disk: {volume_dir}. Skipping...")
            continue

        # 1. Stage all files in this specific volume directory
        # Quoting handles spaces cleanly (e.g., "musicscores/The Twelve/*")
        stage_cmd = f'git add "musicscores/{volume_name}/*"'
        print(f"  📥 Staging files for volume: musicscores/{volume_name}/")
        run_cmd(stage_cmd)

        # 2. Check if there are staged changes ready to commit
        status_ok, status_out = run_cmd("git status --porcelain")
        if not status_out.strip():
            print(f"  ℹ️ No new or modified files found in {volume_name}. Skipping...")
            continue

        # 3. Create a local commit for this volume
        commit_msg = f"Add chapter MP3s and scores for volume: {volume_name}"
        print(f"  📝 Committing: '{commit_msg}'")
        commit_ok, commit_out = run_cmd(f'git commit -m "{commit_msg}"')

        if not commit_ok:
            print(f"  ⚠️ Commit skipped or no changes detected.")
            continue

        # 4. Push loop with network retry logic
        pushed = False
        for attempt in range(1, MAX_RETRIES + 1):
            print(f"  🚀 Pushing {volume_name} to GitHub (Attempt {attempt}/{MAX_RETRIES})...")
            push_ok, push_out = run_cmd("git push")

            if push_ok:
                print(f"  ✅ Successfully pushed volume: {volume_name}!")
                pushed = True
                break
            else:
                print(f"  ⚠️ Push failed (Network drop or timeout). Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

        if not pushed:
            print(f"  ❌ Could not push {volume_name} after {MAX_RETRIES} attempts. Continuing to next volume...")

        # Small pause between uploads
        time.sleep(2)

    print("\n==================================================")
    print("🎉 Staged Volume Commit & Push Process Complete!")
    print("==================================================")

if __name__ == "__main__":
    main()