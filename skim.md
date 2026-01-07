---
description: Skim large documents (PDFs, text, URLs) to extract key insights using stratified sampling - read 20-30% strategically
---

# Document Skimmer

Efficiently analyze large documents by reading only 20-30% strategically distributed across the full length, mimicking how humans skim.

## Arguments

$ARGUMENTS

Accepts: file path, URL, or document description. Optional focus area in quotes.

Examples:
- `/skim ~/reports/annual-report.pdf`
- `/skim https://example.com/long-article.html`
- `/skim ~/docs/spec.txt "focus on security section"`

## Helper Scripts

Located at `~/.claude/commands/skim-scripts/`:

```bash
# Extract text from PDF (specific pages)
python ~/.claude/commands/skim-scripts/pdf_extract.py document.pdf --pages 1-10,50-60

# Fetch URL content with limits
python ~/.claude/commands/skim-scripts/url_fetch.py https://example.com --max-chars 5000

# Analyze document structure
python ~/.claude/commands/skim-scripts/doc_structure.py document.txt
```

---

## STRICT CONSTRAINTS (Non-negotiable)

### Output Limits
- **Max 100 words per analysis check**
- **2000 words total for entire task**
- ONLY use bash utilities with built-in output limits: `head`, `tail`, `grep`, `sed`, `awk`, `wc`
- ALL commands MUST have explicit limits (e.g., `head -n 50`, `grep -m 10`)

### Before EVERY Tool Call, Verify:
1. Does this tool/command have output limitations?
2. If NO → DO NOT USE IT
3. If YES → Verify the limit is sufficient
4. If uncertain → Ask user for guidance

### Forbidden Actions
- Reading entire files without limits
- Web fetching without character limits
- Spawning unlimited agents
- Any tool without explicit output constraints
- Guessing or improvising when information is missing

### Compliance Rule
Breaking these rules = INVALID ANALYSIS. Stop immediately if constraints cannot be met.

---

## METHODOLOGY: Stratified Sampling

### Step 1: Detect Source Type

```bash
# Check if it's a URL or local file
if [[ "$ARGUMENTS" == http* ]]; then
    echo "SOURCE: URL"
else
    echo "SOURCE: Local file"
    ls -la -- "$ARGUMENTS"
fi
```

### Step 2: Get Document Size

For text files:
```bash
wc -l < document.txt
```

For PDFs (use helper script):
```bash
python ~/.claude/commands/skim-scripts/pdf_extract.py document.pdf --info
```

For URLs:
```bash
python ~/.claude/commands/skim-scripts/url_fetch.py URL --info
```

### Step 3: Map Document Structure

```bash
# Find headers/sections in text
grep -n "^#\|^Chapter\|^Section\|^[0-9]\+\." document.txt | head -50

# Or use helper
python ~/.claude/commands/skim-scripts/doc_structure.py document.txt
```

### Step 4: Divide Into 6 Chunks

For a document with N lines/pages:
- Chunk 1: Lines 1 to N/6
- Chunk 2: Lines N/6 to 2N/6
- Chunk 3: Lines 2N/6 to 3N/6
- Chunk 4: Lines 3N/6 to 4N/6
- Chunk 5: Lines 4N/6 to 5N/6
- Chunk 6: Lines 5N/6 to N

### Step 5: Stratified Sampling

Sample from EACH chunk proportionally:

| Position | What to Read | Example (174 pages) |
|----------|--------------|---------------------|
| Beginning | First 10% | Pages 1-17 |
| 25% mark | 5 pages | Pages 44-48 |
| 50% mark | 5 pages | Pages 87-91 |
| 75% mark | 5 pages | Pages 131-135 |
| End | Last 10% | Pages 157-174 |
| Throughout | Every Nth | Every 15th page |

**Commands for text files:**
```bash
# Beginning (first 100 lines)
head -n 100 document.txt

# 25% mark
sed -n '250,300p' document.txt

# 50% mark (middle)
sed -n '500,550p' document.txt

# 75% mark
sed -n '750,800p' document.txt

# End (last 100 lines)
tail -n 100 document.txt

# Every 50th line throughout
awk 'NR % 50 == 0' document.txt | head -50
```

