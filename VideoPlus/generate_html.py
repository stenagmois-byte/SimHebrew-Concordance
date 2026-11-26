#!/usr/bin/env python3
"""Build the searchable Archive.org performance directory from spreadsheet.csv."""

from __future__ import annotations

import csv
import html
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote_plus, urlsplit


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "spreadsheet.csv"
OUTPUT = HERE / "PERFORMANCES.html"

BOOK_ORDER = [
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy",
    "Joshua", "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings",
    "2 Kings", "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah",
    "Esther", "Job", "Psalms", "Proverbs", "Ecclesiastes",
    "Song of Songs", "Lamentations", "Isaiah", "Jeremiah", "Ezekiel",
    "Daniel", "Hosea", "Joel", "Amos", "Obadiah", "Jonah", "Micah",
    "Nahum", "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi",
]
BOOK_PATTERNS = sorted(BOOK_ORDER, key=len, reverse=True)


def book_and_reference(raw_reference: str) -> tuple[str, str]:
    label = re.sub(r"\.(?:mp3|wmv)$", "", raw_reference.strip(), flags=re.I)
    comparable = unquote_plus(label).strip()
    if comparable.casefold().startswith("song of songs"):
        return "Song of Songs", comparable[len("Song of Songs"):].strip(" -") or "Performance"
    if comparable.casefold() == "song" or comparable.casefold().startswith("song "):
        return "Song of Songs", comparable[4:].strip(" -") or "Performance"
    for book in BOOK_PATTERNS:
        if comparable.casefold() == book.casefold() or comparable.casefold().startswith(book.casefold() + " "):
            suffix = comparable[len(book):].strip()
            return book, suffix or "Performance"
    return "Other performances", comparable


def collection_label(folder_url: str) -> str:
    path_parts = [unquote_plus(part) for part in urlsplit(folder_url).path.split("/") if part]
    media_index = next((i for i, part in enumerate(path_parts) if part.casefold() in {"mp3", "wmv"}), None)
    if media_index is None:
        return "Archive.org collection"
    names = path_parts[media_index + 1:]
    return " / ".join(names) if names else "Archive.org collection"


def read_records() -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with SOURCE.open(encoding="utf-8-sig", newline="") as source:
        for line_number, row in enumerate(csv.reader(source), 1):
            if not row or not any(cell.strip() for cell in row):
                continue
            if len(row) < 3:
                raise ValueError(f"Row {line_number} needs reference, folder URL, and filename")
            raw_reference, folder_url, filename = (cell.strip() for cell in row[:3])
            if not raw_reference:
                continue
            if not folder_url.startswith("https://archive.org/") or not filename:
                raise ValueError(f"Row {line_number} has an invalid Archive.org folder or filename")

            book, reference = book_and_reference(raw_reference)
            direct_url = folder_url.rstrip("/") + "/" + filename.lstrip("/")
            track = unquote_plus(filename)
            grouped[book].append({
                "reference": reference,
                "track": track,
                "collection": collection_label(folder_url),
                "url": direct_url,
            })
    return grouped


