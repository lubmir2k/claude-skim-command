# Claude Code `/skim` Command

A Claude Code slash command that enables AI to efficiently "skim" large documents using stratified sampling - reading only 20-30% while covering the full document length.

Based on the methodology from [this Medium article](https://medium.com/@airabbitX/i-taught-ai-to-skim-1000-page-documents-like-a-human-bce9fcc9f5c6) by airabbitX.

## What It Does

Instead of reading entire documents (which can exceed context limits and cost more tokens), this command teaches Claude to skim like humans do:

- **Stratified sampling**: Read beginning, 25%, 50%, 75%, end + periodic samples
- **Strict output limits**: 100 words per check, 2000 words total
- **Honest labeling**: Every finding marked as VERIFIED / SAMPLED / INFERRED / UNKNOWN
- **Coverage tracking**: Visual gap markers showing exactly what was/wasn't examined

## Supported Sources

- **PDF files** (requires `pymupdf` or `pdfplumber`)
- **Text files** (markdown, plain text, LaTeX, etc.)
- **URLs** (web pages converted to text)

## Installation

### Option 1: Claude Code Plugin (Recommended)

```bash
# Add the plugin marketplace
/plugin marketplace add lubmir2k/claude-skim-command

# Install the plugin
/plugin install skim@lubmir2k/claude-skim-command
```

After installing the plugin, run the install script to set up helper scripts:
```bash
# Navigate to the plugin directory and run install
cd ~/.claude/plugins/lubmir2k-claude-skim-command  # Path may vary; find with: find ~/.claude/plugins -name '*skim*' -type d
./install.sh
```

### Option 2: Direct Install via Script

```bash
# Download and inspect before running (recommended)
curl -fsSL -o install.sh https://raw.githubusercontent.com/lubmir2k/claude-skim-command/main/install.sh
less install.sh  # Review the script
bash install.sh

# Or one-liner (only if you trust the source)
curl -fsSL https://raw.githubusercontent.com/lubmir2k/claude-skim-command/main/install.sh | bash
```

### Option 3: Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/lubmir2k/claude-skim-command.git
   cd claude-skim-command
   ```

2. Run the install script:
   ```bash
   ./install.sh
   ```

Or manually copy the files:
```bash
mkdir -p ~/.claude/commands/skim-scripts
cp commands/skim.md ~/.claude/commands/
cp scripts/*.py ~/.claude/commands/skim-scripts/
chmod +x ~/.claude/commands/skim-scripts/*.py
```

### Optional Dependencies

For PDF support (highly recommended):
```bash
pip install pymupdf
# or
pip install pdfplumber
```

For better URL fetching:
```bash
pip install requests beautifulsoup4
```

The scripts fall back to basic tools (curl, simple HTML parsing) if these aren't installed.

## Usage

```bash
# Skim a local PDF
/skim ~/reports/annual-report-2024.pdf

# Skim a web page
/skim https://example.com/long-article

# Skim with focus area
/skim ~/docs/technical-spec.txt "focus on security requirements"

# Skim a remote PDF
/skim https://ntrs.nasa.gov/api/citations/19910015625/downloads/19910015625.pdf
```

## How It Works

### 1. Document Analysis
First, Claude analyzes the document structure:
- Total size (pages/lines/words)
- Headers and sections
- Optimal sampling points

### 2. Stratified Sampling
Claude reads strategically distributed samples:

| Position | What's Read | Example (174 pages) |
|----------|-------------|---------------------|
| Beginning | First 10% | Pages 1-17 |
| 25% mark | ~5 pages | Pages 44-48 |
| 50% mark | ~5 pages | Pages 87-91 |
| 75% mark | ~5 pages | Pages 131-135 |
| End | Last 10% | Pages 157-174 |
| Throughout | Every Nth | Every 15th page |

### 3. Honest Reporting
Every finding is labeled:
- **VERIFIED**: Direct quote with exact location
- **SAMPLED**: From representative section
- **INFERRED**: Pattern-based conclusion
- **UNKNOWN**: Section not examined

### 4. Coverage Map
Output includes a visual coverage map:
```
[EXAMINED] pages 1-17
[NOT READ] pages 18-43
[SAMPLED]  pages 44-48
[NOT READ] pages 49-86
...
```

## Helper Scripts

The command includes three utility scripts:

### `pdf_extract.py`
Extract text from PDF files with page range support.
```bash
python ~/.claude/commands/skim-scripts/pdf_extract.py document.pdf --info
python ~/.claude/commands/skim-scripts/pdf_extract.py document.pdf --pages 1-10,50-60
```

### `url_fetch.py`
Fetch web content with output limits.
```bash
python ~/.claude/commands/skim-scripts/url_fetch.py https://example.com --info
python ~/.claude/commands/skim-scripts/url_fetch.py https://example.com --max-chars 5000
```

### `doc_structure.py`
Analyze document structure and suggest sampling strategy.
```bash
python ~/.claude/commands/skim-scripts/doc_structure.py document.txt
python ~/.claude/commands/skim-scripts/doc_structure.py document.pdf
```

## Configuration

You can modify the sampling strategy by editing `~/.claude/commands/skim.md`:

- Adjust word limits (default: 100 per check, 2000 total)
- Change sampling percentages
- Add custom document format detection
- Modify output format

## Benefits

- **Cost reduction**: Process 20-30% of tokens vs 100%
- **Faster responses**: Less content to analyze
- **Better quality**: Focused on representative content
- **No infrastructure**: No RAG database or chunking required
- **Honest analysis**: Clear about what was/wasn't examined

## Limitations

- Cannot provide complete analysis (by design)
- PDF extraction quality depends on PDF structure
- Some complex layouts may not extract well
- Requires Python 3.8+ for helper scripts

## Uninstall

```bash
rm ~/.claude/commands/skim.md
rm -rf ~/.claude/commands/skim-scripts
```

## License

This is free and unencumbered software released into the public domain. See [UNLICENSE](UNLICENSE) for details.

## Credits

- Methodology based on [airabbitX's article](https://medium.com/@airabbitX/i-taught-ai-to-skim-1000-page-documents-like-a-human-bce9fcc9f5c6)
- Built for [Claude Code](https://claude.ai/code)
