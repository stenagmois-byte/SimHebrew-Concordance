"""Compare glossary content by semantic domain in HTML files, directories, or EPUBs."""
from __future__ import annotations

import argparse
import html
import re
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup


SPLIT_NAME = re.compile(r"^99Glossary_([A-Za-z0-9_-]+)\.html$", re.I)


def normalize_text(value: str) -> str:
    return " ".join(value.split())


def extract_sections(content: str, fallback_id: str | None = None) -> dict[str, list[dict[str, object]]]:
    soup = BeautifulSoup(content, "html.parser")
    body = soup.body or soup
    markers = body.select("div.split-here[id]")
    if not markers:
        if fallback_id:
            markers = [None]
        else:
            return {}
    result = {}
    for index, marker in enumerate(markers):
        if marker is None:
            nodes = [body]
            domain_id = fallback_id
        else:
            domain_id = marker["id"]
            nodes = [marker]
            node = marker.next_sibling
            while node is not None and not (
                getattr(node, "name", None) == "div"
                and "split-here" in (node.get("class") or [])
                and node.has_attr("id")
            ):
                nodes.append(node)
                node = node.next_sibling
        entries = []
        for node in nodes:
            if not getattr(node, "name", None):
                continue
            for row in node.select("tr") if hasattr(node, "select") else []:
                cells = row.find_all(["th", "td"], recursive=False)
                if not cells:
                    continue
                parts = []
                links = []
                for cell in cells:
                    text = normalize_text(cell.get_text(" ", strip=True))
                    parts.append(text)
                    links.extend({
                        "label": normalize_text(link.get_text(" ", strip=True)),
                        "href": link.get("href", ""),
                    } for link in cell.find_all("a", href=True))
                display = " | ".join(parts)
                key = links[0]["href"].split("#", 1)[-1] if links else display.casefold()
                entries.append({"key": key, "display": display, "links": links})
        if not entries:
            for node in nodes:
                if getattr(node, "name", None):
                    text = normalize_text(node.get_text(" ", strip=True))
                    if text:
                        links = [{"label": normalize_text(link.get_text(" ", strip=True)), "href": link.get("href", "")} for link in node.find_all("a", href=True)]
                        key = links[0]["href"].split("#", 1)[-1] if links else text.casefold()
                        entries.append({"key": key, "display": text, "links": links})
        result[domain_id] = entries
    return result


def load_source(source: Path) -> dict[str, list[dict[str, object]]]:
    if source.is_dir():
        split_files = {}
        for path in source.glob("99Glossary_*.html"):
            match = SPLIT_NAME.fullmatch(path.name)
            if match:
                split_files[match.group(1)] = path
        if split_files:
            result = {}
            for domain_id, path in split_files.items():
                result.update(extract_sections(path.read_text(encoding="utf-8"), domain_id))
            return result
        candidates = [source / "99Glossary.html", source / "glossary.html"]
        file = next((path for path in candidates if path.is_file()), None)
        if file is None:
            raise FileNotFoundError(f"No glossary HTML found in {source}")
        return extract_sections(file.read_text(encoding="utf-8"))
    if source.suffix.lower() == ".epub":
        with zipfile.ZipFile(source, "r") as archive:
            names = archive.namelist()
            split_files = {}
            for name in names:
                basename = Path(name).name
                match = SPLIT_NAME.fullmatch(basename)
                if match:
                    split_files[match.group(1)] = name
            if split_files:
                result = {}
                for domain_id, name in split_files.items():
                    result.update(extract_sections(archive.read(name).decode("utf-8", "replace"), domain_id))
                return result
            monolithic = next((name for name in names if Path(name).name.lower() == "99glossary.html"), None)
            if monolithic is None:
                raise FileNotFoundError(f"No 99Glossary.html found in {source}")
            return extract_sections(archive.read(monolithic).decode("utf-8", "replace"))
    if source.is_file():
        return extract_sections(source.read_text(encoding="utf-8"))
    raise FileNotFoundError(source)


