#!/usr/bin/env python3
"""
PDF Text Extraction Script for Document Skimming

Extracts text from PDF files with support for:
- Specific page ranges
- Output limiting
- Document info/metadata

Usage:
    python pdf_extract.py document.pdf --info
    python pdf_extract.py document.pdf --pages 1-10
    python pdf_extract.py document.pdf --pages 1-10,50-60,100-110
    python pdf_extract.py document.pdf --pages 1-10 --max-chars 5000

Dependencies:
    pip install pymupdf  # or: pip install pdfplumber
"""

import argparse
import sys
from pathlib import Path


def parse_page_ranges(ranges_str: str) -> list[tuple[int, int]]:
    """Parse page ranges like '1-10,50-60' into list of (start, end) tuples."""
    ranges = []
    for part in ranges_str.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            if '-' in part:
                start, end = part.split('-', 1)
                ranges.append((int(start), int(end)))
            else:
                page = int(part)
                ranges.append((page, page))
        except ValueError:
            print(f"Warning: Ignoring invalid page range '{part}'", file=sys.stderr)
    return ranges


def extract_with_pymupdf(pdf_path: str, page_ranges: list[tuple[int, int]] | None,
                          max_chars: int, show_info: bool) -> str:
    """Extract text using PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF
    except ImportError:
        return "ERROR: PyMuPDF not installed. Run: pip install pymupdf"

    try:
        with fitz.open(pdf_path) as doc:
            total_pages = len(doc)

            if show_info:
                metadata = doc.metadata
                output = [
                    f"PDF Info: {pdf_path}",
                    f"  Total pages: {total_pages}",
                    f"  Title: {metadata.get('title', 'N/A')}",
                    f"  Author: {metadata.get('author', 'N/A')}",
                    f"  Subject: {metadata.get('subject', 'N/A')}",
                    f"  Creator: {metadata.get('creator', 'N/A')}",
                    "",
                    "Suggested sampling strategy:",
                    f"  Beginning (10%): pages 1-{max(1, total_pages // 10)}",
                    f"  25% mark: pages {total_pages // 4}-{total_pages // 4 + 5}",
                    f"  50% mark: pages {total_pages // 2}-{total_pages // 2 + 5}",
                    f"  75% mark: pages {3 * total_pages // 4}-{3 * total_pages // 4 + 5}",
                    f"  End (10%): pages {total_pages - total_pages // 10}-{total_pages}",
                ]
                return "\n".join(output)

            # Determine which pages to extract
            if page_ranges:
                pages_to_read = set()
                for start, end in page_ranges:
                    for p in range(max(1, start), min(total_pages, end) + 1):
                        pages_to_read.add(p)
                pages_to_read = sorted(pages_to_read)
            else:
                # Default: first 10 pages
                pages_to_read = list(range(1, min(11, total_pages + 1)))

            output_lines = []
            char_count = 0

            for page_num in pages_to_read:
                if char_count >= max_chars:
                    output_lines.append(f"\n[OUTPUT LIMIT REACHED at {max_chars} chars]")
                    break

                page = doc[page_num - 1]  # 0-indexed
                text = page.get_text()

                output_lines.append(f"\n{'='*60}")
                output_lines.append(f"PAGE {page_num} of {total_pages}")
                output_lines.append('='*60)

                remaining_chars = max_chars - char_count
                if len(text) > remaining_chars:
                    text = text[:remaining_chars] + "\n[TRUNCATED]"

                output_lines.append(text)
                char_count += len(text) + 100  # Account for headers

            # Add coverage summary
            coverage = (len(pages_to_read) / total_pages * 100) if total_pages > 0 else 0.0
            summary = [
                f"\n{'='*60}",
                "EXTRACTION SUMMARY",
                '='*60,
                f"Pages extracted: {pages_to_read}",
                f"Coverage: {coverage:.1f}% ({len(pages_to_read)} of {total_pages} pages)",
                f"Characters output: ~{char_count}",
            ]
            output_lines.extend(summary)

            return "\n".join(output_lines)
    except Exception as e:
        return f"ERROR: Could not open PDF: {e}"


def extract_with_pdfplumber(pdf_path: str, page_ranges: list[tuple[int, int]] | None,
                             max_chars: int, show_info: bool) -> str:
    """Extract text using pdfplumber (fallback)."""
    try:
        import pdfplumber
    except ImportError:
        return "ERROR: pdfplumber not installed. Run: pip install pdfplumber"

    try:
        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)

            if show_info:
                output = [
                    f"PDF Info: {pdf_path}",
                    f"  Total pages: {total_pages}",
                    "",
                    "Suggested sampling strategy:",
                    f"  Beginning (10%): pages 1-{max(1, total_pages // 10)}",
                    f"  25% mark: pages {total_pages // 4}-{total_pages // 4 + 5}",
                    f"  50% mark: pages {total_pages // 2}-{total_pages // 2 + 5}",
                    f"  75% mark: pages {3 * total_pages // 4}-{3 * total_pages // 4 + 5}",
                    f"  End (10%): pages {total_pages - total_pages // 10}-{total_pages}",
                ]
                return "\n".join(output)

            # Determine which pages to extract
            if page_ranges:
                pages_to_read = set()
                for start, end in page_ranges:
                    for p in range(max(1, start), min(total_pages, end) + 1):
                        pages_to_read.add(p)
                pages_to_read = sorted(pages_to_read)
            else:
                pages_to_read = list(range(1, min(11, total_pages + 1)))

            output_lines = []
            char_count = 0

            for page_num in pages_to_read:
                if char_count >= max_chars:
                    output_lines.append(f"\n[OUTPUT LIMIT REACHED at {max_chars} chars]")
                    break

                page = pdf.pages[page_num - 1]
                text = page.extract_text() or "[No text extracted]"

                output_lines.append(f"\n{'='*60}")
                output_lines.append(f"PAGE {page_num} of {total_pages}")
                output_lines.append('='*60)

                remaining_chars = max_chars - char_count
                if len(text) > remaining_chars:
                    text = text[:remaining_chars] + "\n[TRUNCATED]"

                output_lines.append(text)
                char_count += len(text) + 100

            coverage = (len(pages_to_read) / total_pages * 100) if total_pages > 0 else 0.0
            summary = [
                f"\n{'='*60}",
                "EXTRACTION SUMMARY",
                '='*60,
                f"Pages extracted: {pages_to_read}",
                f"Coverage: {coverage:.1f}% ({len(pages_to_read)} of {total_pages} pages)",
                f"Characters output: ~{char_count}",
            ]
            output_lines.extend(summary)

            return "\n".join(output_lines)
    except Exception as e:
        return f"ERROR: Could not open PDF: {e}"


def main():
    parser = argparse.ArgumentParser(
        description='Extract text from PDF files for document skimming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.pdf --info
  %(prog)s document.pdf --pages 1-10
  %(prog)s document.pdf --pages 1-10,50-60,100-110
  %(prog)s document.pdf --pages 1-10 --max-chars 5000
        """
    )
    parser.add_argument('pdf_path', help='Path to PDF file')
    parser.add_argument('--pages', '-p', help='Page ranges to extract (e.g., "1-10,50-60")')
    parser.add_argument('--info', '-i', action='store_true', help='Show PDF info and suggested sampling')
    parser.add_argument('--max-chars', '-m', type=int, default=10000,
                        help='Maximum characters to output (default: 10000)')

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"ERROR: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    page_ranges = parse_page_ranges(args.pages) if args.pages else None

    # Try PyMuPDF first, fall back to pdfplumber
    result = extract_with_pymupdf(args.pdf_path, page_ranges, args.max_chars, args.info)
    if result.startswith("ERROR: PyMuPDF not installed"):
        result = extract_with_pdfplumber(args.pdf_path, page_ranges, args.max_chars, args.info)

    print(result)


if __name__ == '__main__':
    main()
