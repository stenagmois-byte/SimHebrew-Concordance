import os
import re

root_dir = "./musicscores" 
modified_count = 0

print("=== STARTING LIVE CLEANUP ===")

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename == "index.html":
            file_path = os.path.join(dirpath, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # 1. Remove the JSON header cell completely
            updated_content = content.replace(
                '<td class="tdch4">JSON Data Tree</td>', 
                ''
            )
            
            # 2. Remove any data cell matching the pattern <td class="tdcl4">...</td>
            # This handles any variations in spacing inside the cell
            updated_content = re.sub(
                r'<td class="tdcl4">.*?</td>\s*', 
                '', 
                updated_content
            )
            
            # Only save the file if modifications were actually made
            if updated_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print(f"✅ Cleaned and saved: {file_path}")
                modified_count += 1

print(f"\n=== CLEANUP COMPLETE ===")
print(f"Successfully processed and updated {modified_count} index files.")
