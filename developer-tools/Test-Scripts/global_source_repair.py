import os

def run_global_source_repair():
    # Targets all potential storage locations across your workspace
    target_dirs = ["./musicscores", "musicscores", "."]
    
    # Trackers for your diagnostic logs
    modified_files_count = 0
    total_files_scanned = 0
    
    print("⏳ Beginning global database source repair pipeline...")
    print("======================================================")

    # Use a set to prevent scanning the same physical directory twice
    scanned_paths = set()
    
    for t_dir in target_dirs:
        abs_path = os.path.abspath(t_dir)
        if abs_path in scanned_paths or not os.path.exists(abs_path):
            continue
        scanned_paths.add(abs_path)
        
        for root, dirs, files in os.walk(abs_path):
            for file in files:
                # Target only real JSON files, bypassing hidden files
                if file.endswith('.json') and not file.startswith('.'):
                    total_files_scanned += 1
                    file_path = os.path.join(root, file)
                    
                    try:
                        # 1. Read the file as a raw text string to catch all nested properties
                        with open(file_path, 'r', encoding='utf-8') as f:
                            raw_content = f.read()
                        
                        # 2. Check if the misspelling exists anywhere inside this specific text layout
                        # We use lower() for check safety, but look for both common cases just in case
                        if "qatana" in raw_content or "QATANA" in raw_content:
                            print(f"🛠️  Fixing typo inside: {file}")
                            
                            # 3. Cleanly execute the string repair swapping 'qatana' with 'qetana'
                            repaired_content = raw_content.replace("qatana", "qetana").replace("QATANA", "QETANA")
                            
                            # 4. Save the pristine corrected data back to disk immediately
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(repaired_content)
                                
                            modified_files_count += 1
                            
                    except Exception as e:
                        print(f"❌ Error operating on file {file}: {str(e)}")
                        continue

    print("======================================================")
    print("✨ Global Source Repair Pipeline Complete!")
    print(f"📊 Scanned:  {total_files_scanned} JSON source files.")
    print(f"🔧 Repaired: {modified_files_count} files containing the 'qatana' typo.")
    print("\n👉 Next Step: Re-run 'mass_produce_and_log_matrices.py' to generate a pristine 'motif_relationship_matrix.json' with perfect matching counts!")

if __name__ == "__main__":
    run_global_source_repair()
