"""Repair paragraph/list structure in every EPUB under the Kindle Input folder.

The script processes EPUBs recursively, including files in ``Input/Pending``.
It makes only these two changes to embedded HTML/XHTML:

1. Wrap plain-text/inline-only blockquote contents in a paragraph element.
   Blockquotes that already contain paragraphs or other block elements are
   left alone to avoid creating invalid nested markup.
2. In Presentation.html, move the known SimHebrew pronunciation note out of
   the surrounding list by closing the list, wrapping the note in <p>, and
   opening a new list before the next list item.

Each archive is written to a temporary file beside the original, checked, and
atomically replaced only after the rewritten EPUB can be opened successfully.
"""

from __future__ import annotations

import argparse
import codecs
import os
import re
import shutil
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


DEFAULT_INPUT_DIR = Path(r"C:\Users\Bob\KindleProject\Input")
MARKUP_SUFFIXES = {".html", ".htm", ".xhtml"}

BLOCKQUOTE_RE = re.compile(
    r"(?P<open><blockquote\b[^>]*>)(?P<body>.*?)(?P<close></blockquote\s*>)",
    re.IGNORECASE | re.DOTALL,
)
PARAGRAPH_TAG_RE = re.compile(r"<\s*/?\s*p\b", re.IGNORECASE)
BLOCK_CHILD_RE = re.compile(
    r"<\s*/?\s*(?:address|article|aside|blockquote|div|dl|fieldset|figure|"
    r"footer|form|h[1-6]|header|hr|ol|p|pre|section|table|ul)\b",
    re.IGNORECASE,
)

