import json
import re
import sys

# Force the standard output stream to use UTF-8 coding when piped to a file
sys.stdout.reconfigure(encoding='utf-8')

ZAQEF_QATAN = "\u0594"
ATNAH = "\u0591"
CAESURA_ENTITY = "&#119059;"

# Targeted processing for These books prose
SCROLLS = [    "DEUTERONOMY",
    # The Twelve Minor Prophets (Standard uppercase snake_case format)
    "HOSEA", "JOEL", "AMOS", "OBADIAH", "JONAH", "MICAH", 
    "NAHUM", "HABAKKUK", "ZEPHANIAH", "HAGGAI", "ZECHARIAH", "MALACHI",
    "SONG","RUTH","LAMENTATIONS","QOHELET","ESTHER"
]
# "GENESIS", "EXODUS", "LEVITICUS", "NUMBERS", 
def load_data():
    with open('translation.json', 'r', encoding='utf-8') as f:
        translation_data = json.load(f)
    with open('ornament_index.json', 'r', encoding='utf-8') as f:
        ornament_data = json.load(f)
    return translation_data, ornament_data

def extract_items(translation_data):
    results_container = translation_data.get("results", [])
    if isinstance(results_container, list):
        for block in results_container:
            if isinstance(block, dict) and "items" in block:
                return block["items"]
    elif isinstance(results_container, dict):
        return results_container.get("items", [])
    return translation_data.get("items", [])

def get_accented_words(hebrew_text_segment):
    """Scans a Hebrew text string and returns a list of words holding the zaqef-qatan."""
    words = hebrew_text_segment.split()
    # Strip common trailing prose formatting or newline noise from the words if present
    return [w.strip() for w in words if ZAQEF_QATAN in w]

def build_split_zaqef_map(ornament_data):
    """
    Maps each verse to its exact Hebrew word metrics and split zaqef counts
    to enable precise proportional alignment calculations.
    """
    zaqef_map = {}
    zq_section = ornament_data.get("zaqef-qatan", {})
    
    for category, verses in zq_section.items():
        for item in verses:
            raw_book = item.get("b", "")
            book_clean = raw_book.upper().replace(" ", "_")
                
            if book_clean not in SCROLLS:
                continue

            chapter_clean = str(item.get("c", "")).zfill(3)
            verse_clean = str(item.get("v", "")).zfill(3)
            key = f"{book_clean}_{chapter_clean}_{verse_clean}"
            
            hebrew_text = item.get("t", "").strip()
            heb_words = hebrew_text.split()
            heb_total_words = len(heb_words)
            
            # Locate position of the Atnah
            atnah_word_idx = -1
            for idx, word in enumerate(heb_words):
                if ATNAH in word:
                    atnah_word_idx = idx + 1
                    break
            
            # Split Hebrew on Atnah to accurately isolate the targeted words per half
            if ATNAH in hebrew_text:
                parts = hebrew_text.split(ATNAH, 1)
                first_half_heb = parts[0]
                second_half_heb = parts[1]
                count_first = first_half_heb.count(ZAQEF_QATAN)
                count_second = second_half_heb.count(ZAQEF_QATAN)
            else:
                first_half_heb = hebrew_text
                second_half_heb = ""
                count_first = hebrew_text.count(ZAQEF_QATAN)
                count_second = 0
            
            # Isolate the exact words carrying the accent for easier error reporting
            words_first = get_accented_words(first_half_heb)
            words_second = get_accented_words(second_half_heb)
            
            if key not in zaqef_map:
                zaqef_map[key] = {
                    "first_half": count_first, 
                    "second_half": count_second,
                    "first_half_words": words_first,
                    "second_half_words": words_second,
                    "heb_total_words": heb_total_words,
                    "atnah_word_idx": atnah_word_idx
                }
            else:
                # Merge logic favoring maximum count discovery
                if count_first > zaqef_map[key]["first_half"]:
                    zaqef_map[key]["first_half"] = count_first
                    zaqef_map[key]["first_half_words"] = words_first
                if count_second > zaqef_map[key]["second_half"]:
                    zaqef_map[key]["second_half"] = count_second
                    zaqef_map[key]["second_half_words"] = words_second
                if atnah_word_idx != -1:
                    zaqef_map[key]["atnah_word_idx"] = atnah_word_idx
                    zaqef_map[key]["heb_total_words"] = heb_total_words
            
            
    return zaqef_map

def clean_tail_noise(text_segment):
    """Cleanly strips trailing Parashat markers and standard sentence boundaries."""
    text_segment = re.sub(r'[\.\;\:\?]\s*[PSRW]\s*$', '', text_segment.strip())
    text_segment = re.sub(r'[\.\;\:\?\"\'\!]+$', '', text_segment.strip())
    
    if len(text_segment) > 4:
        tail = text_segment[-4:]
        if any(mark in tail for mark in ['.', ';', ':', '?']):
            for i in range(len(text_segment) - 1, len(text_segment) - 5, -1):
                if text_segment[i] in ['.', ';', ':', '?']:
                    text_segment = text_segment[:i] + text_segment[i+1:]
                    break
    return text_segment

