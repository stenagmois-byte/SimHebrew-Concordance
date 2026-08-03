import os

root_dir = "./musicscores"
modified_count = 0

print("=== SCOPING INDEX TABLES ===")

for dirpath, _, filenames in os.walk(root_dir):
    for filename in filenames:
        if filename == "index.html":
            file_path = os.path.join(dirpath, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Target your exact table declaration and add a scoping class
            if '<table class="atable">' in content:
                updated_content = content.replace(
                    '<table class="atable">',
                    '<table class="atable index-table">'
                )
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print(f"🏷️ Scoped table in: {file_path}")
                modified_count += 1

print(f"\n=== SCOPING COMPLETE. Processed {modified_count} files ===")
