import os
import pandas as pd
from collections import Counter

def build_reconciliation_matrix(master_sequence_log):
    print("🚀 Initializing Calibrated Modal Reconciliation Matrix...")
    
    if not master_sequence_log:
        print("❌ Error: master_sequence_log is empty.")
        return

    # THE VALUE LOCATION: Safely nested right after the return checkpoint
    DEGREE_MAP = {
        'D5':'7', 'C5':'6', 'B4':'5', 'A4':'4', 'G4':'3', 'F4':'2',
        'E4':'1',
        'D4':'-1', 'C4':'-2'
    }

    df = pd.DataFrame(master_sequence_log)
    
    # 1. Global Verse Ledger Reconciliation Calculations
    total_left_poetry = len(df[(df["is_poetry"] == "1") & (df["type"] == "Left Approach")])
    total_left_prose = len(df[(df["is_poetry"] == "0") & (df["type"] == "Left Approach")])
    total_no_atnah_poetry = len(df[(df["is_poetry"] == "1") & (df["type"] == "No Atnah")])
    total_no_atnah_prose = len(df[(df["is_poetry"] == "0") & (df["type"] == "No Atnah")])
    
    reconciled_verses_poetry = total_left_poetry + total_no_atnah_poetry
    reconciled_verses_prose = total_left_prose + total_no_atnah_prose
    grand_total_verses = reconciled_verses_poetry + reconciled_verses_prose

    # 2. Independent Helper Functions
    def get_diatonic_shape(row):
        raw_pattern = str(row.get("sequence_pattern", "")).strip()
        return " ".join(raw_pattern.replace("#", "").split())

    def get_modal_shorthand(row):
        raw_pattern = str(row.get("sequence_pattern", "")).strip()
        clean_notes = raw_pattern.replace("#", "").split()
        
        if not clean_notes:
            return ""
            
        shorthand_steps = []
        for note in clean_notes:
            pitch_token = note.upper().strip()
            # Grabs values natively from the map definition above
            step_num = DEGREE_MAP.get(pitch_token, '?')
            shorthand_steps.append(step_num)
            
        return " ".join(shorthand_steps)

    # 3. Apply the mappings one-by-one to prevent ValueError conflicts
    df["diatonic_shape"] = df.apply(get_diatonic_shape, axis=1)
    df["shorthand"] = df.apply(get_modal_shorthand, axis=1)
    # ==========================================================================
    # 4. FUNCTIONAL CONTEXT GROUPING DEFINITIONS (Independent Multi-Tier Fix)
    # ==========================================================================
    
    def get_sort_tier(row):
        orig_type = row.get("type", "")
        shorthand = str(row.get("shorthand", "")).strip()
        
        # Highlight critical 1-2-1 supertonic cadences in poetry explicitly
        if row.get("is_poetry") == "1" and (shorthand.endswith("1 2 1") or shorthand == "1 2 1"):
            return 1.5
            
        if orig_type == "Left Approach":
            return 1
        elif orig_type == "Right Resolution":
            return 2
        else:
            return 3

    def get_functional_context(row):
        orig_type = row.get("type", "")
        shorthand = str(row.get("shorthand", "")).strip()
        
        # Highlight label for 1-2-1 supertonic cadences
        if row.get("is_poetry") == "1" and (shorthand.endswith("1 2 1") or shorthand == "1 2 1"):
            return "Poetic Cadence on Supertonic (1 2 1)"
            
        if orig_type == "Left Approach":
            return "Approaching the subdominant"
        elif orig_type == "Right Resolution":
            return "Returning to the tonic"
        else:
            return "No subdominant"

    # Apply calculations independently to completely eliminate packing errors
    df["sort_tier"] = df.apply(get_sort_tier, axis=1)
    df["functional_context"] = df.apply(get_functional_context, axis=1)


    # 4. Compile Split Counter Subsets
    poetry_subset = df[df["is_poetry"] == "1"]
    prose_subset = df[df["is_poetry"] == "0"]
    
    poetry_totals = len(poetry_subset)
    prose_totals = len(prose_subset)

    # 5. Extract Unique Keys and Sort strictly by your 3 custom structural categories
    unique_rows = df.drop_duplicates(subset=["diatonic_shape", "functional_context"])
    unique_rows = unique_rows.sort_values(by=["sort_tier", "diatonic_shape"])

    # 6. HTML Page Generation
    html_path = "reconciliation_matrix.html"
    
    html = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="stylesheet" href="qstyles.css">
  <title>Tanakh Modal Comparison Matrix</title>
  <style>
    .matrix-table { width: 100%; border-collapse: collapse; font-family: 'Georgia', serif; margin: 25px 0; }
    .matrix-table td { padding: 12px; border: 1px solid #ddd; vertical-align: middle; }
    .matrix-hdr { background-color: #f3f0e8; color: #800000; font-weight: bold; text-align: center; }
    .section-divider { background-color: #eaeaea; color: #222; font-weight: bold; padding: 8px 12px; font-size: 1.05rem; }
    .supertonic-row { background-color: #fff4f4 !important; border-left: 5px solid #d35400; }
    .blank-cell { background-color: #fafafa; font-style: italic; color: #aaa; text-align: center; }
    .num-col { text-align: right; font-variant-numeric: tabular-nums; padding-right: 15px; }
    .reconcile-box { background-color: #fffcf4; border: 2px solid #800000; padding: 20px; margin-top: 40px; border-radius: 6px; }
    .reconcile-table { width: 100%; margin-top: 10px; border-collapse: collapse; }
    .reconcile-table td { padding: 8px; border-bottom: 1px solid #e1e4e6; }
  </style>
</head>
<body>

  <div class="nav"><a href="index.html">← Back to Volume Directory</a></div>

  <h1>Diatonic Alignment & Reconciliation Matrix</h1>
  <p>Isolated structural note paths compared by stripping accidentals. Grouped functionally to map out the foundational syntax of biblical modality.</p>

  <table class="matrix-table">
    <thead>
      <tr>
        <td class="matrix-hdr" style="width: 25%;">Prose Diatonic Phrase</td>
        <td class="matrix-hdr" style="width: 25%;">Poetic Diatonic Phrase</td>
        <td class="matrix-hdr" style="width: 15%;">Shorthand</td>
        <td class="matrix-hdr" class="num-col">Prose Count</td>
        <td class="matrix-hdr" class="num-col">Prose %</td>
        <td class="matrix-hdr" class="num-col">Poetry Count</td>
        <td class="matrix-hdr" class="num-col">Poetry %</td>
      </tr>
    </thead>
    <tbody>"""

    current_group = None
    
    for _, row in unique_rows.iterrows():
        shape = row["diatonic_shape"]
        context_label = row["functional_context"]
        shorthand = row["shorthand"]
        tier = row["sort_tier"]
        
        # Inject bold horizontal headings when moving between your 3 functional tiers
        if context_label != current_group:
            current_group = context_label
            html += f"      <tr><td colspan=\"7\" class=\"section-divider\">Structural Tier: {context_label}</td></tr>\n"

        # Apply specific visual highlight rows for your critical 1-2-1 poetic supertonic cadences
        row_class = " class=\"supertonic-row\"" if tier == 1.5 else ""

        # Query counts safely out of our split data dataframes
        prose_cnt = len(prose_subset[(prose_subset["diatonic_shape"] == shape) & (prose_subset["functional_context"] == context_label)])
        poetry_cnt = len(poetry_subset[(poetry_subset["diatonic_shape"] == shape) & (poetry_subset["functional_context"] == context_label)])
        
        if prose_cnt == 0 and poetry_cnt == 0:
            continue

        prose_pct = (prose_cnt / prose_totals) * 100 if prose_totals > 0 else 0
        poetry_pct = (poetry_cnt / poetry_totals) * 100 if poetry_totals > 0 else 0

        html += f"      <tr{row_class}>\n"
        
        # COLUMN 1: PROSE DISPLAY
        if prose_cnt > 0:
            html += f"        <td><strong>[ {shape} ]</strong></td>\n"
        else:
            html += "        <td class=\"blank-cell\">— Not used in prose —</td>\n"
            
        # COLUMN 2: POETRY DISPLAY
        if poetry_cnt > 0:
            html += f"        <td><strong>[ {shape} ]</strong></td>\n"
        else:
            html += "        <td class=\"blank-cell\">— Not used in poetry —</td>\n"
            
        # FREQUENCY METRIC DATA COLUMNS
        html += f"        <td style=\"color: #555; font-weight: bold;\">{shorthand}</td>\n"
        html += f"        <td class=\"num-col\">{prose_cnt if prose_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\">{f'{prose_pct:.2f}%' if prose_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\">{poetry_cnt if poetry_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\">{f'{poetry_pct:.2f}%' if poetry_cnt > 0 else '-'}</td>\n"
        html += "      </tr>\n"

    html += f"""    </tbody>
  </table>

  <!-- VERSE BALANCE ACCOUNTING PANEL -->
  <div class="reconcile-box">
    <h3>📋 Database Verse Reconciliation Ledger</h3>
    <table class="reconcile-table">
      <thead>
        <tr style="font-weight: bold; background-color: #fdfaf2;">
          <td>Accent System Classification Group</td>
          <td class="num-col">Atnah Verses (Left Approaches)</td>
          <td class="num-col">Single Phrase Verses (No Atnah)</td>
          <td class="num-col" style="color: #800000;">Reconciled Total Verses</td>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Prose Accent System</strong> (The 21 Books)</td>
          <td class="num-col">{total_left_prose}</td>
          <td class="num-col">{total_no_atnah_prose}</td>
          <td class="num-col" style="font-weight: bold; color: #800000;">{reconciled_verses_prose}</td>
        </tr>
        <tr>
          <td><strong>Poetic Accent System</strong> (Psalms, Proverbs, Job Core)</td>
          <td class="num-col">{total_left_poetry}</td>
          <td class="num-col">{total_no_atnah_poetry}</td>
          <td class="num-col" style="font-weight: bold; color: #800000;">{reconciled_verses_poetry}</td>
        </tr>
        <tr style="font-weight: bold; background-color: #f3f0e8;">
          <td>GRAND TOTAL VERSE RECONCILIATION BALANCE</td>
          <td class="num-col">{total_left_prose + total_left_poetry}</td>
          <td class="num-col">{total_no_atnah_prose + total_no_atnah_poetry}</td>
          <td class="num-col" style="font-size: 1.1rem; color: #800000;">{grand_total_verses}</td>
        </tr>
      </tbody>
    </table>
  </div>

  <footer>
    <p>Qualum Publishing · Computational Musicology Research Suite</p>
  </footer>

</body>
</html>"""

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"📊 Alignment dashboard matrix generated successfully: {os.path.abspath(html_path)}")
