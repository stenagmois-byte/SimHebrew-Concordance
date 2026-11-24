"""Create a readable text and hyperlink comparison report for two EPUB files."""
from __future__ import annotations

import argparse
import difflib
import html
import sys
import zipfile
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup


HTML_SUFFIXES = {".html", ".xhtml"}


def normalize(value: str) -> str:
    return " ".join(value.split())


def extract_text(archive: zipfile.ZipFile, member: str) -> list[str]:
    raw = archive.read(member).decode("utf-8", errors="replace")
    soup = BeautifulSoup(raw, "html.parser")
    body = soup.body or soup
    for tag in body.find_all(["svg", "script", "style", "noscript"]):
        tag.decompose()

    lines = []
    block_tags = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "tr", "blockquote", "pre", "dt", "dd"]
    for element in body.find_all(block_tags):
        text = normalize(element.get_text(" ", strip=True))
        if text and (not lines or lines[-1] != text):
            lines.append(text)
    if not lines:
        text = normalize(body.get_text(" ", strip=True))
        if text:
            lines.append(text)

    for anchor in body.find_all("a", href=True):
        label = normalize(anchor.get_text(" ", strip=True))
        href = normalize(anchor.get("href", ""))
        if href:
            lines.append(f"[Link] {label} -> {href}")
    return lines


def compare_epubs(old_path: Path, new_path: Path) -> tuple[list[dict[str, object]], dict[str, int]]:
    if not old_path.is_file():
        raise FileNotFoundError(f"Old EPUB not found: {old_path}")
    if not new_path.is_file():
        raise FileNotFoundError(f"New EPUB not found: {new_path}")
    with zipfile.ZipFile(old_path, "r") as old_zip, zipfile.ZipFile(new_path, "r") as new_zip:
        old_members = {name for name in old_zip.namelist() if Path(name).suffix.lower() in HTML_SUFFIXES}
        new_members = {name for name in new_zip.namelist() if Path(name).suffix.lower() in HTML_SUFFIXES}
        rows = []
        stats = {"changed": 0, "added": 0, "removed": 0, "unchanged": 0}
        for member in sorted(old_members | new_members, key=str.casefold):
            before = extract_text(old_zip, member) if member in old_members else []
            after = extract_text(new_zip, member) if member in new_members else []
            status = "added" if member not in old_members else "removed" if member not in new_members else "changed" if before != after else "unchanged"
            stats[status] += 1
            if status == "unchanged":
                continue
            diff = list(difflib.unified_diff(before, after, fromfile=f"Old/{member}", tofile=f"New/{member}", lineterm="", n=2))
            rows.append({"member": member, "status": status, "old_lines": len(before), "new_lines": len(after), "diff": diff})
    return rows, stats


def build_report(rows: list[dict[str, object]], stats: dict[str, int], old_path: Path, new_path: Path) -> str:
    total = sum(stats.values())
    parts = ["""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>EPUB Text Comparison</title>
<style>body{font:16px/1.5 Georgia,serif;max-width:1200px;margin:28px auto;padding:0 18px;background:#fffcf4;color:#222}h1{font-weight:normal;color:#800000}.summary{padding:12px 16px;background:#f3f0e8;border:1px solid #ddd;font:14px/1.6 sans-serif}.file{margin:12px 0;border:1px solid #ddd;background:white;padding:10px 14px}.file summary{cursor:pointer;font:bold 14px sans-serif;color:#800000}.file pre{white-space:pre-wrap;overflow-wrap:anywhere;font:13px/1.45 Consolas,monospace;background:#fafafa;padding:12px;border:1px solid #eee}.changed{border-left:4px solid #b27a00}.added{border-left:4px solid #218838}.removed{border-left:4px solid #b21f2d}.small{color:#555;font-size:.9rem}.hint{margin:16px 0;color:#555}</style></head><body>"""]
    parts.append(f"<h1>EPUB Text Comparison</h1><p class='small'>Old: {html.escape(old_path.name)}<br>New: {html.escape(new_path.name)}</p>")
    parts.append(f"<div class='summary'>HTML/XHTML resources: {total} · Changed: {stats['changed']} · Added: {stats['added']} · Removed: {stats['removed']} · Unchanged: {stats['unchanged']}</div>")
    parts.append("<p class='hint'>SVG artwork and CSS are omitted. Text, verse content, and hyperlink destinations are included. Expand a file to see its line changes.</p>")
    if not rows:
        parts.append("<p>No text or hyperlink differences found.</p>")
    for row in rows:
        member = html.escape(str(row["member"]))
        status = str(row["status"])
        summary = f"{member} — {status} ({row['old_lines']} old lines, {row['new_lines']} new lines)"
        diff = "\n".join(row["diff"])
        if not diff:
            diff = "(No textual detail available for this resource.)"
        parts.append(f"<details class='file {status}'><summary>{html.escape(summary)}</summary><pre>{html.escape(diff)}</pre></details>")
    parts.append("</body></html>")
    return "\n".join(parts)


def choose_latest_pair(folder: Path) -> tuple[Path, Path]:
    candidates = sorted(folder.glob("*.epub"), key=lambda path: path.stat().st_mtime)
    if len(candidates) < 2:
        raise ValueError(f"Need at least two EPUB files in {folder}, or supply both file paths.")
    return candidates[-2], candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old", nargs="?", type=Path, help="Older/reference EPUB")
    parser.add_argument("new", nargs="?", type=Path, help="Newer/candidate EPUB")
    parser.add_argument("--output", type=Path, help="HTML report path (default: beside this script)")
    args = parser.parse_args()

    if bool(args.old) != bool(args.new):
        parser.error("Supply both EPUB paths, or neither to compare the two newest EPUBs beside this tool.")
    if args.old and args.new:
        old_path, new_path = args.old.resolve(), args.new.resolve()
    else:
        old_path, new_path = choose_latest_pair(Path(__file__).resolve().parent)

    output = args.output.resolve() if args.output else Path(__file__).resolve().parent / f"epubcompare_{datetime.now():%Y%m%d_%H%M%S}.html"
    rows, stats = compare_epubs(old_path, new_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(rows, stats, old_path, new_path), encoding="utf-8")
    print(f"Old EPUB: {old_path}")
    print(f"New EPUB: {new_path}")
    print(f"Changed {stats['changed']} files; added {stats['added']}; removed {stats['removed']}; unchanged {stats['unchanged']}.")
    print(f"Report: {output}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    raise SystemExit(main())
