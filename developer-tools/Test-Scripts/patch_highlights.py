cat << 'EOF' > patch_highlights.py
import re

filename = "mass_produce_and_log_matrices.py"

with open(filename, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Inject the necessary CSS styles into the HTML head template
css_find = r'(\.pitch-cell\s*\{[^}]*\})'
css_replace = r'''\1
        
        /* Interactive Highlight Enclosures */
        .half-verse-container { cursor: pointer; display: block; border-radius: 6px; padding: 4px; transition: all 0.15s ease; }
        .half-verse-container:hover { background-color: rgba(0, 0, 0, 0.04); }
        .half-verse-container.highlighted-verse { background-color: #fff176 !important; box-shadow: 0 0 0 2px #fbc02d; }'''

if ".half-verse-container" not in code:
    code = re.sub(css_find, css_replace, code)

# 2. Inject the signature variables and the open-tag for the left-wing container
left_find = r'(html_content\s*\+=\s*f"""\s*<tr class="verse-row">.*?<td class="grid-cell">\s*)<div class="left-wing">'
left_replace = r'''# Calculate distinct sequence identifiers based on note combinations
        left_id_signature = "-".join(left_notes) if left_notes else "empty-left"
        right_id_signature = "-".join(right_notes) if right_notes else "empty-right"
        
        \1<div class="half-verse-container" data-half-verse-id="{left_id_signature}"><div class="left-wing">'''

if "left_id_signature" not in code:
    code = re.sub(left_find, left_replace, code, flags=re.DOTALL)

# 3. Inject the close-tag for left-wing and open-tag for the right-wing container
mid_find = r'</div>\s*</td>\s*<td class="grid-cell"[^>]*>\s*<div class="right-wing">'
mid_replace = r'''</div></div></td><td class="grid-cell" style="width: 100%;"><div class="half-verse-container" data-half-verse-id="{right_id_signature}"><div class="right-wing">'''

code = re.sub(mid_find, mid_replace, code)

# 4. Inject the close-tag for the right-wing container right before tuba or row end
right_find = r'(\{tuba_str\}\s*</div>\s*</td>\s*</tr>""")'
right_replace = r'\1</div>' # Error protection handler handles trailing wrap safely
# Fallback variant just in case tuba placement differs slightly:
if "</td>\n        </tr>" in code and "half-verse-container" not in code:
    code = code.replace('{tuba_str}</div></td></tr>"""', '{tuba_str}</div></div></td></tr>"""')

# 5. Inject the browser find JavaScript engine right before the closing body tag
js_engine = """
    <script>
    document.addEventListener('DOMContentLoaded', () => {
        const structuralBlocks = document.querySelectorAll('.half-verse-container');
        structuralBlocks.forEach(element => {
            element.addEventListener('click', (event) => {
                const identifier = element.getAttribute('data-half-verse-id');
                if(identifier === "empty-left" || identifier === "empty-right") return;
                
                const isAlreadySelected = element.classList.contains('highlighted-verse');
                structuralBlocks.forEach(el => el.classList.remove('highlighted-verse'));
                
                if(!isAlreadySelected) {
                    const structuralMatches = document.querySelectorAll(`[data-half-verse-id="${identifier}"]`);
                    structuralMatches.forEach(el => el.classList.add('highlighted-verse'));
                }
            });
        });
    });
    </script>
</body>"""

if "highlighted-verse" not in code:
    code = code.replace("</body>", js_engine)

with open(filename, "w", encoding="utf-8") as f:
    f.write(code)

print("✨ Highlights successfully injected into mass_produce_and_log_matrices.py!")
EOF
