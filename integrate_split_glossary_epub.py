"""Insert a split glossary into an EPUB copy, leaving the source EPUB untouched."""
from __future__ import annotations

import argparse
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET


DOMAIN_FILE = re.compile(r"^99Glossary_([A-Za-z0-9_-]+)\.html$")


def repair_existing_markup(filename: str, data: bytes) -> bytes:
    """Remove two invalid empty block-level fragments already present in this source EPUB."""
    if filename == "00-5Front-matter.html":
        data, count = re.subn(
            rb"</p>\s*<br\s*/>\s*(?=<p>SimHebrew Bible text copyright)",
            b"</p>\n\n  ",
            data,
            count=1,
            flags=re.I,
        )
        if count != 1:
            raise ValueError("Could not locate the stray front-matter break to repair")
    elif filename == "00-6Introduction.html":
        data, count = re.subn(rb"<i>\s*</i>", b"", data, count=1, flags=re.I)
        if count != 1:
            raise ValueError("Could not locate the empty introduction emphasis element to repair")
    return data


def find_opf(archive: zipfile.ZipFile) -> str:
    container = ET.fromstring(archive.read("META-INF/container.xml"))
    rootfile = next((element for element in container.iter() if element.tag.endswith("rootfile")), None)
    if rootfile is None or not rootfile.get("full-path"):
        raise ValueError("EPUB container.xml does not identify its package document")
    return rootfile.get("full-path")


def add_manifest_items(opf_text: str, domain_files: list[str]) -> str:
    match = re.search(r"<manifest\b[^>]*>(.*?)</manifest>", opf_text, flags=re.I | re.S)
    if not match:
        raise ValueError("Package document has no manifest element")
    current = match.group(1)
    existing_hrefs = set(re.findall(r"\bhref=[\"']([^\"']+)[\"']", current))
    existing_ids = set(re.findall(r"\bid=[\"']([^\"']+)[\"']", current))
    additions = []
    for filename in domain_files:
        if filename in existing_hrefs:
            raise ValueError(f"EPUB already contains glossary domain file {filename}")
        domain_id = DOMAIN_FILE.fullmatch(filename).group(1)
        item_id = f"glossary_{domain_id}"
        if item_id in existing_ids:
            raise ValueError(f"Manifest ID already exists: {item_id}")
        existing_ids.add(item_id)
        additions.append(f'    <item id="{item_id}" href="{filename}" media-type="application/xhtml+xml"/>')
    new_manifest = current.rstrip() + "\n" + "\n".join(additions) + "\n  "
    updated = opf_text[:match.start(1)] + new_manifest + opf_text[match.end(1):]
    ET.fromstring(updated)
    return updated


def add_spine_items(opf_text: str, domain_files: list[str]) -> str:
    match = re.search(r"<spine\b[^>]*>(.*?)</spine>", opf_text, flags=re.I | re.S)
    if not match:
        raise ValueError("Package document has no spine element")
    current = match.group(1)
    existing = set(re.findall(r"\bidref=[\"']([^\"']+)[\"']", current))
    additions = []
    for filename in domain_files:
        domain_id = DOMAIN_FILE.fullmatch(filename).group(1)
        itemref = f"glossary_{domain_id}"
        if itemref not in existing:
            additions.append(f'    <itemref idref="{itemref}"/>')
            existing.add(itemref)
    if not additions:
        return opf_text
    new_spine = current.rstrip() + "\n" + "\n".join(additions) + "\n  "
    updated = opf_text[:match.start(1)] + new_spine + opf_text[match.end(1):]
    ET.fromstring(updated)
    return updated


def add_ncx_glossary_entry(ncx_text: str) -> str:
    root = ET.fromstring(ncx_text)
    nav_map = next((element for element in root.iter() if element.tag.endswith("navMap")), None)
    if nav_map is None:
        raise ValueError("NCX has no navMap")
    for point in (element for element in nav_map.iter() if element.tag.endswith("navPoint")):
        content = next((child for child in point if child.tag.endswith("content")), None)
        if content is not None and content.get("src", "").split("#", 1)[0] == "99Glossary.html":
            return ncx_text
    play_orders = [int(point.get("playOrder", "0")) for point in nav_map.iter() if point.tag.endswith("navPoint")]
    next_order = max(play_orders, default=0) + 1
    point_id = "glossary-domain-index"
    used_ids = {element.get("id") for element in nav_map.iter() if element.get("id")}
    while point_id in used_ids:
        point_id += "-1"
    nav_namespace = nav_map.tag.partition("}")[0].strip("{")
    q = lambda local: f"{{{nav_namespace}}}{local}"
    point = ET.SubElement(nav_map, q("navPoint"), {"id": point_id, "playOrder": str(next_order)})
    nav_label = ET.SubElement(point, q("navLabel"))
    ET.SubElement(nav_label, q("text")).text = "Glossary"
    ET.SubElement(point, q("content"), {"src": "99Glossary.html"})
    # Keep the original NCX formatting and namespaces while inserting the new node.
    closing = re.search(r"</(?:[A-Za-z_][\w.-]*:)?navMap\s*>", ncx_text, flags=re.I)
    if not closing:
        raise ValueError("Could not locate navMap close tag in NCX")
    parent_open = re.search(r"<(?:[A-Za-z_][\w.-]*:)?navMap\b[^>]*>", ncx_text, flags=re.I)
    if not parent_open:
        raise ValueError("Could not locate navMap opening tag in NCX")
    prefix_match = re.match(r"<([A-Za-z_][\w.-]*:)?navMap", parent_open.group(0), flags=re.I)
    prefix = prefix_match.group(1) or ""
    indent = "    "
    point_xml = (
        f'{indent}<{prefix}navPoint id="{point_id}" playOrder="{next_order}">\n'
        f'{indent}  <{prefix}navLabel><{prefix}text>Glossary</{prefix}text></{prefix}navLabel>\n'
        f'{indent}  <{prefix}content src="99Glossary.html"/>\n'
        f'{indent}</{prefix}navPoint>\n  '
    )
    updated = ncx_text[:closing.start()] + point_xml + ncx_text[closing.start():]
    ET.fromstring(updated)
    return updated


