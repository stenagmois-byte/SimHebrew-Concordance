"""Split SimHebrew canonical HTML files and optionally refresh the matching EPUB entries.

The generated import set is flat: <book>_split0.html is the navigation-only file,
and <book>_split1.html onward hold chapters. For an EPUB refresh, split0 maps to
the existing <book>.html archive member; all chapter names map directly. The
package manifest and TOC are left intact because the EPUB already uses those names.
"""
from __future__ import annotations

import argparse
import filecmp
import html.entities
import os
import re
import shutil
import tempfile
import zipfile
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from xml.etree import ElementTree

from bs4 import BeautifulSoup

DEFAULT_SOURCE_DIR = Path(r"C:\Users\Bob\Downloads")
DEFAULT_INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
DEFAULT_EPUB = DEFAULT_INPUT_DIR / "The SimHebrew Bible - Jonathan Orr-Stav.epub"
DEFAULT_OUTPUT_ROOT = Path(r"C:\Users\Bob\KindleProject\Output")

CHAPTER_MARKER = re.compile(
    r'<h4\b[^>]*class=["\'][^"\']*\bchapter-head\b[^"\']*["\'][^>]*>.*?</h4>',
    re.I | re.S,
)
GRID_ID = re.compile(r'<div\s+class=["\']grid-h4["\'][^>]*\bid=["\'](a\d+)["\']', re.I)
BOOK_FILE = re.compile(r"^(\d{2}[A-Za-z0-9_ -]+)$")
SPLIT_FILE = re.compile(r"^(\d{2}[A-Za-z0-9_-]+)_split(\d+)\.html$", re.I)


class TagStackParser(HTMLParser):
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.stack: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() not in self.VOID:
            self.stack.append((tag.lower(), self.get_starttag_text()))

    def handle_startendtag(self, tag: str, attrs) -> None:
        pass

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