PRESENTATION_NOTE_RE = re.compile(
    r"(?P<li_end></li\s*>)\s*<br\s*/?\s*>\s*"
    r"(?P<note>In\s+addition,\s+the\s+pronunciation\s+of\s+the\s+"
    r"letters\s+a,\s*b,\s*c,\s+and\s+y\s+may\s+vary:)\s*"
    r"<br\s*/?\s*>\s*(?=<li\b)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class RepairCounts:
    blockquotes_wrapped: int = 0
    blockquotes_already_paragraphed: int = 0
    blockquotes_skipped_complex: int = 0
    presentation_lists_split: int = 0


def decode_markup(raw: bytes) -> tuple[str, Callable[[str], bytes]]:
    """Decode markup while retaining its original encoding and any BOM."""
    if raw.startswith(codecs.BOM_UTF8):
        text = raw[len(codecs.BOM_UTF8):].decode("utf-8")
        return text, lambda value: codecs.BOM_UTF8 + value.encode("utf-8")
    if raw.startswith(codecs.BOM_UTF16_LE):
        text = raw[len(codecs.BOM_UTF16_LE):].decode("utf-16-le")
        return text, lambda value: codecs.BOM_UTF16_LE + value.encode("utf-16-le")
    if raw.startswith(codecs.BOM_UTF16_BE):
        text = raw[len(codecs.BOM_UTF16_BE):].decode("utf-16-be")
        return text, lambda value: codecs.BOM_UTF16_BE + value.encode("utf-16-be")

    declaration = re.search(
        br"(?:encoding|charset)\s*=\s*['\"]([^'\"]+)['\"]",
        raw[:1024],
        re.IGNORECASE,
    )
    encoding = declaration.group(1).decode("ascii", errors="ignore") if declaration else "utf-8"
    try:
        text = raw.decode(encoding)
    except (LookupError, UnicodeDecodeError):
        # Latin-1 is a lossless fallback for legacy single-byte files.
        encoding = "latin-1"
        text = raw.decode(encoding)
    return text, lambda value: value.encode(encoding)


def repair_markup(text: str, member_name: str) -> tuple[str, RepairCounts]:
    counts = RepairCounts()

    def repair_blockquote(match: re.Match[str]) -> str:
        body = match.group("body")
        stripped = body.strip()
        if not stripped:
            return match.group(0)

        if PARAGRAPH_TAG_RE.search(body):
            # Existing paragraph structure is preserved; partial or mixed
            # structures are reported for manual attention rather than nested.
            first_tag = re.match(r"<\s*p\b", stripped, re.IGNORECASE)
            last_tag = re.search(r"</\s*p\s*>\s*$", stripped, re.IGNORECASE)
            if first_tag and last_tag:
                counts.blockquotes_already_paragraphed += 1
            else:
                counts.blockquotes_skipped_complex += 1
            return match.group(0)

        if BLOCK_CHILD_RE.search(body):
            counts.blockquotes_skipped_complex += 1
            return match.group(0)

        counts.blockquotes_wrapped += 1
        return f"{match.group('open')}<p>{body}</p>{match.group('close')}"

    repaired = BLOCKQUOTE_RE.sub(repair_blockquote, text)

    if Path(member_name).name.lower() == "presentation.html":
        def split_presentation_list(match: re.Match[str]) -> str:
            note = " ".join(match.group("note").split())
            return f"{match.group('li_end')}\n</ul>\n\n<p>{note}</p>\n\n<ul>\n\n"

        repaired, counts.presentation_lists_split = PRESENTATION_NOTE_RE.subn(
            split_presentation_list, repaired
        )

    return repaired, counts


def scan_epub(epub_path: Path) -> tuple[dict[int, bytes], RepairCounts, int]:
    replacements: dict[int, bytes] = {}
    totals = RepairCounts()
    markup_files = 0

    with zipfile.ZipFile(epub_path, "r") as archive:
        for info in archive.infolist():
            if Path(info.filename).suffix.lower() not in MARKUP_SUFFIXES:
                continue
            markup_files += 1
            raw = archive.read(info)
            text, encode = decode_markup(raw)
            repaired, counts = repair_markup(text, info.filename)
            totals.blockquotes_wrapped += counts.blockquotes_wrapped
            totals.blockquotes_already_paragraphed += counts.blockquotes_already_paragraphed
            totals.blockquotes_skipped_complex += counts.blockquotes_skipped_complex
            totals.presentation_lists_split += counts.presentation_lists_split
            if repaired != text:
                replacements[info.header_offset] = encode(repaired)

    return replacements, totals, markup_files


def rewrite_epub_atomically(epub_path: Path, replacements: dict[int, bytes]) -> None:
    """Rewrite the ZIP without extracting it, then atomically replace source."""
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{epub_path.name}.", suffix=".repair.tmp", dir=epub_path.parent
    )
    os.close(descriptor)
    temp_path = Path(temp_name)

    try:
        with zipfile.ZipFile(epub_path, "r") as source:
            with zipfile.ZipFile(temp_path, "w") as destination:
                destination.comment = source.comment
                for info in source.infolist():
                    replacement = replacements.get(info.header_offset)
                    if replacement is not None:
                        destination.writestr(info, replacement)
                        continue

                    # Stream unchanged images and scores to keep memory use low.
                    with source.open(info, "r") as member_in:
                        with destination.open(info, "w", force_zip64=True) as member_out:
                            shutil.copyfileobj(member_in, member_out, length=1024 * 1024)

        with zipfile.ZipFile(temp_path, "r") as check:
            if check.testzip() is not None:
                raise zipfile.BadZipFile("CRC validation failed after rewrite")
            if check.namelist()[0] != "mimetype":
                raise zipfile.BadZipFile("EPUB mimetype entry is no longer first")
            if check.getinfo("mimetype").compress_type != zipfile.ZIP_STORED:
                raise zipfile.BadZipFile("EPUB mimetype entry is compressed")

        os.replace(temp_path, epub_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def process_epub(epub_path: Path) -> bool:
    replacements, counts, markup_files = scan_epub(epub_path)
    if not replacements:
        print(
            f"  No changes: {epub_path.name} "
            f"({markup_files} markup files, "
            f"{counts.blockquotes_already_paragraphed} blockquotes already paragraphed, "
            f"{counts.blockquotes_skipped_complex} complex blockquotes left for review)"
        )
        return False

    rewrite_epub_atomically(epub_path, replacements)
    print(
        f"  Updated: {epub_path.name} — "
        f"{counts.blockquotes_wrapped} blockquotes wrapped, "
        f"{counts.presentation_lists_split} presentation list(s) split, "
        f"{counts.blockquotes_already_paragraphed} already paragraphed, "
        f"{counts.blockquotes_skipped_complex} complex blockquotes left for review"
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Repair blockquote paragraphs and the Presentation.html list break in EPUBs."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=DEFAULT_INPUT_DIR,
        help=f"EPUB folder to process recursively (default: {DEFAULT_INPUT_DIR})",
    )
    args = parser.parse_args()

    if not args.input_dir.is_dir():
        print(f"Input directory does not exist: {args.input_dir}", file=sys.stderr)
        return 2

    epub_files = sorted(
        path for path in args.input_dir.rglob("*")
        if path.is_file() and path.suffix.lower() == ".epub"
    )
    if not epub_files:
        print(f"No EPUB files found under {args.input_dir}")
        return 0

    print(f"Found {len(epub_files)} EPUB file(s) under {args.input_dir}")
    changed = 0
    failures = 0
    for epub_path in epub_files:
        try:
            changed += process_epub(epub_path)
        except Exception as error:  # Keep processing other volumes after one failure.
            failures += 1
            print(f"  ERROR: {epub_path}: {type(error).__name__}: {error}", file=sys.stderr)

    print(f"\nComplete: updated {changed} EPUB(s); errors: {failures}.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
