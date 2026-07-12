import os

print("Scanning repository for JSON filename formatting issues...")
print("-" * 60)

dash_count = 0
total_json_count = 0

# Walk through all directories and files
for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower().endswith(".json"):
            total_json_count += 1
            
            # Check if a dash exists in the JSON filename
            if "-" in file:
                dash_count += 1
                full_path = os.path.join(root, file)
                print(f"!! CRITICAL: Found dash in JSON filename: {full_path}")

print("-" * 60)
print(f"Scan complete. Checked {total_json_count} total JSON files.")

if dash_count == 0:
    print("SUCCESS: Every single JSON file is perfectly formatted with underscores! No dashes found.")
else:
    print(f"WARNING: Found {dash_count} misformatted JSON file(s) containing dashes. They need to be renamed.")
