import os
import re

# Targeting your musicscores directory
root_dir = "./musicscores" 

print("=== STARTING DIRECTORY SCAN SIMULATION ===")

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename == "index.html":
            file_path = os.path.join(dirpath, filename)
            print(f"\n📂 Found index file at: {file_path}")
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                
                # Check each line to see if it matches our target code patterns
                for line_num, line in enumerate(lines, 1):
                    if '<td class="tdch4">JSON Data Tree</td>' in line:
                        print(f"   ✂️ MATCH FOUND (Header) on Line {line_num}: {line.strip()}")
                    
                    if 'class="tdcl4"' in line or '.json' in line:
                        print(f"   ✂️ MATCH FOUND (Data Row) on Line {line_num}: {line.strip()}")
                        
            except Exception as e:
                print(f"   ❌ Error reading file: {e}")

print("\n=== SIMULATION COMPLETE ===")
print("No files were modified during this run.")
