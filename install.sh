#!/usr/bin/env bash
#
# Install script for Claude Code /skim command
#
# Usage:
#   ./install.sh
#   curl -fsSL https://raw.githubusercontent.com/lubmir2k/claude-skim-command/main/install.sh | bash
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize variables
TEMP_INSTALL=false
SCRIPT_DIR=""

# Ensure cleanup of temporary files on exit
cleanup() {
    if [ "$TEMP_INSTALL" = true ] && [ -n "$SCRIPT_DIR" ] && [ -d "$SCRIPT_DIR" ]; then
        rm -rf "$SCRIPT_DIR"
    fi
}
trap cleanup EXIT

echo -e "${GREEN}Installing Claude Code /skim command...${NC}"

# Determine script directory (works for both local and piped execution)
if [ -n "$BASH_SOURCE" ] && [ -f "$BASH_SOURCE" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    # Running from curl pipe - need to download files
    SCRIPT_DIR=$(mktemp -d)
    TEMP_INSTALL=true

    echo "Downloading files..."
    REPO_URL="https://raw.githubusercontent.com/lubmir2k/claude-skim-command/main"

    curl -fsSL "$REPO_URL/skim.md" -o "$SCRIPT_DIR/skim.md"
    mkdir -p "$SCRIPT_DIR/scripts"
    curl -fsSL "$REPO_URL/scripts/pdf_extract.py" -o "$SCRIPT_DIR/scripts/pdf_extract.py"
    curl -fsSL "$REPO_URL/scripts/url_fetch.py" -o "$SCRIPT_DIR/scripts/url_fetch.py"
    curl -fsSL "$REPO_URL/scripts/doc_structure.py" -o "$SCRIPT_DIR/scripts/doc_structure.py"
fi

# Target directories
COMMANDS_DIR="$HOME/.claude/commands"
SCRIPTS_DIR="$COMMANDS_DIR/skim-scripts"

# Create directories
echo "Creating directories..."
mkdir -p "$COMMANDS_DIR"
mkdir -p "$SCRIPTS_DIR"

# Copy files
echo "Copying files..."
cp "$SCRIPT_DIR/skim.md" "$COMMANDS_DIR/"
cp "$SCRIPT_DIR/scripts/pdf_extract.py" "$SCRIPTS_DIR/"
cp "$SCRIPT_DIR/scripts/url_fetch.py" "$SCRIPTS_DIR/"
cp "$SCRIPT_DIR/scripts/doc_structure.py" "$SCRIPTS_DIR/"

# Make scripts executable
echo "Setting permissions..."
chmod +x "$SCRIPTS_DIR"/*.py

# Verify installation
echo ""
echo -e "${GREEN}Installation complete!${NC}"
echo ""
echo "Installed files:"
echo "  $COMMANDS_DIR/skim.md"
echo "  $SCRIPTS_DIR/pdf_extract.py"
echo "  $SCRIPTS_DIR/url_fetch.py"
echo "  $SCRIPTS_DIR/doc_structure.py"
echo ""

# Check for optional dependencies
echo "Checking optional dependencies..."

if python3 -c "import fitz" 2>/dev/null || python3 -c "import pdfplumber" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} PDF support available"
else
    echo -e "  ${YELLOW}!${NC} PDF support not installed (optional)"
    echo "    Install with: pip install pymupdf"
fi

if python3 -c "import requests" 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} requests library available"
else
    echo -e "  ${YELLOW}!${NC} requests not installed (optional)"
    echo "    Install with: pip install requests beautifulsoup4"
fi

echo ""
echo -e "${GREEN}Usage:${NC}"
echo "  /skim ~/documents/large-report.pdf"
echo "  /skim https://example.com/article"
echo "  /skim ~/docs/spec.txt \"focus on security\""
echo ""