def build_html(grouped: dict[str, list[dict[str, str]]]) -> str:
    books = sorted(
        grouped,
        key=lambda book: (BOOK_ORDER.index(book) if book in BOOK_ORDER else len(BOOK_ORDER), book),
    )
    total = sum(len(records) for records in grouped.values())
    esc = lambda value: html.escape(value, quote=True)

    chunks = ["""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Available Bible Performances</title>
  <style>
    :root { color-scheme: light dark; }
    body { font-family: system-ui, -apple-system, "Segoe UI", sans-serif; line-height: 1.55; max-width: 1100px; margin: 0 auto; padding: 1rem; }
    header { margin-bottom: 1.25rem; }
    .toolbar { position: sticky; top: 0; z-index: 2; padding: .8rem; background: Canvas; border: 1px solid #8886; border-radius: .5rem; }
    input { width: min(100%, 36rem); padding: .65rem; font: inherit; }
    #result-count { margin-left: .6rem; }
    nav { display: flex; flex-wrap: wrap; gap: .4rem .8rem; margin: 1rem 0; }
    nav a { white-space: nowrap; }
    h2 { margin-top: 2rem; border-bottom: 1px solid #8886; padding-bottom: .3rem; }
    table { border-collapse: collapse; width: 100%; margin: .7rem 0 1.7rem; font-size: .95rem; }
    th, td { text-align: left; vertical-align: top; padding: .55rem; border: 1px solid #8886; }
    th { background: color-mix(in srgb, CanvasText 8%, Canvas); }
    td:first-child { white-space: nowrap; }
    .back { display: inline-block; margin-bottom: .75rem; }
    .muted { opacity: .78; }
    @media (max-width: 650px) { td:first-child { white-space: normal; } table { font-size: .86rem; } }
  </style>
</head>
<body>
  <a class="back" href="./index.html">← VideoPlus home</a>
  <header>
    <h1>Available Bible Performances</h1>
    <p class="muted">Browse Archive.org recordings by biblical book. Each link opens the individual audio or video file.</p>
  </header>
"""]

    chunks.append('  <div class="toolbar"><label for="performance-search">Filter by book, reference, track, or collection</label><br>')
    chunks.append('    <input id="performance-search" type="search" placeholder="e.g. Psalms 23, Esther Lamandier, Exodus 20">')
    chunks.append('    <span id="result-count" aria-live="polite"></span></div>\n')
    chunks.append("  <nav aria-label=\"Books with available performances\">\n")
    for book in books:
        slug = "book-" + re.sub(r"[^a-z0-9]+", "-", book.casefold()).strip("-")
        chunks.append(f'    <a href="#{slug}">{esc(book)} ({len(grouped[book])})</a>\n')
    chunks.append("  </nav>\n")

    for book in books:
        slug = "book-" + re.sub(r"[^a-z0-9]+", "-", book.casefold()).strip("-")
        chunks.append(f'  <section id="{slug}">\n    <h2>{esc(book)}</h2>\n')
        chunks.append("    <table>\n      <thead><tr><th>Reference</th><th>Track</th><th>Collection</th><th>Listen / view</th></tr></thead>\n      <tbody>\n")
        for record in grouped[book]:
            searchable = " ".join((book, record["reference"], record["track"], record["collection"]))
            chunks.append(
                '        <tr class="performance-row" data-search="' + esc(searchable.casefold()) + '">'
                f'<td>{esc(record["reference"])}</td>'
                f'<td>{esc(record["track"])}</td>'
                f'<td>{esc(record["collection"])}</td>'
                f'<td><a href="{esc(record["url"])}" target="_blank" rel="noopener">Archive.org ↗</a></td>'
                "</tr>\n"
            )
        chunks.append("      </tbody>\n    </table>\n  </section>\n")

    chunks.append(f"""  <script>
    const search = document.getElementById('performance-search');
    const rows = [...document.querySelectorAll('.performance-row')];
    const sections = [...document.querySelectorAll('section')];
    const count = document.getElementById('result-count');
    function filterPerformances() {{
      const query = search.value.trim().toLocaleLowerCase();
      let visible = 0;
      for (const row of rows) {{
        const show = !query || row.dataset.search.includes(query);
        row.hidden = !show;
        if (show) visible++;
      }}
      for (const section of sections) {{
        section.hidden = !section.querySelector('.performance-row:not([hidden])');
      }}
      count.textContent = `${{visible}} of {total} performances`;
    }}
    search.addEventListener('input', filterPerformances);
    filterPerformances();
  </script>
</body>
</html>
""")
    return "".join(chunks)