def run_diagnostic():
    translation_data, ornament_data = load_data()
    zaqef_map = build_split_zaqef_map(ornament_data)
    items = extract_items(translation_data)
    
    errors = []
    matches_found = 0
    scrolls_items_count = 0
    
    for item in items:
        book = str(item.get("book_cd", "")).strip().upper().replace(" ", "_")
            
        if book not in SCROLLS or item.get("poetry") == "1":
            continue
            
        scrolls_items_count += 1
        chapter = str(item.get("chapter_cd", "")).strip()
        verse = str(item.get("verse_cd", "")).strip()
        eng_text = item.get("eng_text", "").strip()
        has_atnah = item.get("has_atnah") == "1"
        
        lookup_key = f"{book}_{chapter}_{verse}"
        verse_display = f"{book.replace('_', ' ')} {int(chapter)}:{int(verse)}"

        z_data = zaqef_map.get(lookup_key, {
            "first_half": 0, "second_half": 0, 
            "first_half_words": [], "second_half_words": [],
            "heb_total_words": 0, "atnah_word_idx": -1
        })
        if lookup_key in zaqef_map:
            matches_found += 1

        # --- ALIGNMENT TEST: DETECT MISPLACED CAESURA BOUNDARIES ---
        if has_atnah and z_data["atnah_word_idx"] != -1 and z_data["heb_total_words"] > 0:
            eng_words = eng_text.split()
            eng_total_words = len(eng_words)
            caesura_word_idx = -1
            for idx, word in enumerate(eng_words):
                if CAESURA_ENTITY in word:
                    caesura_word_idx = idx + 1
                    break
            
            if caesura_word_idx != -1:
                heb_atnah_ratio = z_data["atnah_word_idx"] / z_data["heb_total_words"]
                eng_caesura_ratio = caesura_word_idx / eng_total_words
                variance = abs(heb_atnah_ratio - eng_caesura_ratio)
                
                if variance > 0.20:
                    errors.append({
                        "type": "MISPLACED_CAESURA_BOUNDARY",
                        "verse": verse_display,
                        "text": eng_text,
                        "reason": f"Caesura boundary shift! Hebrew Atnah is at {int(heb_atnah_ratio*100)}%, but English entity is at {int(eng_caesura_ratio*100)}%."
                    })

        # --- CAESURA-BASED SPLITTING LOGIC ---
        if has_atnah:
            if CAESURA_ENTITY in eng_text:
                parts = eng_text.split(CAESURA_ENTITY, 1)
                first_half_eng = parts[0]
                second_half_eng = parts[1]
                first_half_eng = re.sub(r',\s*$', '', first_half_eng.strip())
            else:
                first_half_eng = eng_text
                second_half_eng = ""
                errors.append({
                    "type": "MISSING_CAESURA_MARKER",
                    "verse": verse_display,
                    "text": eng_text,
                    "reason": f"Verse profile sets 'has_atnah: 1', but no explicit HTML entity ({CAESURA_ENTITY}) was found."
                })
        else:
            first_half_eng = eng_text
            second_half_eng = ""

        first_half_clean = clean_tail_noise(first_half_eng)
        second_half_clean = clean_tail_noise(second_half_eng)

        # --- VALIDATION: FIRST HALF (Strict Quantity Check) ---
        expected_z1 = z_data["first_half"]
        if expected_z1 > 0:
            commas_z1 = first_half_clean.count(",")
            strong_marks_z1 = len(re.findall(r'[\.\;\:\?](?!\s*𝄓)', first_half_clean))
            breaks_z1 = commas_z1 + strong_marks_z1
            
            if breaks_z1 < expected_z1:
                # Format the specific words for display in the output terminal
                target_words_str = " | ".join(z_data["first_half_words"])
                errors.append({
                    "type": "INSUFFICIENT_ZAQEF_FIRST_HALF",
                    "verse": verse_display,
                    "text": f"[First Half Segment]: {first_half_eng.strip()}",
                    "reason": f"First half requires {expected_z1} zaqef-qatan pause(s), but only found {breaks_z1}. Hebrew Target Word(s): {target_words_str}"
                })

        # --- VALIDATION: SECOND HALF (Strict Quantity Check) ---
        if has_atnah and second_half_clean:
            expected_z2 = z_data["second_half"]
            if expected_z2 > 0:
                # Count internal commas and strong sentence marks in the second half
                commas_z2 = second_half_clean.count(",")
                strong_marks_z2 = len(re.findall(r'[\.\;\:\?](?!\s*𝄓)', second_half_clean))
                breaks_z2 = commas_z2 + strong_marks_z2
                
                # Quantitative verification: flags partial omissions
                if breaks_z2 < expected_z2:
                    # Isolate and format the specific Hebrew words for the report message
                    target_words_str = " | ".join(z_data["second_half_words"])
                    errors.append({
                        "type": "INSUFFICIENT_ZAQEF_SECOND_HALF",
                        "verse": verse_display,
                        "text": f"[Second Half Segment]: {second_half_eng.strip()}",
                        "reason": f"Second half requires {expected_z2} zaqef-qatan pause(s), but only found {breaks_z2} phrasing mark(s). Hebrew Target Word(s): {target_words_str}"
                    })

    print(f"--- FILTER REPORT ---")
    print(f"Total Torah prose items evaluated: {scrolls_items_count}")
    print(f"Successfully matched {matches_found} verses within targeted scope.\n")
    return errors

if __name__ == "__main__":
    try:
        detected_errors = run_diagnostic()
        print(f"Analysis complete. Found {len(detected_errors)} structural violations:\n")
        
        for err in detected_errors:
            print(f"[{err['type']}] {err['verse']}")
            print(f"Reason: {err['reason']}")
            print(f"Text Segment: \"{err['text']}\"")
            print("-" * 60)
            
    except Exception as e:
        print(f"Execution failed: {e}")
