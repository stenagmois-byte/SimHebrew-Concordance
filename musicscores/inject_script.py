import os

# The exact JavaScript code block we want to inject into every index.html file
js_block_to_inject = """
<script>
document.addEventListener("DOMContentLoaded", () => {
    const links = document.querySelectorAll("a");
    links.forEach(link => {
        const fileTarget = link.getAttribute("href") || "";
        const lowerTarget = fileTarget.toLowerCase();
        if (!lowerTarget.endsWith(".mscz") && !lowerTarget.endsWith(".json") && !lowerTarget.endsWith(".xml")) {
            return;
        }
        let cleanName = fileTarget
            .split('/').pop()
            .split('\\\\').pop()
            .replace(/\\.(mscz|json|xml)$/i, "")
            .replace(/[-_]/g, " ")
            .trim();
        const colorClass = getGematriaMenuClass(cleanName);
        if (colorClass) {
            link.classList.add(colorClass);
            link.style.display = "inline-block";
            link.style.padding = "2px 6px";
            link.style.margin = "2px 1px";
            link.style.borderRadius = "4px";
            link.style.textDecoration = "none";
        }
    });
});
function getGematriaMenuClass(text) {
    if (!text) return '';
    let score = 0;
    for (let i = 0; i < text.length; i++) { score += text.charCodeAt(i); }
    const bucket = score % 5;
    if (bucket === 0) return 'gem-low';
    if (bucket === 1) return 'gem-mid-low';
    if (bucket === 2) return 'gem-mid';
    if (bucket === 3) return 'gem-mid-high';
    return 'gem-high';
}
</script>
</body>
"""

print("Scanning directories for index.html files...")

# Walk through all folders and subfolders starting from the current directory
for root, dirs, files in os.walk("."):
    for file in files:
        if file.lower() == "index.html":
            file_path = os.path.join(root, file)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Check if the file already has the script to avoid injecting it twice
            if "getGematriaMenuClass" in content:
                print(f"-> Skipped (Already Updated): {file_path}")
                continue
                
            # Safely replace the closing body tag with our script + the closing body tag
            if "</body>" in content:
                updated_content = content.replace("</body>", js_block_to_inject)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)
                print(f"-> Successfully Updated: {file_path}")
            else:
                print(f"!! Warning: Could not find </body> tag in {file_path}")

print("\\nDone! All available volume indexes have been successfully color-coded.")
