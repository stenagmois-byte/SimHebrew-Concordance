import os
import json
from collections import defaultdict

def identify_rare_accent_verses():
    target_dirs = ["./musicscores", "musicscores", "."]
    
    # Trackers for your specific hypothesis
    zq_no_pashta_verses = []
    
    for t_dir in target_dirs:
        if os.path.exists(t_dir):
            for root, dirs, files in os.walk(t_dir):
                for file in files:
                    if file.endswith('.json') and not file.startswith('.'):
                        try:
                            with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                                # Unpack rows natively matching your structure
                                rows = []
                                if isinstance(data, dict) and 'results' in data:
                                    for res in data['results']:
                                        if 'items' in res: rows.extend(res['items'])
                                elif isinstance(data, list): rows = data
                                elif isinstance(data, dict): rows = data.get('rows', [data])
                                
                                # Group row items by specific verse to see the full accent chain
                                verse_accents = defaultdict(set)
                                verse_refs = {}
                                
                                for row in rows:
                                    if not isinstance(row, dict): continue
                                    
                                    # Create unique identifier for the verse
                                    b_cd = row.get('book_cd', '').strip().upper()
                                    ch = row.get('chapter_cd', '').strip()
                                    vs = row.get('verse_cd', '').strip()
                                    v_key = f"{b_cd}_{ch}_{vs}"
                                    
                                    orn = str(row.get('ornament_name', row.get('ORNAMENT_NAME', ''))).strip().lower()
                                    
                                    if orn != '0' and orn != '':
                                        verse_accents[v_key].add(orn)
                                        # Save a clean display reference
                                        verse_refs[v_key] = f"{b_cd.replace('_', ' ').title()} {int(ch)}:{int(vs)}"
                                
                                # Evaluate the logic gate for each unique verse in this file
                                for v_key, accents in verse_accents.items():
                                    # Change these strings to match the exact spelling inside your JSON keys
                                    has_zq = 'zaqef-qatan' in accents or 'zaqef_qatan' in accents
                                    has_pashta = 'pashta' in accents
                                    
                                    if has_zq and not has_pashta:
                                        zq_no_pashta_verses.append(verse_refs[v_key])
                                        
                        except Exception:
                            continue
            break # Stop after finding the first valid target directory pool

    print(f"📊 Analysis Complete.")
    print(f"Discovered {len(zq_no_pashta_verses)} verses with a Zaqef-Qatan but NO Pashta:")
    for ref in sorted(zq_no_pashta_verses):
        print(f"  • {ref}")

if __name__ == "__main__":
    identify_rare_accent_verses()
