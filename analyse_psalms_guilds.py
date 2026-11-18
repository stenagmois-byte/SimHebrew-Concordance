import os
import json
import glob
from collections import defaultdict

KORAH_PSALMS = {42, 44, 45, 46, 47, 48, 49, 84, 85, 87, 88}
ASAPH_PSALMS = {50, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83}
DAVID_PSALMS = {
    3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
    21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 34, 35, 36, 37, 38, 39, 40, 41,
    51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 68, 69, 70, 86,
    101, 103, 108, 109, 110, 122, 124, 131, 133, 138, 139, 140, 141, 142, 143, 144, 145
}

def get_cohort(psalm_num):
    if psalm_num in KORAH_PSALMS:
        return "Sons of Korah"
    elif psalm_num in ASAPH_PSALMS:
        return "Asaph"
    elif psalm_num in DAVID_PSALMS:
        return "David"
    else:
        return "Control Group (Anonymous / Other)"

def analyze_psalm_scores(scores_dir):
    pattern = os.path.join(scores_dir, "**", "PSALMS_*.json")
    files = glob.glob(pattern, recursive=True)
    if not files:
        pattern = os.path.join(scores_dir, "*.json")
        files = [f for f in glob.glob(pattern) if "PSALM" in os.path.basename(f).upper()]
        
    print(f"Found {len(files)} Psalm JSON files in '{scores_dir}'.")
    
    cohort_stats = defaultdict(lambda: {
        "psalms_count": 0,
        "total_verses": 0,
        "starting_pitches": defaultdict(int),
        "creation_motif_count": 0,
        "total_syllables": 0,
        "total_ornaments": 0,
        "sublinear_only_verses": 0,
        "ornamented_verses": 0,
        "active_syllables": 0
    })

    for fpath in sorted(files):
        filename = os.path.basename(fpath)
        num_str = ''.join(c for c in filename if c.isdigit())
        if not num_str: continue
        
        psalm_num = int(num_str)
        cohort = get_cohort(psalm_num)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        rows = []
        if isinstance(data, dict) and 'results' in data:
            for res in data['results']:
                if 'items' in res: rows.extend(res['items'])
        elif isinstance(data, list):
            rows = data
        elif isinstance(data, dict):
            rows = data.get('items', data.get('rows', [data]))
            
        cohort_stats[cohort]["psalms_count"] += 1
        
        verses = defaultdict(list)
        for r in rows:
            v_cd = str(r.get('verse_cd', r.get('VERSE_CD', '0'))).lstrip('0') or '0'
            verses[v_cd].append(r)
            
        cohort_stats[cohort]["total_verses"] += len(verses)
        
        for v_cd, v_rows in verses.items():
            if not v_rows: continue
            
            # 1. Opening Pitch (Implied E4 if 1st syllable is unaccented/0)
            first_raw = str(v_rows[0].get('syll_note', v_rows[0].get('SYLL_NOTE', ''))).strip().upper()
            if not first_raw or first_raw == '0':
                start_pitch = 'E'  # Implied E4 tonic opening
            else:
                start_pitch = first_raw[0]  # Base letter (C, B, E, A, F, G, D)
                
            cohort_stats[cohort]["starting_pitches"][start_pitch] += 1
            
            # 2. Build verse pitch sequence (inserting implied E4 at start if needed)
            pitch_seq = []
            for idx, r in enumerate(v_rows):
                p_raw = str(r.get('syll_note', r.get('SYLL_NOTE', ''))).strip().upper()
                if not p_raw or p_raw == '0':
                    if idx == 0:
                        pitch_seq.append('E4')  # Implied E4
                else:
                    pitch_seq.append(p_raw)
                    cohort_stats[cohort]["total_syllables"] += 1
                    
                orn = str(r.get('ornament_name', r.get('ORNAMENT_NAME', ''))).strip().lower()
                if orn and orn != '0':
                    cohort_stats[cohort]["total_ornaments"] += 1

            # 3. Collapse adjacent pitch repetitions to form melodic contour
            contour = []
            for note in pitch_seq:
                # Strip octave number for clean matching (E4 -> E, G4 -> G)
                clean_note = note[0] if note else ''
                if clean_note and (not contour or contour[-1] != clean_note):
                    contour.append(clean_note)
            
            contour_str = " ".join(contour)

            # Check for Creation Motif: E -> G -> B -> A
            if "E G B A" in contour_str:
                cohort_stats[cohort]["creation_motif_count"] += 1

            # ... [pitch parsing & creation motif check] ...
            
            v_ornaments = 0
            v_syllables = 0
            
            for r in v_rows:
                pitch = str(r.get('syll_note', r.get('SYLL_NOTE', ''))).strip().upper()
                if pitch and pitch != '0':
                    v_syllables += 1
                
                orn = str(r.get('ornament_name', r.get('ORNAMENT_NAME', ''))).strip().lower()
                if orn and orn != '0':
                    v_ornaments += 1
            
            cohort_stats[cohort]["total_syllables"] += v_syllables
            cohort_stats[cohort]["total_ornaments"] += v_ornaments
            
            # --- NEW METRICS ---
            if v_ornaments == 0:
                cohort_stats[cohort]["sublinear_only_verses"] += 1
            else:
                cohort_stats[cohort]["ornamented_verses"] += 1
                cohort_stats[cohort]["active_syllables"] += v_syllables
    # Windows-Safe Output
    print("\n" + "="*70)
    print("PSALM GUILD COMPARATIVE ANALYSIS MATRIX (IMPLIED E4 MATCHING)")
    print("="*70)
    
    for cohort, stats in cohort_stats.items():
        v_tot = stats["total_verses"] or 1
        s_tot = stats["total_syllables"] or 1
        print(f"\n=== {cohort.upper()} ({stats['psalms_count']} Psalms, {v_tot} Verses) ===")
        
        starts = stats["starting_pitches"]
        c_high = (starts.get('C', 0) / v_tot) * 100
        b_dom = (starts.get('B', 0) / v_tot) * 100
        e_tonic = (starts.get('E', 0) / v_tot) * 100
        print(f"  * Opening Pitch Ratios  : High C (Mahpach): {c_high:.1f}% | Dominant B: {b_dom:.1f}% | Tonic E (incl. implied): {e_tonic:.1f}%")
        
        cm_pct = (stats["creation_motif_count"] / v_tot) * 100
        print(f"  * Creation Motif Rate   : {stats['creation_motif_count']} verses ({cm_pct:.2f}% of cohort verses)")
        
        orn_density = (stats["total_ornaments"] / s_tot) * 100
        print(f"  * Ornament Density      : {orn_density:.2f}% of syllables")

        sub_only_pct = (stats["sublinear_only_verses"] / v_tot) * 100
        active_sylls = stats["active_syllables"] or 1
        active_orn_pct = (stats["total_ornaments"] / active_sylls) * 100
        
        print(f"  * Plain Verses (Sublinear Only) : {stats['sublinear_only_verses']} ({sub_only_pct:.1f}% of cohort)")
        print(f"  * Global Ornament Density        : {orn_density:.2f}% (all syllables)")
        print(f"  * Active Ornament Density        : {active_orn_pct:.2f}% (ornamented verses only)")
if __name__ == "__main__":
    import sys
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "./musicscores"
    analyze_psalm_scores(target_dir)