def package_split_glossary(source_epub: Path, split_dir: Path, output_epub: Path) -> None:
    if source_epub.resolve() == output_epub.resolve():
        raise ValueError("Output must be a separate EPUB copy")
    if output_epub.exists():
        raise FileExistsError(f"Output EPUB already exists: {output_epub}")
    index_file = split_dir / "99Glossary.html"
    if not index_file.is_file():
        raise FileNotFoundError(f"Split glossary index missing: {index_file}")
    domain_paths = sorted(
        (path for path in split_dir.glob("99Glossary_*.html") if DOMAIN_FILE.fullmatch(path.name)),
        key=lambda path: path.name.casefold(),
    )
    if not domain_paths:
        raise ValueError(f"No 99Glossary_<domain>.html files in {split_dir}")
    replacements = {"99Glossary.html": index_file.read_bytes()}
    replacements.update({path.name: path.read_bytes() for path in domain_paths})

    output_epub.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_epub, "r") as source:
        names = source.namelist()
        if not names or names[0] != "mimetype" or source.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            raise ValueError("Source EPUB does not have the required first, uncompressed mimetype member")
        if "99Glossary.html" not in names:
            raise FileNotFoundError("Source EPUB has no 99Glossary.html to replace")
        collisions = set(replacements) & (set(names) - {"99Glossary.html"})
        if collisions:
            raise FileExistsError("Source EPUB already has: " + ", ".join(sorted(collisions)))
        opf_path = find_opf(source)
        opf_text = source.read(opf_path).decode("utf-8")
        domain_names = [path.name for path in domain_paths]
        opf_text = add_manifest_items(opf_text, domain_names)
        opf_text = add_spine_items(opf_text, domain_names)
        ncx_path = next((name for name in names if name.lower().endswith(".ncx")), None)
        if ncx_path:
            ncx_text = add_ncx_glossary_entry(source.read(ncx_path).decode("utf-8"))
            replacements[ncx_path] = ncx_text.encode("utf-8")
        replacements[opf_path] = opf_text.encode("utf-8")

        with zipfile.ZipFile(output_epub, "x") as output:
            output.comment = source.comment
            for info in source.infolist():
                data = replacements.pop(info.filename, source.read(info.filename))
                data = repair_existing_markup(info.filename, data)
                output.writestr(info, data)
            for filename, data in sorted(replacements.items()):
                output.writestr(filename, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    with zipfile.ZipFile(output_epub, "r") as result:
        corrupt = result.testzip()
        if corrupt:
            output_epub.unlink(missing_ok=True)
            raise zipfile.BadZipFile(f"Corrupt output member: {corrupt}")
        if result.namelist()[0] != "mimetype" or result.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
            output_epub.unlink(missing_ok=True)
            raise zipfile.BadZipFile("Output EPUB no longer has mimetype first and uncompressed")
        if len(result.namelist()) != len(names) + len(domain_paths):
            output_epub.unlink(missing_ok=True)
            raise zipfile.BadZipFile("Unexpected output member count")
        package = ET.fromstring(result.read(opf_path))
        ns = {"opf": package.tag.partition("}")[0].strip("{")}
        hrefs = {item.get("href") for item in package.findall("opf:manifest/opf:item", ns)}
        missing = set(path.name for path in domain_paths) - hrefs
        if missing:
            output_epub.unlink(missing_ok=True)
            raise ValueError("New glossary pages missing from package manifest: " + ", ".join(sorted(missing)))
        spine_refs = {item.get("idref") for item in package.findall("opf:spine/opf:itemref", ns)}
        missing_spine = {f"glossary_{DOMAIN_FILE.fullmatch(path.name).group(1)}" for path in domain_paths} - spine_refs
        if missing_spine:
            output_epub.unlink(missing_ok=True)
            raise ValueError("New glossary pages missing from spine: " + ", ".join(sorted(missing_spine)))
        if ncx_path and b"99Glossary.html" not in result.read(ncx_path):
            output_epub.unlink(missing_ok=True)
            raise ValueError("Glossary index is absent from the NCX navigation")

    print(f"Created {output_epub} with {len(domain_paths)} glossary domain pages")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_epub", type=Path)
    parser.add_argument("split_dir", type=Path)
    parser.add_argument("output_epub", type=Path)
    args = parser.parse_args()
    package_split_glossary(args.source_epub, args.split_dir, args.output_epub)


if __name__ == "__main__":
    main()
