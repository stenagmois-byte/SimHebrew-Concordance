import os

# Let's inspect the actual files inside the musicscores directory to see their exact naming pattern
for root, dirs, files in os.walk("./musicscores"):
    json_files = [f for f in files if f.endswith('.json')]
    if json_files:
        print(f"Sample filenames in {os.path.basename(root)}: {json_files[:3]}")
        break
