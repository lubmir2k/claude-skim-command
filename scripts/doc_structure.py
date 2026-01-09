#!/usr/bin/env python3
"""
Document Structure Analyzer for Document Skimming

Analyzes document structure to identify:
- Headers and sections
- Document length and sections
- Optimal sampling points

Usage:
    python doc_structure.py document.txt
    python doc_structure.py document.txt --format markdown
    python doc_structure.py document.pdf

Dependencies:
    For PDFs: pip install pymupdf  # or pdfplumber
"""

import argparse
import re
import sys
from pathlib import Path


def analyze_text_structure(filepath: str, format_hint: str = 'auto') -> dict:
    """Analyze structure of a text file."""

    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except (FileNotFoundError, IOError, UnicodeDecodeError) as e:
        return {'error': f'Error reading file: {e}'}

    lines = content.split('\n')
    total_lines = len(lines)
    total_chars = len(content)
    total_words = len(content.split())

    # Detect format if auto
    if format_hint == 'auto':
        if re.search(r'^#{1,6}\s', content, re.MULTILINE):
            format_hint = 'markdown'
        elif re.search(r'^\\(section|chapter|title)\{', content, re.MULTILINE):
            format_hint = 'latex'
        elif re.search(r'^Chapter \d|^CHAPTER \d|^\d+\.\s+[A-Z]', content, re.MULTILINE):
            format_hint = 'book'
        else:
            format_hint = 'plain'

    # Find headers based on format
    headers = []

    if format_hint == 'markdown':
        pattern = r'^(#{1,6})\s+(.+)$'
        for i, line in enumerate(lines):
            match = re.match(pattern, line)
            if match:
                level = len(match.group(1))
                headers.append({
                    'line': i + 1,
                    'level': level,
                    'text': match.group(2).strip()
                })

    elif format_hint == 'latex':
        patterns = [
            (r'\\chapter\{([^}]+)\}', 1),
            (r'\\section\{([^}]+)\}', 2),
            (r'\\subsection\{([^}]+)\}', 3),
        ]
        for i, line in enumerate(lines):
            for pattern, level in patterns:
                match = re.search(pattern, line)
                if match:
                    headers.append({
                        'line': i + 1,
                        'level': level,
                        'text': match.group(1).strip()
                    })

    elif format_hint == 'book':
        patterns = [
            (r'^(Chapter|CHAPTER)\s+(\d+|[IVXLC]+)[:\.]?\s*(.*)$', 1),
            (r'^(\d+)\.\s+([A-Z][^.]+)$', 2),
            (r'^(\d+\.\d+)\s+(.+)$', 3),
        ]
        for i, line in enumerate(lines):
            for pattern, level in patterns:
                match = re.match(pattern, line.strip())
                if match:
                    text = match.group(2) if level > 1 else f'{match.group(1)} {match.group(2)} {match.group(3)}'
                    headers.append({
                        'line': i + 1,
                        'level': level,
                        'text': text.strip()
                    })
                    break

    else:  # plain
        # Look for all-caps lines or lines ending with colon
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and (
                (stripped.isupper() and len(stripped) > 3 and len(stripped) < 100) or
                (stripped.endswith(':') and len(stripped) < 80 and stripped[:-1].replace(' ', '').isalpha())
            ):
                headers.append({
                    'line': i + 1,
                    'level': 1 if stripped.isupper() else 2,
                    'text': stripped.rstrip(':')
                })

    # Calculate sections based on headers
    sections = []
    for i, header in enumerate(headers):
        start = header['line']
        end = headers[i + 1]['line'] - 1 if i + 1 < len(headers) else total_lines
        sections.append({
            'name': header['text'],
            'start_line': start,
            'end_line': end,
            'line_count': end - start + 1
        })

    # Calculate sampling points
    chunk_size = max(1, total_lines // 6)  # Ensure at least 1 to avoid invalid ranges
    sampling_points = {
        'beginning': (1, min(total_lines // 10, 100)) if total_lines > 10 else (1, total_lines),
        '25_percent': (total_lines // 4, min(total_lines, total_lines // 4 + 50)),
        '50_percent': (total_lines // 2, min(total_lines, total_lines // 2 + 50)),
        '75_percent': (3 * total_lines // 4, min(total_lines, 3 * total_lines // 4 + 50)),
        'end': (max(1, total_lines - total_lines // 10), total_lines),
        'chunks': [(1, total_lines)] if total_lines < 6 else [
            (i * chunk_size + 1, min((i + 1) * chunk_size, total_lines))
            for i in range(6)
        ]
    }

    return {
        'filepath': filepath,
        'format': format_hint,
        'total_lines': total_lines,
        'total_chars': total_chars,
        'total_words': total_words,
        'headers': headers[:50],  # Limit output
        'sections': sections[:30],  # Limit output
        'sampling_points': sampling_points
    }


def analyze_pdf_structure(filepath: str) -> dict:
    """Analyze structure of a PDF file."""

    # Try PyMuPDF
    try:
        import fitz
        with fitz.open(filepath) as doc:
            total_pages = len(doc)

            # Get TOC if available
            toc = doc.get_toc()

        # Calculate sampling points
        chunk_size = max(1, total_pages // 6)  # Ensure at least 1 to avoid invalid ranges
        sampling_points = {
            'beginning': (1, max(1, total_pages // 10)) if total_pages > 10 else (1, total_pages),
            '25_percent': (total_pages // 4, min(total_pages, total_pages // 4 + 5)),
            '50_percent': (total_pages // 2, min(total_pages, total_pages // 2 + 5)),
            '75_percent': (3 * total_pages // 4, min(total_pages, 3 * total_pages // 4 + 5)),
            'end': (max(1, total_pages - total_pages // 10), total_pages),
            'chunks': [(1, total_pages)] if total_pages < 6 else [
                (i * chunk_size + 1, min((i + 1) * chunk_size, total_pages))
                for i in range(6)
            ]
        }

        return {
            'filepath': filepath,
            'format': 'pdf',
            'total_pages': total_pages,
            'toc': toc[:30] if toc else [],  # Limit output
            'sampling_points': sampling_points
        }

    except ImportError:
        pass

    # Try pdfplumber
    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            total_pages = len(pdf.pages)

        chunk_size = max(1, total_pages // 6)  # Ensure at least 1 to avoid invalid ranges
        sampling_points = {
            'beginning': (1, max(1, total_pages // 10)) if total_pages > 10 else (1, total_pages),
            '25_percent': (total_pages // 4, min(total_pages, total_pages // 4 + 5)),
            '50_percent': (total_pages // 2, min(total_pages, total_pages // 2 + 5)),
            '75_percent': (3 * total_pages // 4, min(total_pages, 3 * total_pages // 4 + 5)),
            'end': (max(1, total_pages - total_pages // 10), total_pages),
            'chunks': [(1, total_pages)] if total_pages < 6 else [
                (i * chunk_size + 1, min((i + 1) * chunk_size, total_pages))
                for i in range(6)
            ]
        }

        return {
            'filepath': filepath,
            'format': 'pdf',
            'total_pages': total_pages,
            'toc': [],
            'sampling_points': sampling_points
        }

    except ImportError:
        return {'error': 'No PDF library available. Install pymupdf or pdfplumber.'}


def format_output(analysis: dict) -> str:
    """Format analysis results for output."""

    if 'error' in analysis:
        return f"ERROR: {analysis['error']}"

    lines = []
    lines.append("=" * 60)
    lines.append("DOCUMENT STRUCTURE ANALYSIS")
    lines.append("=" * 60)
    lines.append(f"File: {analysis['filepath']}")
    lines.append(f"Format: {analysis['format']}")

    if 'total_pages' in analysis:
        lines.append(f"Total pages: {analysis['total_pages']}")
    if 'total_lines' in analysis:
        lines.append(f"Total lines: {analysis['total_lines']}")
        lines.append(f"Total words: {analysis['total_words']}")
        lines.append(f"Total chars: {analysis['total_chars']}")

    # TOC for PDFs
    if analysis.get('toc'):
        lines.append("")
        lines.append("-" * 40)
        lines.append("TABLE OF CONTENTS")
        lines.append("-" * 40)
        for level, title, page in analysis['toc'][:20]:
            indent = "  " * (level - 1)
            lines.append(f"{indent}{title} (page {page})")
        if len(analysis['toc']) > 20:
            lines.append(f"  ... and {len(analysis['toc']) - 20} more entries")

    # Headers for text files
    if analysis.get('headers'):
        lines.append("")
        lines.append("-" * 40)
        lines.append("DETECTED HEADERS")
        lines.append("-" * 40)
        for h in analysis['headers'][:20]:
            indent = "  " * (h['level'] - 1)
            lines.append(f"Line {h['line']:>5}: {indent}{h['text']}")
        if len(analysis['headers']) > 20:
            lines.append(f"  ... and {len(analysis['headers']) - 20} more headers")

    # Sections
    if analysis.get('sections'):
        lines.append("")
        lines.append("-" * 40)
        lines.append("SECTIONS")
        lines.append("-" * 40)
        for s in analysis['sections'][:15]:
            lines.append(f"Lines {s['start_line']:>5}-{s['end_line']:>5} ({s['line_count']:>4} lines): {s['name'][:50]}")
        if len(analysis['sections']) > 15:
            lines.append(f"  ... and {len(analysis['sections']) - 15} more sections")

    # Sampling strategy
    sp = analysis['sampling_points']
    lines.append("")
    lines.append("-" * 40)
    lines.append("RECOMMENDED SAMPLING STRATEGY")
    lines.append("-" * 40)

    unit = 'pages' if 'total_pages' in analysis else 'lines'

    lines.append(f"Beginning (10%): {unit} {sp['beginning'][0]}-{sp['beginning'][1]}")
    lines.append(f"25% mark: {unit} {sp['25_percent'][0]}-{sp['25_percent'][1]}")
    lines.append(f"50% mark: {unit} {sp['50_percent'][0]}-{sp['50_percent'][1]}")
    lines.append(f"75% mark: {unit} {sp['75_percent'][0]}-{sp['75_percent'][1]}")
    lines.append(f"End (10%): {unit} {sp['end'][0]}-{sp['end'][1]}")

    lines.append("")
    lines.append("6-Chunk division:")
    for i, chunk in enumerate(sp['chunks']):
        lines.append(f"  Chunk {i+1}: {unit} {chunk[0]}-{chunk[1]}")

    # Commands to use
    lines.append("")
    lines.append("-" * 40)
    lines.append("SUGGESTED COMMANDS")
    lines.append("-" * 40)

    if 'total_pages' in analysis:
        lines.append(f"# Beginning")
        lines.append(f"python pdf_extract.py {analysis['filepath']} --pages {sp['beginning'][0]}-{sp['beginning'][1]}")
        lines.append(f"# Middle sample")
        lines.append(f"python pdf_extract.py {analysis['filepath']} --pages {sp['50_percent'][0]}-{sp['50_percent'][1]}")
        lines.append(f"# End")
        lines.append(f"python pdf_extract.py {analysis['filepath']} --pages {sp['end'][0]}-{sp['end'][1]}")
    else:
        lines.append(f"# Beginning")
        lines.append(f"head -n {sp['beginning'][1]} {analysis['filepath']}")
        lines.append(f"# Middle sample")
        lines.append(f"sed -n '{sp['50_percent'][0]},{sp['50_percent'][1]}p' {analysis['filepath']}")
        lines.append(f"# End")
        lines.append(f"tail -n {sp['end'][1] - sp['end'][0]} {analysis['filepath']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze document structure for skimming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s document.txt
  %(prog)s document.md --format markdown
  %(prog)s document.pdf
        """
    )
    parser.add_argument('filepath', help='Path to document')
    parser.add_argument('--format', '-f', choices=['auto', 'markdown', 'latex', 'book', 'plain'],
                        default='auto', help='Document format hint (default: auto-detect)')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    filepath = Path(args.filepath)

    if not filepath.exists():
        print(f"ERROR: File not found: {args.filepath}", file=sys.stderr)
        sys.exit(1)

    # Analyze based on file type
    if filepath.suffix.lower() == '.pdf':
        analysis = analyze_pdf_structure(str(filepath))
    else:
        analysis = analyze_text_structure(str(filepath), args.format)

    if args.json:
        import json
        print(json.dumps(analysis, indent=2))
    else:
        print(format_output(analysis))


if __name__ == '__main__':
    main()
