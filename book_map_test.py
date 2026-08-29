import json

# 1. Load the centralized JSON map file
with open("book_map.json", "r", encoding="utf-8") as f:
    book_map = json.load(f)

# 2. Test lookup strings for your edge cases
for test_key in ["1_SAMUEL", "PSALMS", "GENESIS", "HOSEA"]:
    folder = book_map.get(test_key, test_key.replace("_", " ").title())
    print(f"📖 Book Key: {test_key:<12} ➔ Resolved Folder: {folder}")