def decode_source(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("cp1252")


def normalized_base(path: Path) -> str:
    return re.sub(r"\s+", "_", path.stem.strip())


def epub_book_bases(epub_path: Path) -> set[str]:
    with zipfile.ZipFile(epub_path, "r") as archive:
        bases = set()
        for name in archive.namelist():
            if "/" in name or not name.lower().endswith(".html"):
                continue
            split_match = SPLIT_FILE.fullmatch(Path(name).name)
            if split_match:
                # Calibre's split book root is stored as _split0.html. It is
                # the canonical book page for validation, not a chapter file.
                if int(split_match.group(2)) == 0:
                    bases.add(split_match.group(1))
                continue
            stem = Path(name).stem
            match = BOOK_FILE.fullmatch(stem)
            if match and 1 <= int(stem[:2]) <= 24:
                bases.add(stem)
        return bases


def split_one(source: Path, base: str) -> tuple[dict[str, str], int]:
    text = decode_source(source)
    body_match = re.search(r"<body\b[^>]*>", text, re.I)
    markers = list(CHAPTER_MARKER.finditer(text))
    if not body_match or not markers:
        raise ValueError(f"Missing body or chapter-head markers in {source.name}")

    chapters: list[tuple[str, int]] = []
    for index, marker in enumerate(markers):
        start = marker.start()
        if index == 0:
            # Keep the real book_hdr wrapper with chapter 1 when it surrounds the h4.
            book_hdr = text.rfind('<div class="book_hdr"', 0, marker.start())
            if book_hdr >= 0:
                start = book_hdr
        grid = GRID_ID.search(text, marker.end(), min(len(text), marker.end() + 3000))
        if not grid:
            raise ValueError(f"Cannot associate chapter marker {index + 1} with a grid ID in {source.name}")
        chapters.append((grid.group(1), start))

    chapter_ids = [chapter_id for chapter_id, _ in chapters]
    if len(set(chapter_ids)) != len(chapter_ids):
        raise ValueError(f"Duplicate chapter grid IDs in {source.name}")

    def stack_at(position: int) -> list[tuple[str, str]]:
        parser = TagStackParser()
        parser.feed(text[:position])
        return list(parser.stack)

    raw_files: dict[str, str] = {}
    nav_name = f"{base}_split0.html"
    nav_text = text[:chapters[0][1]].rstrip() + "\n</div></div></body></html>\n"
    raw_files[nav_name] = nav_text

    for index, (_chapter_id, start) in enumerate(chapters):
        end = chapters[index + 1][1] if index + 1 < len(chapters) else len(text)
        wrappers = "".join(
            raw for tag, raw in stack_at(start)
            if tag not in {"html", "head", "body"}
        )
        content = text[:body_match.end()] + "\n" + wrappers + "\n" + text[start:end]
        # Close the chapter's open wrapper divs, including a missing outer close in source exports.
        content = re.sub(r"</body>\s*</html>\s*$", "", content, flags=re.I)
        open_divs = len(re.findall(r"<div\b", content, re.I))
        close_divs = len(re.findall(r"</div\s*>", content, re.I))
        if open_divs > close_divs:
            content = content.rstrip() + "\n" + "</div>" * (open_divs - close_divs)
        content = content.rstrip() + "\n</body></html>\n"
        raw_files[f"{base}_split{index + 1}.html"] = content

    # Repoint chapter navigation fragments to their new chapter files.
    id_to_file: dict[str, str] = {}
    for filename, content in raw_files.items():
        for target_id in re.findall(r"\bid=[\"']([^\"']+)[\"']", content):
            id_to_file[target_id] = filename
    href_re = re.compile(r"href=([\"'])#([^\"']+)\1")
    for filename, content in list(raw_files.items()):
        def replace_href(match: re.Match[str]) -> str:
            quote, target = match.group(1), match.group(2)
            destination = id_to_file.get(target)
            if not destination or destination == filename:
                return match.group(0)
            return f"href={quote}{destination}#{target}{quote}"
        raw_files[filename] = href_re.sub(replace_href, content)

    def numeric_entities(serialized: str) -> str:
        def convert(match: re.Match[str]) -> str:
            codepoint = html.entities.name2codepoint.get(match.group(1))
            return f"&#{codepoint};" if codepoint is not None else match.group(0)
        return re.sub(r"&([A-Za-z][A-Za-z0-9]+);", convert, serialized)

    formatted: dict[str, str] = {}
    for filename, content in raw_files.items():
        pretty = BeautifulSoup(content, "html.parser").prettify(formatter="html")
        # The SQL export's DOCTYPE incorrectly contains html attributes. Emit the XHTML root directly.
        pretty = re.sub(r"^<!DOCTYPE[^>]*>\s*", "", pretty, count=1, flags=re.I)
        pretty = re.sub(
            r"<html\b[^>]*>",
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            pretty,
            count=1,
            flags=re.I,
        )
        pretty = "<?xml version='1.0' encoding='utf-8'?>\n" + numeric_entities(pretty)
        try:
            ElementTree.fromstring(pretty)
        except ElementTree.ParseError as exc:
            raise ValueError(f"Generated XHTML is not well-formed for {filename}: {exc}") from exc
        formatted[filename] = pretty
    return formatted, len(chapters)


def generate_files(source_dir: Path, epub_path: Path) -> tuple[dict[str, str], list[str], list[str]]:
    expected = epub_book_bases(epub_path)
    if len(expected) != 24:
        raise ValueError(f"Expected 24 book files in the EPUB; found {len(expected)}")

    source_by_base: dict[str, Path] = {}
    duplicates: list[str] = []
    for path in source_dir.glob("*.html"):
        base = normalized_base(path)
        if base in expected:
            if base in source_by_base:
                duplicates.append(base)
            else:
                source_by_base[base] = path
    if duplicates:
        raise ValueError("Multiple source files map to: " + ", ".join(sorted(set(duplicates))))

    missing = sorted(expected - source_by_base.keys())
    generated: dict[str, str] = {}
    summary: list[str] = []
    for base in sorted(source_by_base, key=lambda value: int(value[:2])):
        files, chapter_count = split_one(source_by_base[base], base)
        generated.update(files)
        summary.append(f"{base}: {chapter_count} chapters plus _split0 navigation")
    return generated, missing, summary


def write_stage(generated: dict[str, str], output_dir: Path, missing: list[str], summary: list[str]) -> None:
    if output_dir.exists() and any(output_dir.iterdir()):
        raise FileExistsError(f"Output directory is not empty; choose a new directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, content in generated.items():
        (output_dir / name).write_text(content, encoding="utf-8", newline="\n")
    manifest = ["SimHebrew split output", "", *summary, "", f"Files written: {len(generated)}"]
    if missing:
        manifest += ["", "Missing source books (not generated):", *missing]
    (output_dir / "split_manifest.txt").write_text("\n".join(manifest) + "\n", encoding="utf-8")


def html_ids(content: str) -> set[str]:
    return {value for _, value in re.findall(r"\bid\s*=\s*([\"'])(.*?)\1", content, re.I | re.S)}


def add_book_toc_anchor(content: str, anchor: str) -> str:
    """Preserve an existing NCX target on the regenerated split0 book heading."""
    if anchor in html_ids(content):
        return content
    escaped = html.escape(anchor, quote=True)
    heading = re.search(
        r"<h[1-6]\b(?=[^>]*\bclass\s*=\s*([\"'])[^\"']*\bbook-head\b[^\"']*\1)[^>]*>",
        content,
        re.I | re.S,
    )
    if heading:
        opening = heading.group(0)
        if re.search(r"\bid\s*=", opening, re.I):
            replacement = f'<span id="{escaped}"></span>\n{opening}'
        else:
            replacement = opening[:-1] + f' id="{escaped}">'
        updated = content[:heading.start()] + replacement + content[heading.end():]
    else:
        body = re.search(r"<body\b[^>]*>", content, re.I)
        if not body:
            raise ValueError(f"Cannot preserve NCX anchor {anchor}: generated page has no book heading or body")
        updated = content[:body.end()] + f'\n<span id="{escaped}"></span>' + content[body.end():]
    try:
        ElementTree.fromstring(updated)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Preserving NCX anchor {anchor} made XHTML invalid: {exc}") from exc
    return updated


def replace_epub(epub_path: Path, output_dir: Path, generated: dict[str, str], missing: list[str], allow_partial: bool) -> Path:
    if missing and not allow_partial:
        raise ValueError("Refusing EPUB update; source HTML is missing for: " + ", ".join(missing))
    backup = epub_path.with_suffix(epub_path.suffix + ".bak")
    backup_matches_source = backup.exists() and filecmp.cmp(epub_path, backup, shallow=False)
    if backup.exists() and not backup_matches_source:
        raise FileExistsError(f"Backup already exists; inspect it before proceeding: {backup}")

    fd, temp_name = tempfile.mkstemp(prefix=epub_path.stem + "_", suffix=".tmp", dir=epub_path.parent)
    os.close(fd)
    temp_path = Path(temp_name)
    try:
        with zipfile.ZipFile(epub_path, "r") as archive:
            names = set(archive.namelist())
            replacements: dict[str, bytes] = {}
            for staged_name, content in generated.items():
                match = SPLIT_FILE.fullmatch(staged_name)
                if not match:
                    raise ValueError(f"Unexpected generated filename: {staged_name}")
                base, suffix = match.group(1), int(match.group(2))
                if suffix == 0:
                    unsplit_root = f"{base}.html"
                    split_root = f"{base}_split0.html"
                    if unsplit_root in names and split_root in names:
                        raise ValueError(
                            f"EPUB contains both possible root pages for {base}; "
                            "resolve the duplicate before replacement"
                        )
                    archive_name = split_root if split_root in names else unsplit_root
                else:
                    archive_name = staged_name
                if archive_name not in names:
                    raise ValueError(f"EPUB has no matching member: {archive_name}")
                replacements[archive_name] = content.encode("utf-8")

            # Require each updated book's chapter count to match the EPUB's existing resources.
            for base in {SPLIT_FILE.fullmatch(name).group(1) for name in generated}:
                staged_nums = {int(SPLIT_FILE.fullmatch(name).group(2)) for name in generated if SPLIT_FILE.fullmatch(name).group(1) == base}
                epub_nums = {int(m.group(1)) for name in names if (m := re.fullmatch(re.escape(base) + r"_split(\d+)\.html", name))}
                split_root_exists = f"{base}_split0.html" in names
                expected_epub_nums = staged_nums if split_root_exists else staged_nums - {0}
                if (
                    staged_nums != set(range(0, max(staged_nums) + 1))
                    or expected_epub_nums != epub_nums
                ):
                    raise ValueError(f"Generated chapter files for {base} do not match the EPUB's existing split files")

            # The existing NCX can point into split0 pages. Keep each referenced
            # anchor if regenerated XHTML no longer carries that legacy ID.
            for ncx_name in (name for name in names if name.lower().endswith(".ncx")):
                ncx_root = ElementTree.fromstring(archive.read(ncx_name))
                for element in ncx_root.iter():
                    if not element.tag.lower().endswith("content"):
                        continue
                    src = element.get("src", "")
                    target, separator, fragment = src.partition("#")
                    if not separator or not fragment or target not in replacements:
                        continue
                    new_content = replacements[target].decode("utf-8")
                    if fragment in html_ids(new_content):
                        continue
                    old_content = archive.read(target).decode("utf-8", "replace")
                    if fragment in html_ids(old_content):
                        replacements[target] = add_book_toc_anchor(new_content, fragment).encode("utf-8")

            with zipfile.ZipFile(temp_path, "w") as out:
                out.comment = archive.comment
                for info in archive.infolist():
                    data = replacements.get(info.filename)
                    if data is None:
                        data = archive.read(info.filename)
                    out.writestr(info, data)
            with zipfile.ZipFile(temp_path, "r") as check:
                bad = check.testzip()
                if bad:
                    raise zipfile.BadZipFile(f"Corrupt member after update: {bad}")
                if check.namelist() != archive.namelist():
                    raise zipfile.BadZipFile("Archive member order or names changed unexpectedly")
        # Close the original ZIP before the atomic replacement. Windows denies
        # renaming an EPUB while this function itself still has it open.
        if not backup_matches_source:
            shutil.copy2(epub_path, backup)
        os.replace(temp_path, epub_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return backup


def main() -> None:
    parser = argparse.ArgumentParser(description="Split SimHebrew HTML into one flat Calibre import set.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR, help="Folder containing the 24 canonical source HTML files (default: Downloads).")
    parser.add_argument("--epub", type=Path, default=DEFAULT_EPUB, help="SimHebrew Bible EPUB used to check book/chapter filenames.")
    parser.add_argument("--output-dir", type=Path, help="Output folder. By default, a timestamped folder is created under KindleProject\\Output.")
    parser.add_argument("--replace-epub", action="store_true", help="After validation, replace matching XHTML entries in the EPUB and keep a .bak backup.")
    parser.add_argument("--allow-partial", action="store_true", help="Allow EPUB replacement when some source books are missing.")
    args = parser.parse_args()

    if not args.source_dir.is_dir():
        parser.error(f"Source directory not found: {args.source_dir}")
    if not args.epub.is_file():
        parser.error(f"EPUB not found: {args.epub}")
    output_dir = args.output_dir or DEFAULT_OUTPUT_ROOT / f"SimHebrew_Import_{datetime.now():%Y%m%d_%H%M%S}"

    generated, missing, summary = generate_files(args.source_dir, args.epub)
    if not generated:
        parser.error(f"No canonical book HTML files found in {args.source_dir}")
    write_stage(generated, output_dir, missing, summary)
    print(f"Wrote {len(generated)} files to one folder: {output_dir}")
    if missing:
        print("Missing source books: " + ", ".join(missing))
    if args.replace_epub:
        backup = replace_epub(args.epub, output_dir, generated, missing, args.allow_partial)
        print(f"Updated EPUB by matching filenames. Backup retained at: {backup}")


if __name__ == "__main__":
    main()