**Commands for PDFs:**
```bash
python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 1-17
python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 44-48
python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 87-91
python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 131-135
python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 157-174
```

### Step 6: Track Coverage

After each sample, log:
```
[EXAMINED lines 1-100]
[NOT READ lines 101-249]
[SAMPLED lines 250-300]
[NOT READ lines 301-499]
[SAMPLED lines 500-550]
...
```

### Step 7: Generate Summary with Honest Gaps

---

## OUTPUT LABELING (Required)

Every finding MUST be labeled:

| Label | Meaning | Example |
|-------|---------|---------|
| **VERIFIED** | Direct quote with location | "VERIFIED (page 15): 'The system uses AES-256 encryption'" |
| **SAMPLED** | From representative section | "SAMPLED (pages 87-91): Security discussed in Chapter 5" |
| **INFERRED** | Pattern-based conclusion | "INFERRED: Document follows standard RFC format based on headers" |
| **UNKNOWN** | Section not examined | "UNKNOWN (pages 92-130): Content not sampled" |

---

## OUTPUT FORMAT

### After Every Analysis Step:

```
## [Section Name]

**Coverage:** X% of document (lines/pages A-B examined)

### Findings:
- VERIFIED (line X): [exact quote or fact]
- SAMPLED (lines Y-Z): [observation]
- INFERRED: [conclusion based on patterns]

### Gaps:
- [NOT READ lines A-B]
- [UNKNOWN: section C]

---
CONSTRAINT CHECK: Output used [X]/100 words. Status: COMPLIANT
```

### Final Summary Format:

```
# Document Skim Summary

**Source:** [filename or URL]
**Total Size:** [pages/lines/words]
**Coverage:** [X]% read ([specific ranges])

## Key Findings

### VERIFIED (directly observed):
1. [Finding with page/line reference]
2. [Finding with page/line reference]

### SAMPLED (representative sections):
1. [Observation from sample]
2. [Observation from sample]

### INFERRED (pattern-based):
1. [Inference with basis]

## Coverage Map

```
[EXAMINED] pages 1-17
[NOT READ] pages 18-43
[SAMPLED]  pages 44-48
[NOT READ] pages 49-86
[SAMPLED]  pages 87-91
[NOT READ] pages 92-130
[SAMPLED]  pages 131-135
[NOT READ] pages 136-156
[EXAMINED] pages 157-174
```

## Limitations

- Sections [X-Y] were not examined
- Cannot confirm [specific detail] without reading pages [A-B]
- [Any other honest gaps]

---
FINAL CONSTRAINT CHECK: Total output [X]/2000 words. Status: COMPLIANT
```

---

## ANTI-CHEATING RULES

1. **DEFINE SCOPE EXPLICITLY** - State exactly what percentage you will read
2. **NO GAPS LARGER THAN 30 PAGES** - Sample from every major section
3. **NEVER EXTRAPOLATE BEYOND DATA** - Say "unknown" instead of guessing
4. **IF ASKED FOR FULL ANALYSIS, SAY NO** - Explain that full analysis requires reading all content
5. **SHOW YOUR WORK** - Log every command executed and its output
6. **DISTINGUISH FACT FROM GUESS** - Never mix without explicit labels

---

## Quick Reference

| Task | Command |
|------|---------|
| PDF page count | `python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --info` |
| PDF text extract | `python ~/.claude/commands/skim-scripts/pdf_extract.py doc.pdf --pages 1-10` |
| Text file size | `wc -l < file.txt` |
| First N lines | `head -n N file.txt` |
| Last N lines | `tail -n N file.txt` |
| Lines X to Y | `sed -n 'X,Yp' file.txt` |
| Every Nth line | `awk 'NR % N == 0' file.txt \| head -50` |
| Find headers | `grep -n "^#" file.txt \| head -30` |
| URL fetch | `python ~/.claude/commands/skim-scripts/url_fetch.py URL --max-chars 5000` |