def row_map(entries: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    result = {}
    duplicates = {}
    for entry in entries:
        key = str(entry["key"])
        duplicates[key] = duplicates.get(key, 0) + 1
        unique_key = f"{key}::{duplicates[key]}"
        result[unique_key] = entry
    return result


def entry_cell(entry: dict[str, object] | None) -> str:
    if entry is None:
        return "<span class='empty'>—</span>"
    output = [f"<div class='entry'>{html.escape(str(entry['display']))}</div>"]
    links = entry.get("links", [])
    if links:
        targets = []
        for link in links:
            label = html.escape(str(link.get("label", "open concordance")))
            href = html.escape(str(link.get("href", "")), quote=True)
            targets.append(f"<a href='{href}'>{label}</a> <code>{html.escape(str(link.get('href', '')))}</code>")
        output.append("<div class='links'>" + "<br>".join(targets) + "</div>")
    return "".join(output)


def build_report(old: dict[str, list[dict[str, object]]], new: dict[str, list[dict[str, object]]], old_name: str, new_name: str) -> str:
    ids = set(old) | set(new)
    changes = []
    for domain_id in ids:
        before, after = old.get(domain_id), new.get(domain_id)
        before_rows, after_rows = row_map(before or []), row_map(after or [])
        entry_changes = []
        for key in before_rows.keys() | after_rows.keys():
            old_entry, new_entry = before_rows.get(key), after_rows.get(key)
            if old_entry is None:
                entry_changes.append(("added", None, new_entry))
            elif new_entry is None:
                entry_changes.append(("removed", old_entry, None))
            elif old_entry != new_entry:
                entry_changes.append(("edited", old_entry, new_entry))
        domain_status = "added" if before is None else "removed" if after is None else "changed"
        if entry_changes or before is None or after is None:
            changes.append((domain_id, domain_status, entry_changes))
    priority = {name: index for index, name in enumerate(("People", "Person", "Location"))}
    changes.sort(key=lambda row: (priority.get(row[0], 99), row[0].casefold()))
    counts = {status: sum(1 for _id, state, _items in changes if state == status) for status in ("added", "removed", "changed")}
    entry_count = sum(len(items) for _id, _state, items in changes)
    chunks = ["""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Glossary Domain Comparison</title>
<style>body{font:16px/1.5 Georgia,serif;max-width:1250px;margin:30px auto;padding:0 18px;background:#fffcf4;color:#222}h1{color:#800000;font-weight:normal}.summary{padding:12px 16px;background:#f3f0e8;border:1px solid #ddd;font-family:sans-serif}.domain{margin:14px 0;border:1px solid #ddd;background:#fff;padding:10px 14px}.domain summary{cursor:pointer;font-family:sans-serif;font-weight:bold;color:#800000}.domain-table{width:100%;border-collapse:collapse;margin-top:10px;font:14px/1.45 sans-serif}.domain-table th,.domain-table td{border:1px solid #ddd;padding:9px;vertical-align:top;text-align:left}.domain-table th{background:#f3f0e8;color:#800000}.domain-table td:first-child{width:82px;font-weight:bold}.domain-table td:nth-child(2),.domain-table td:nth-child(3){width:46%}.entry{font-size:1rem}.links{margin-top:5px;color:#555;font-size:.82rem;overflow-wrap:anywhere}.links code{font-size:.78rem}.edited{background:#fff9e8}.added{background:#f0fbf3}.removed{background:#fff2f2}.empty{color:#888}.small{color:#555;font-size:.9rem}.focus{border-top:3px solid #800000}</style></head><body>"""]
    chunks.append(f"<h1>Glossary Change Review</h1><p class='small'>Old: {html.escape(Path(old_name).name)}<br>New: {html.escape(Path(new_name).name)}</p>")
    chunks.append(f"<div class='summary'>Domains: {len(ids)} · Changed: {counts['changed']} · Added: {counts['added']} · Removed: {counts['removed']} · Changed entries: {entry_count}</div>")
    if not changes:
        chunks.append("<p>No semantic-domain differences found.</p>")
    for domain_id, status, items in changes:
        open_attr = " open" if domain_id in priority else ""
        chunks.append(f"<details class='domain {status}{' focus' if domain_id in priority else ''}'{open_attr}><summary>{html.escape(domain_id)} — {len(items)} changed entries</summary>")
        chunks.append("<table class='domain-table'><thead><tr><th>Change</th><th>Previous entry</th><th>Current entry</th></tr></thead><tbody>")
        for entry_status, before_entry, after_entry in sorted(items, key=lambda item: str((item[1] or item[2])['display']).casefold()):
            chunks.append(f"<tr class='{entry_status}'><td>{entry_status.title()}</td><td>{entry_cell(before_entry)}</td><td>{entry_cell(after_entry)}</td></tr>")
        chunks.append("</tbody></table></details>")
    chunks.append("</body></html>")
    return "\n".join(chunks)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--old", required=True, type=Path, help="Old monolithic/split glossary, directory, or EPUB")
    parser.add_argument("--new", required=True, type=Path, help="New monolithic/split glossary, directory, or EPUB")
    parser.add_argument("--output", required=True, type=Path, help="HTML comparison report path")
    args = parser.parse_args()
    old = load_source(args.old)
    new = load_source(args.new)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_report(old, new, str(args.old), str(args.new)), encoding="utf-8")
    changed = sum(old.get(key) != new.get(key) for key in set(old) | set(new))
    print(f"Compared {len(set(old) | set(new))} semantic domains; {changed} changed, report: {args.output}")


if __name__ == "__main__":
    main()
