import os
import json
import html

print("Scanning and translating HTML decimal entities to raw Hebrew...")
print("-" * 60)

converted_files = 0

for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith(".json"):
            file_path = os.path.join(root, file)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content_str = f.read()
                
                # Check if the file actually contains any HTML numeric entities like &#1502;
                if "&#" in content_str:
                    # 1. html.unescape turns '&#1502;' directly into the raw letter 'מ'
                    decoded_str = html.unescape(content_str)
                    
                    # 2. Parse it back to valid JSON object to ensure safety
                    json_data = json.loads(decoded_str)
                    
                    # 3. Save it back in its ultra-compact, raw UTF-8 format
                    with open(file_path, "w", encoding="utf-8") as out_f:
                        json.dump(json_data, out_f, separators=(',', ':'), ensure_ascii=False)
                        
                    converted_files += 1
                    print(f" -> Successfully decoded letters in: {file}")
                    
            except Exception as e:
                print(f" !! Error converting {file}: {e}")

print("-" * 60)
print(f"Done! Cleaned and translated text in {converted_files} JSON files.")
