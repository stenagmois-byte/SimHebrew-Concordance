import os
import pandas as pd
from collections import Counter

def build_reconciliation_matrix(master_sequence_log):
    print("🚀 Initializing Comparative Matrix with Reference Mapping...")
    
    if not master_sequence_log:
        print("❌ Error: master_sequence_log is empty.")
        return

    # Initialize the DataFrame
    df = pd.DataFrame(master_sequence_log)
    
    # Pre-initialize target columns as empty strings to guarantee they exist in the index layout
    df["diatonic_shape"] = ""
    df["sort_tier"] = 3
    df["functional_context"] = "No subdominant"

    # 1. Global Verse Ledger Reconciliation Calculations
    total_left_poetry = len(df[(df["is_poetry"] == "1") & (df["type"] == "Left Approach")])
    total_left_prose = len(df[(df["is_poetry"] == "0") & (df["type"] == "Left Approach")])
    total_no_atnah_poetry = len(df[(df["is_poetry"] == "1") & (df["type"] == "No Atnah")])
    total_no_atnah_prose = len(df[(df["is_poetry"] == "0") & (df["type"] == "No Atnah")])
    
    reconciled_verses_poetry = total_left_poetry + total_no_atnah_poetry
    reconciled_verses_prose = total_left_prose + total_no_atnah_prose
    grand_total_verses = reconciled_verses_poetry + reconciled_verses_prose

    # 2. Extract Clean Diatonic Shapes (Strips accidentals)
    def get_diatonic_shape(row):
        raw_pattern = str(row.get("sequence_pattern", "")).strip()
        return " ".join(raw_pattern.replace("#", "").split())

    # Map directly to fill the pre-initialized column field
    df["diatonic_shape"] = df.apply(get_diatonic_shape, axis=1)

    # 3. Apply Functional Context Grouping Tiers
    def get_sort_tier(row):
        orig_type = row.get("type", "")
        if orig_type == "Left Approach": return 1
        elif orig_type == "Right Resolution": return 2
        else: return 3

    def get_functional_context(row):
        orig_type = row.get("type", "")
        if orig_type == "Left Approach": return "Approaching the subdominant"
        elif orig_type == "Right Resolution": return "Returning to the tonic"
        else: return "No subdominant"

    df["sort_tier"] = df.apply(get_sort_tier, axis=1)
    df["functional_context"] = df.apply(get_functional_context, axis=1)

    # 4. Compile Split Counter Subsets
    poetry_subset = df[df["is_poetry"] == "1"]
    prose_subset = df[df["is_poetry"] == "0"]
    
    poetry_totals = len(poetry_subset)
    prose_totals = len(prose_subset)

    # 5. Extract Unique Keys Sorted by Tier and Shape Structure (Now perfectly safe from KeyError)
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
    .section-divider { background-color: #eaeaea; color: #222; font-weight: bold; padding: 10px 12px; font-size: 1.1rem; border-top: 3px solid #800000; }
    .blank-cell { background-color: #fafafa; font-style: italic; color: #aaa; text-align: center; }
    .num-col { text-align: right; font-variant-numeric: tabular-nums; padding-right: 15px; }
    .sample-text { font-size: 0.85rem; color: #666; font-family: sans-serif; line-height: 1.4; display: block; max-width: 280px; word-wrap: break-word; }
    .reconcile-box { background-color: #fffcf4; border: 2px solid #800000; padding: 20px; margin-top: 40px; border-radius: 6px; }
    .reconcile-table { width: 100%; margin-top: 10px; border-collapse: collapse; }
    .reconcile-table td { padding: 8px; border-bottom: 1px solid #e1e4e6; }
  </style>
</head>
<body>

  <!-- RESOLVED WARNING PATH: Fixed backslash to web forward slash -->
  <div class="nav"><a href="musicscores/index.html">← Back to Volume Directory</a></div>

  <h1>Diatonic Alignment & Reconciliation Matrix</h1>
  <p>Isolated structural note paths compared by stripping accidentals. Grouped functionally to track occurrences and reference locations side-by-side.</p>

  <table class="matrix-table">
    <thead>
      <tr>
        <td class="matrix-hdr" style="width: 25%;">Prose Diatonic Phrase</td>
        <td class="matrix-hdr" style="width: 25%;">Poetic Diatonic Phrase</td>
        <td class="matrix-hdr" style="width: 25%;">Sample Text Reference Occurrences</td>
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
        
        if context_label != current_group:
            current_group = context_label
            html += f"      <tr><td colspan=\"7\" class=\"section-divider\">Structural Tier: {context_label}</td></tr>\n"

        # Query dynamic matching frames out of our split data sub-pools
        matching_prose = prose_subset[(prose_subset["diatonic_shape"] == shape) & (prose_subset["functional_context"] == context_label)]
        matching_poetry = poetry_subset[(poetry_subset["diatonic_shape"] == shape) & (poetry_subset["functional_context"] == context_label)]
        
        prose_cnt = len(matching_prose)
        poetry_cnt = len(matching_poetry)
        
        if prose_cnt == 0 and poetry_cnt == 0:
            continue

        # PINPOINT CLARITY FIX: Compute percentages relative to the explicit functional tier total
        # Prose denominator = prose_totals (All Prose elements) or len(prose_subset[prose_subset["functional_context"] == context_label])
        prose_tier_total = len(prose_subset[prose_subset["functional_context"] == context_label])
        poetry_tier_total = len(poetry_subset[poetry_subset["functional_context"] == context_label])

        prose_pct = (prose_cnt / prose_tier_total) * 100 if prose_tier_total > 0 else 0
        poetry_pct = (poetry_cnt / poetry_tier_total) * 100 if poetry_tier_total > 0 else 0

        # Gather sample references
        samples_list = []
        if not matching_prose.empty:
            for _, r in matching_prose.head(3).iterrows():
                b_name = str(r['book']).replace('_', ' ').title()
                samples_list.append(f"{b_name} {r['chapter']}:{r['verse']}")
                
        if not matching_poetry.empty:
            for _, r in matching_poetry.head(3).iterrows():
                b_name = str(r['book']).replace('_', ' ').title()
                samples_list.append(f"{b_name} {r['chapter']}:{r['verse']}")

        samples_display_str = ", ".join(samples_list)

        html += "      <tr>\n"
        
        # PROSE VIEW
        if prose_cnt > 0:
            html += f"        <td><strong>[ {shape} ]</strong></td>\n"
        else:
            html += "        <td class=\"blank-cell\">— Not used in prose —</td>\n"
            
        # POETRY VIEW
        if poetry_cnt > 0:
            html += f"        <td><strong>[ {shape} ]</strong></td>\n"
        else:
            html += "        <td class=\"blank-cell\">— Not used in poetry —</td>\n"
            
        # REFERENCE CODES
        html += f"        <td><span class=\"sample-text\">{samples_display_str}</span></td>\n"
        
        # FREQUENCY METRIC DATA COLUMNS WITH EXPLICIT TITLES IN HOVER/TEXT
        # Displays percentage along with a clear title marker mapping to the specific subset tier
        html += f"        <td class=\"num-col\">{prose_cnt if prose_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\" title=\"of {prose_tier_total} {context_label} elements\">{f'{prose_pct:.2f}%' if prose_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\">{poetry_cnt if poetry_cnt > 0 else '-'}</td>\n"
        html += f"        <td class=\"num-col\" title=\"of {poetry_tier_total} {context_label} elements\">{f'{poetry_pct:.2f}%' if poetry_cnt > 0 else '-'}</td>\n"
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
    print(f"✅ Success! Matrix compiled with explicit index instantiation and proper slash targets: {html_path}")
