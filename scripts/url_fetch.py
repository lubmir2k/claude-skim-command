#!/usr/bin/env python3
"""
URL Content Fetcher for Document Skimming

Fetches web content with:
- Character limits
- HTML to text conversion
- Partial content fetching

Usage:
    python url_fetch.py https://example.com --info
    python url_fetch.py https://example.com --max-chars 5000
    python url_fetch.py https://example.com --start 1000 --max-chars 5000

Dependencies:
    pip install requests beautifulsoup4  # optional but recommended

Falls back to curl if requests not available.
"""

import argparse
import subprocess
import sys
import re
from html.parser import HTMLParser


class HTMLTextExtractor(HTMLParser):
    """Simple HTML to text converter."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'head', 'meta', 'link'}
        self.current_tag = None
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip_depth += 1
        self.current_tag = tag
        if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr'):
            self.text_parts.append('\n')

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip_depth > 0:
            self.skip_depth -= 1
        if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            self.text_parts.append('\n')

    def handle_data(self, data):
        if self.skip_depth == 0:
            self.text_parts.append(data)

    def get_text(self) -> str:
        text = ''.join(self.text_parts)
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()


def html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    # Try BeautifulSoup first
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'head', 'meta', 'link']):
            element.decompose()

        text = soup.get_text(separator='\n')
        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines()]
        text = '\n'.join(line for line in lines if line)
        return text
    except ImportError:
        pass

    # Fall back to simple HTML parser
    parser = HTMLTextExtractor()
    try:
        parser.feed(html)
        return parser.get_text()
    except Exception:
        # Last resort: strip tags with regex
        text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()


def fetch_with_requests(url: str, max_chars: int, start: int = 0) -> tuple[str, dict]:
    """Fetch URL using requests library."""
    try:
        import requests
    except ImportError:
        raise ImportError("requests not installed")

    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; DocumentSkimmer/1.0)'
    }

    # First, get headers to check content info
    head_response = requests.head(url, headers=headers, timeout=10, allow_redirects=True)

    info = {
        'url': head_response.url,
        'status': head_response.status_code,
        'content_type': head_response.headers.get('Content-Type', 'unknown'),
        'content_length': head_response.headers.get('Content-Length', 'unknown'),
    }

    # Fetch content
    response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)
    response.raise_for_status()

    content = response.text
    info['actual_length'] = len(content)

    # Convert HTML to text if needed
    content_type = response.headers.get('Content-Type', '')
    if 'html' in content_type.lower():
        content = html_to_text(content)
        info['converted'] = 'HTML to text'

    # Apply limits
    if start > 0:
        content = content[start:]
        info['start_offset'] = start

    if len(content) > max_chars:
        content = content[:max_chars] + "\n\n[OUTPUT TRUNCATED at {} chars]".format(max_chars)
        info['truncated'] = True

    return content, info


def fetch_with_curl(url: str, max_chars: int, start: int = 0) -> tuple[str, dict]:
    """Fetch URL using curl (fallback)."""
    info = {'url': url, 'method': 'curl'}

    try:
        result = subprocess.run(
            ['curl', '-sL', '-A', 'DocumentSkimmer/1.0', '--max-time', '30', url],
            capture_output=True,
            text=True,
            timeout=35
        )

        if result.returncode != 0:
            return f"ERROR: curl failed with code {result.returncode}", info

        content = result.stdout
        info['actual_length'] = len(content)

        # Check if HTML
        if '<html' in content.lower()[:1000]:
            content = html_to_text(content)
            info['converted'] = 'HTML to text'

        # Apply limits
        if start > 0:
            content = content[start:]
            info['start_offset'] = start

        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[OUTPUT TRUNCATED at {} chars]".format(max_chars)
            info['truncated'] = True

        return content, info

    except subprocess.TimeoutExpired:
        return "ERROR: Request timed out", info
    except FileNotFoundError:
        return "ERROR: curl not found", info


def main():
    parser = argparse.ArgumentParser(
        description='Fetch web content for document skimming',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://example.com --info
  %(prog)s https://example.com --max-chars 5000
  %(prog)s https://example.com --start 1000 --max-chars 5000
        """
    )
    parser.add_argument('url', help='URL to fetch')
    parser.add_argument('--info', '-i', action='store_true', help='Show URL info only (no content)')
    parser.add_argument('--max-chars', '-m', type=int, default=10000,
                        help='Maximum characters to output (default: 10000)')
    parser.add_argument('--start', '-s', type=int, default=0,
                        help='Start offset in characters (default: 0)')

    args = parser.parse_args()

    # Try requests first, fall back to curl
    try:
        content, info = fetch_with_requests(args.url, args.max_chars, args.start)
    except ImportError:
        content, info = fetch_with_curl(args.url, args.max_chars, args.start)
    except Exception as e:
        print(f"Warning: 'requests' failed ({e}), falling back to 'curl'.", file=sys.stderr)
        content, info = fetch_with_curl(args.url, args.max_chars, args.start)

    if args.info:
        print("URL Info:")
        for key, value in info.items():
            print(f"  {key}: {value}")
        print()
        print("Suggested sampling strategy:")
        length = info.get('actual_length') or info.get('content_length') or 'unknown'
        if isinstance(length, int) or (isinstance(length, str) and length.isdigit()):
            length = int(length)
            print(f"  Beginning: --start 0 --max-chars {length // 10}")
            print(f"  25% mark: --start {length // 4} --max-chars {length // 10}")
            print(f"  50% mark: --start {length // 2} --max-chars {length // 10}")
            print(f"  75% mark: --start {3 * length // 4} --max-chars {length // 10}")
            print(f"  End: --start {length - length // 10} --max-chars {length // 10}")
    else:
        # Print info header
        print("="*60)
        print("FETCH INFO")
        print("="*60)
        for key, value in info.items():
            print(f"  {key}: {value}")
        print("="*60)
        print()
        print(content)


if __name__ == '__main__':
    main()
