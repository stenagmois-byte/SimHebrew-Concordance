#!/usr/bin/env python3
"""
split_interlin-v2.py

Splits interlin.json into chapter JSON files organized across 39 book subdirectories
under a root `chapters/` folder using the `k` field key format: `nn_nnn_nnn_nn`
(book_number_chapter_number_verse_number_word_sequence).

Example:
  k = "01_001_001_01" -> Book 01 (GENESIS), Chapter 001
  Output path: chapters/GENESIS/GENESIS_001.json
"""

import json
import os
import sys
from collections import defaultdict


def load_bookseq(bookseq_path):
    """
    Load bookseq.txt or bookseq.json and map 2-digit book sequence numbers ("01", "02", ...)
    to normalized directory book names ("GENESIS", "1_SAMUEL", etc.).
    """
    with open(bookseq_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    seq_map = {}
    items = []
    
    if isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list) and len(data["results"]) > 0:
            items = data["results"][0].get("items", [])
        elif "items" in data:
            items = data["items"]
    elif isinstance(data, list):
        items = data

    for idx, item in enumerate(items, start=1):
        if isinstance(item, dict):
            b_name = item.get("book_cd") or item.get("BOOK_CD") or item.get("book") or item.get("name")
            seq_no = item.get("book_seq_no") or item.get("BOOK_SEQ_NO") or idx
        elif isinstance(item, str):
            b_name = item
            seq_no = idx
        else:
            continue

        if b_name:
            clean_name = str(b_name).strip()
            dir_name = clean_name.replace(' ', '_')
            seq_str = f"{int(seq_no):02d}"
            seq_map[seq_str] = dir_name

    return seq_map


def split_interlinear_by_k_key(interlin_path, seq_map, output_base_dir="chapters"):
    """
    Splits interlin.json items based on the 'k' field (nn_nnn_nnn_nn).
    Groups items by book sequence number and chapter number.
    """
    os.makedirs(output_base_dir, exist_ok=True)
    
    # Pre-create all 39 book directories under chapters/
    for seq_str, dir_name in seq_map.items():
        os.makedirs(os.path.join(output_base_dir, dir_name), exist_ok=True)

    print(f"Loading interlinear data from {interlin_path}...")
    with open(interlin_path, 'r', encoding='utf-8') as f:
        interlin_raw = json.load(f)

    # Extract items array from interlin.json format
    items = []
    if isinstance(interlin_raw, dict):
        if "results" in interlin_raw and isinstance(interlin_raw["results"], list) and len(interlin_raw["results"]) > 0:
            items = interlin_raw["results"][0].get("items", [])
        elif "items" in interlin_raw and isinstance(interlin_raw["items"], list):
            items = interlin_raw["items"]
        else:
            items = []
    elif isinstance(interlin_raw, list):
        items = interlin_raw

    print(f"Total items loaded: {len(items)}")

    # Group items by (book_seq_str, chapter_seq_str) -> list of item dicts
    grouped = defaultdict(list)

    for item in items:
        if not isinstance(item, dict):
            continue
        
        # Look for "k" or "K" field
        k_val = item.get("k") or item.get("K")
        if not k_val or not isinstance(k_val, str):
            continue

        parts = k_val.split('_')
        if len(parts) < 2:
            continue

        book_num_str, chap_num_str = parts[0], parts[1]
        grouped[(book_num_str, chap_num_str)].append(item)

    total_files_written = 0
    written_books = set()

    print("\nWriting chapter JSON files...")
    for (book_num_str, chap_num_str), chap_items in sorted(grouped.items()):
        dir_name = seq_map.get(book_num_str, f"BOOK_{book_num_str}")
        target_dir = os.path.join(output_base_dir, dir_name)
        os.makedirs(target_dir, exist_ok=True)

        filename = f"{dir_name}_{chap_num_str}.json"
        filepath = os.path.join(target_dir, filename)

        with open(filepath, 'w', encoding='utf-8') as out_f:
            json.dump(chap_items, out_f, ensure_ascii=False, indent=2)

        total_files_written += 1
        written_books.add(dir_name)

    print(f"\nDone!")
    print(f"Chapter files created: {total_files_written}")
    print(f"Books populated: {len(written_books)} of {len(seq_map)}")


if __name__ == "__main__":
    bookseq_file = "bookseq.txt" if os.path.exists("bookseq.txt") else "bookseq.json"
    interlin_file = "interlin.json"

    if not os.path.exists(bookseq_file):
        print(f"Error: {bookseq_file} not found.")
        sys.exit(1)

    if not os.path.exists(interlin_file):
        print(f"Error: {interlin_file} not found.")
        sys.exit(1)

    seq_mapping = load_bookseq(bookseq_file)
    print(f"Loaded {len(seq_mapping)} book sequence mappings from {bookseq_file}.")
    split_interlinear_by_k_key(interlin_file, seq_mapping)
