import os
import json

print("Initializing JSON data space optimization loop...")
print("-" * 60)

optimized_count = 0
total_saved_bytes = 0

for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith(".json"):
            file_path = os.path.join(root, file)
            
            try:
                # 1. Read the bloated file
                with open(file_path, "r", encoding="utf-8") as f:
                    original_size = os.path.getsize(file_path)
                    data = json.load(f)
                
                # 2. Rewrite with compact formatting parameters:
                # 'ensure_ascii=False' converts raw '\u05d0' strings back to a clean single literal 'א'
                # Removing indent whitespace compresses the file profile down to a tight, dense grid layout
                with open(file_path, "w", encoding="utf-8") as out_f:
                    json.dump(data, out_f, separators=(',', ':'), ensure_ascii=False)
                
                new_size = os.path.getsize(file_path)
                saved_bytes = original_size - new_size
                total_saved_bytes += saved_bytes
                optimized_count += 1
                
            except Exception as e:
                print(f" !! Skipped due to an anomaly in {file}: {e}")

print("-" * 60)
print(f"Optimization loop complete! Processed {optimized_count} JSON data files.")
print(f"Total space recovered: {total_saved_bytes / (1024 * 1024):.2f} MB")