def build_index_section(grouped: dict[str, list[dict[str, str]]]) -> str:
    """Render the same dataset directly into the VideoPlus home page."""
    books = sorted(
        grouped,
        key=lambda book: (BOOK_ORDER.index(book) if book in BOOK_ORDER else len(BOOK_ORDER), book),
    )
    total = sum(len(records) for records in grouped.values())
    esc = lambda value: html.escape(value, quote=True)
    chunks = [f'''<style>
  .available-performances .performance-filter {{ position: sticky; top: 0; z-index: 2; padding: .8rem; background: Canvas; border: 1px solid #8886; border-radius: .5rem; }}
  .available-performances input[type="search"] {{ width: min(100%, 36rem); padding: .6rem; font: inherit; }}
  .available-performances .performance-book-nav {{ display: flex; flex-wrap: wrap; gap: .4rem .8rem; margin: 1rem 0; }}
  .available-performances .performance-table {{ border-collapse: collapse; width: 100%; margin: .6rem 0 1.6rem; font-size: .92rem; }}
  .available-performances .performance-table th, .available-performances .performance-table td {{ text-align: left; vertical-align: top; padding: .5rem; border: 1px solid #8886; }}
  .available-performances .performance-table th {{ background: #8882; }}
  .available-performances .performance-book h3 {{ margin-top: 1.5rem; }}
  @media (max-width: 650px) {{ .available-performances .performance-table {{ font-size: .82rem; }} }}
</style>
<section id="available-performances" class="available-performances">
  <h2>Available performances by book</h2>
  <p>Search {total} Archive.org audio and video links by book, reference, track, or collection.</p>
  <div class="performance-filter">
    <label for="performance-filter">Filter performances</label><br>
    <input id="performance-filter" type="search" placeholder="e.g. Psalms 23, Esther Lamandier, Exodus 20">
    <span id="performance-filter-count" aria-live="polite"></span>
  </div>
  <nav class="performance-book-nav" aria-label="Books with available performances">
''']
    for book in books:
        slug = "index-book-" + re.sub(r"[^a-z0-9]+", "-", book.casefold()).strip("-")
        chunks.append(f'    <a href="#{slug}">{esc(book)} ({len(grouped[book])})</a>\n')
    chunks.append("  </nav>\n")

    for book in books:
        slug = "index-book-" + re.sub(r"[^a-z0-9]+", "-", book.casefold()).strip("-")
        chunks.append(f'  <section class="performance-book" id="{slug}"><h3>{esc(book)}</h3>\n')
        chunks.append('    <table class="performance-table"><thead><tr><th>Reference</th><th>Track</th><th>Collection</th><th>Link</th></tr></thead><tbody>\n')
        for record in grouped[book]:
            searchable = " ".join((book, record["reference"], record["track"], record["collection"]))
            chunks.append(
                '      <tr class="index-performance-row" data-search="' + esc(searchable.casefold()) + '">'
                f'<td>{esc(record["reference"])}</td><td>{esc(record["track"])}</td>'
                f'<td>{esc(record["collection"])}</td>'
                f'<td><a href="{esc(record["url"])}" target="_blank" rel="noopener">Archive.org ↗</a></td></tr>\n'
            )
        chunks.append("    </tbody></table></section>\n")
    chunks.append(f'''  <script>
    (() => {{
      const input = document.getElementById('performance-filter');
      const rows = [...document.querySelectorAll('.index-performance-row')];
      const sections = [...document.querySelectorAll('.performance-book')];
      const count = document.getElementById('performance-filter-count');
      function update() {{
        const query = input.value.trim().toLocaleLowerCase();
        let visible = 0;
        for (const row of rows) {{
          const show = !query || row.dataset.search.includes(query);
          row.hidden = !show;
          if (show) visible++;
        }}
        for (const section of sections) {{
          section.hidden = !section.querySelector('.index-performance-row:not([hidden])');
        }}
        count.textContent = `${{visible}} of {total} performances`;
      }}
      input.addEventListener('input', update);
      update();
    }})();
  </script>
</section>''')
    return "".join(chunks)


def main() -> None:
    grouped = read_records()
    OUTPUT.write_text(build_html(grouped), encoding="utf-8")
    index_path = HERE / "index.html"
    index = index_path.read_text(encoding="utf-8")
    start_marker = "<!-- PERFORMANCE_DIRECTORY_START -->"
    end_marker = "<!-- PERFORMANCE_DIRECTORY_END -->"
    if start_marker not in index or end_marker not in index:
        raise ValueError("index.html needs PERFORMANCE_DIRECTORY_START/END markers")
    before, remainder = index.split(start_marker, 1)
    _, after = remainder.split(end_marker, 1)
    index_path.write_text(
        before + start_marker + "\n" + build_index_section(grouped) + "\n" + end_marker + after,
        encoding="utf-8",
    )
    print(f"Wrote {sum(map(len, grouped.values()))} performance links to {OUTPUT} and {index_path}")


if __name__ == "__main__":
    main()
