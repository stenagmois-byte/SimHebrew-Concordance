import os

root_dir = "./musicscores"
modified_count = 0

# CHANGE THIS to match exactly how it is currently written in your HTML
CURRENT_BROKEN_PATH = 'href="../qstyles.css"' 
CORRECT_PATH = 'href="../../qstyles.css"'

print("=== STARTING CSS PATH FIX ===")

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename == "index.html":
            file_path = os.path.join(dirpath, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Swap the broken path with the correct two-level relative path
            if CURRENT_BROKEN_PATH in content:
                updated_content = content.replace(CURRENT_BROKEN_PATH, CORRECT_PATH)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                
                print(f"🔧 Fixed CSS path in: {file_path}")
                modified_count += 1
            else:
                print(f"⚠️ Target string not found in: {file_path}")

print(f"\n=== CSS PATH FIX COMPLETE ===")
print(f"Successfully updated {modified_count} index files.")
