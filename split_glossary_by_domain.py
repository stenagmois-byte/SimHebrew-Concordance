"""Split glossary.html at its div.split-here markers for EPUB staging."""
from __future__ import annotations

import argparse
import copy
import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup


def xhtml_text(page: BeautifulSoup) -> str:
    rendered = page.prettify(formatter="minimal")
    rendered = re.sub(r"^<!DOCTYPE[^>]*>\s*", "", rendered, count=1, flags=re.I)
    rendered = re.sub(r"<html\b[^>]*>", '<html xmlns="http://www.w3.org/1999/xhtml">', rendered, count=1, flags=re.I)
    result = "<?xml version='1.0' encoding='utf-8'?>\n" + rendered
    ET.fromstring(result)
    return result


def domain_sections(soup: BeautifulSoup):
    body = soup.body
    if body is None:
        raise ValueError("Glossary source has no body element")
    markers = body.select("div.split-here[id]")
    if not markers:
        raise ValueError("No div.split-here[id] semantic-domain markers found")
    ids = [marker["id"] for marker in markers]
    if len(ids) != len(set(ids)):
        raise ValueError("Semantic-domain marker IDs must be unique")
    for domain_id in ids:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", domain_id):
            raise ValueError(f"Unsafe domain ID for an output filename: {domain_id!r}")

    sections = []
    for marker in markers:
        nodes = [copy.deepcopy(marker)]
        node = marker.next_sibling
        while node is not None and not (
            getattr(node, "name", None) == "div"
            and "split-here" in (node.get("class") or [])
            and node.has_attr("id")
        ):
            nodes.append(copy.deepcopy(node))
            node = node.next_sibling
        heading = marker.get_text(" ", strip=True)
        sections.append((marker["id"], heading or marker["id"], nodes))
    return sections


def make_page(source: BeautifulSoup, title: str, body_nodes) -> BeautifulSoup:
    page = BeautifulSoup("", "html.parser")
    root = page.new_tag("html", attrs={"xmlns": "http://www.w3.org/1999/xhtml"})
    page.append(root)
    if source.head:
        head = copy.deepcopy(source.head)
        title_node = head.find("title")
        if title_node:
            title_node.string = title
        else:
            title_node = page.new_tag("title")
            title_node.string = title
            head.append(title_node)
    else:
        head = page.new_tag("head")
        title_node = page.new_tag("title")
        title_node.string = title
        head.append(title_node)
    root.append(head)
    body = page.new_tag("body")
    for node in body_nodes:
        cloned = copy.deepcopy(node)
        if getattr(cloned, "name", None) == "style":
            cloned["type"] = "text/css"
            head.append(cloned)
        else:
            body.append(cloned)
    root.append(body)
    return page


def read_source(source_path: Path) -> str:
    if source_path.suffix.lower() == ".epub":
        with zipfile.ZipFile(source_path, "r") as archive:
            member = next((name for name in archive.namelist() if Path(name).name.lower() == "99glossary.html"), None)
            if member is None:
                raise FileNotFoundError(f"No 99Glossary.html found in {source_path}")
            return archive.read(member).decode("utf-8", errors="replace")
    return source_path.read_text(encoding="utf-8")


def split_glossary(source_path: Path, output_dir: Path) -> list[Path]:
    source = BeautifulSoup(read_source(source_path), "html.parser")
    sections = domain_sections(source)
    body = source.body
    first_marker = body.select_one("div.split-here[id]")
    intro = []
    for node in body.children:
        if node is first_marker:
            break
        intro.append(copy.deepcopy(node))

    base_body = [node for node in intro if getattr(node, "name", None) != "style"]
    style_nodes = [copy.deepcopy(node) for node in intro if getattr(node, "name", None) == "style"]
    toc_body = [*style_nodes]
    heading = source.new_tag("h1")
    heading.string = "Glossary"
    toc_body.extend(base_body)
    toc_body.append(heading)
    toc = source.new_tag("div", attrs={"class": ["glossary", "domain-toc"]})
    for domain_id, domain_name, _nodes in sections:
        item = source.new_tag("div")
        link = source.new_tag("a", href=f"99Glossary_{domain_id}.html#{domain_id}")
        link.string = domain_name
        item.append(link)
        toc.append(item)
    toc_body.append(toc)
    toc_style = source.new_tag("style")
    toc_style.string = ".domain-toc { column-count: 3; column-gap: 1.2em; } .domain-toc > div { break-inside: avoid; padding: 2px 0; } .glossary-back { margin: 0 0 1em; font-family: sans-serif; }"
    toc_body.insert(len(style_nodes), toc_style)
    pages: list[tuple[str, str]] = [("99Glossary.html", xhtml_text(make_page(source, "Glossary", toc_body)))]

    for domain_id, domain_name, nodes in sections:
        page_body = [*style_nodes]
        back = source.new_tag("p", attrs={"class": "glossary-back"})
        back_link = source.new_tag("a", href="99Glossary.html")
        back_link.string = "← All semantic domains"
        back.append(back_link)
        page_body.extend([back, *nodes])
        page = make_page(source, f"Glossary — {domain_name}", page_body)
        pages.append((f"99Glossary_{domain_id}.html", xhtml_text(page)))

    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, content in pages:
        path = output_dir / name
        path.write_text(content, encoding="utf-8", newline="\n")
        written.append(path)
    manifest = ["Split glossary staging output", "", f"Source: {source_path}", f"Domains: {len(sections)}", "", *[f"99Glossary_{domain_id}.html — {domain_name}" for domain_id, domain_name, _ in sections]]
    (output_dir / "split_glossary_manifest.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Source 99Glossary.html file or EPUB containing div.split-here markers")
    parser.add_argument("output", type=Path, help="New or empty output directory")
    args = parser.parse_args()
    written = split_glossary(args.source, args.output)
    print(f"Wrote {len(written)} XHTML files for {len(written) - 1} semantic domains to {args.output}")


if __name__ == "__main__":
    main()
