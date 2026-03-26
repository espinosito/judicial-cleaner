# Judicial Records Cleaner — Implementation Plan

## Overview

This document describes the complete architecture and step-by-step implementation plan for automating the cleaning of judicial TSV records. The system is designed so that **Python handles ~95% of cases automatically** and **Claude Code only sees the ambiguous 5%**, minimizing token usage while maintaining accuracy.

---

## Document History
- v1.0 — Initial plan and architecture
- v1.1 — Added name classification logic, tools inventory, token capacity analysis

---

## Core Principle

> Every rule that can be expressed as code should be code. Claude is expensive and slow at scale — Python is free and instant. Claude's job is to handle what Python genuinely cannot decide.

---

## What You Need Installed

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.10+ | Run the processing scripts |
| Claude Code | latest | CLI for reviewing ambiguous cases |
| Git | any | Version control for rules and scripts |

No other dependencies. The entire system uses Python's standard library — no pip installs required.

---

## Project Structure

```
judicial-cleaner/
│
├── CLAUDE.md                     ← Claude Code reads this on every session
│
├── .claude/
│   ├── commands/
│   │   ├── analyze.md            ← /analyze — pre-scan a file for anomalies
│   │   ├── resolve.md            ← /resolve — fix flagged ambiguous cases
│   │   └── validate.md           ← /validate — spot check output quality
│   └── settings.json             ← tool permissions
│
├── rules/                        ← human-readable rule documentation
│   ├── individuals.md            ← I-1 through I-10
│   ├── businesses.md             ← B-1 through B-8
│   └── special_cases.md          ← edge cases per county/year
│
├── src/                          ← all processing code
│   ├── parser.py                 ← read TSV, group lines by cause_number
│   ├── rules_i.py                ← individual name rules (deterministic)
│   ├── rules_b.py                ← business name rules (deterministic)
│   ├── dedup.py                  ← deduplication per block
│   ├── ambiguity.py              ← detect cases that need Claude review
│   └── main.py                   ← CLI orchestrator (entry point)
│
├── data/
│   ├── input/                    ← drop raw files here
│   ├── output/                   ← cleaned files appear here
│   └── flagged/                  ← JSON files with ambiguous cases
│
└── tests/
    └── test_rules.py             ← unit tests using examples from prompt
```

---

## The Two-Pass Workflow

Every file goes through two passes:

### Pass 1 — Automatic (Python, zero tokens)

```
input file → parser → [expediente groups] → rules engine → output + flagged.json
```

The rules engine applies every deterministic rule in sequence:
1. Parse each line into fields
2. Skip lines with markers: `IB`, `02`, empty, numeric
3. For `I` records: apply I-1 through I-10 in order
4. For `B` records: apply B-1 through B-8 in order
5. Deduplicate within each cause_number block
6. Any line the engine cannot confidently resolve → write to `flagged.json`

### Pass 2 — Claude Code (only for flagged cases)

```
flagged.json → /resolve → corrections.json → merge → final output
```

Claude Code reads `flagged.json` and the full `rules/` folder, then resolves each case. The corrections are merged back into the output.

---

## Step-by-Step Implementation

### Step 1 — Create the project skeleton

Create the directory structure above. Initialize git. This takes 5 minutes.

### Step 2 — Write `parser.py`

This module:
- Reads the TSV file line by line
- Splits each line into exactly 6 fields (tab-separated, padding stripped)
- Groups lines by `cause_number` (field 2)
- Returns a list of `Case` objects, each containing all their lines

**Key constraint**: never split a case across chunks. A `Case` is always complete.

### Step 3 — Write `rules_i.py` — Individual name rules

Implement each rule as a standalone function:

- `apply_i1(name)` → normalize suffix placement (JR, SR, II, III, IV)
- `apply_i2(name)` → return `None` if name is empty, `,`, `, ` — caller deletes the row
- `apply_i3(name)` → strip legal fragments: `IN REM`, `DECEASED`, `TRUSTEE`, `LIENHOLDER`
- `apply_i4(name, known_first_names)` → detect and fix inverted names using the known list
- `apply_i5(name)` → parse `THE, OR ...` pattern and reformat
- `apply_i6(name)` → parse `THE-lastname, OR INITIALS` pattern
- `apply_i7(name)` → parse `FOR, ...` pattern
- `apply_i8(name)` → extract name from `THE ESTATE OF ...` / `THE ESTAET OF ...`
- `apply_i9(name)` → extract name from `THE UNKNOWN HEIRS OR DEVISEES...`
- `apply_i10(name)` → handle no-comma names: first token = last name

Each function returns either the corrected name string, `None` (delete row), or raises `AmbiguousCase` if it cannot decide.

### Step 4 — Write `rules_b.py` — Business name rules

- `apply_b1(name)` → default: return unchanged (most B records)
- `apply_b2(name)` → detect business prefix at start, move to end
- `apply_b3(name)` → detect reversed geographic/institutional names
- `apply_b4(name)` → split on `AND` into two B records (when both sides are businesses)
- `apply_b5(name)` → split on `AND` into two I records (when both sides are people)
- `apply_b6(name)` → handle `N K A` (now known as) splits
- `apply_b7(name)` → after split, reclassify as I or B based on business indicator list
- `apply_b8(name)` → detect person incorrectly classified as B, convert to I

**The business indicator list** from the prompt (INC, LLC, ISD, BANK, etc.) lives in a `BUSINESS_INDICATORS` constant in this file — easy to update without touching logic.

### Step 5 — Write `ambiguity.py`

This module defines what "ambiguous" means. A case is flagged when:

1. **I-4 trigger**: a name has no comma AND the first token is not in `KNOWN_FIRST_NAMES` — Python cannot safely invert it
2. **B-4/B-5 trigger**: a B record has `AND` but neither side clearly matches the business indicator list
3. **B-8 trigger**: a B record has no business indicators but also doesn't look like a clean `FIRST LAST` pattern
4. **Unknown pattern**: a name starts with an unrecognized legal prefix not covered by I-5 through I-9
5. **Split ambiguity**: after splitting on AND, one side could be either I or B

Everything else → Python decides with confidence.

### Step 6 — Write `dedup.py`

Simple logic:
- Within each cause_number block, track seen names
- On duplicate: keep first, remove second
- **Exception**: two records that differ only by `JR`/`SR` suffix are NOT duplicates — keep both

### Step 7 — Write `main.py` — the orchestrator

Command: `python src/main.py data/input/FILENAME.txt`

Flow:
1. Call parser → get list of cases
2. Pre-analysis: scan all unique I and B names, build per-file dictionaries
3. For each case: run rules engine, collect output lines and flagged items
4. Write cleaned lines to `data/output/FILENAME_clean.txt`
5. Write flagged cases to `data/flagged/FILENAME_flagged.json`
6. Print summary: total lines in / out / flagged

### Step 8 — Write `CLAUDE.md`

This file is what Claude Code reads at the start of every session. It should be short and precise:

```markdown
# Judicial Records Cleaner

## Your role
You resolve ambiguous cases that the Python engine could not decide automatically.
The engine handles ~95% of records. You only see the rest.

## Before doing anything
Read these files in order:
1. rules/individuals.md
2. rules/businesses.md  
3. rules/special_cases.md

## Your only task per session
When asked to /resolve: read data/flagged/FILENAME_flagged.json,
apply the rules, and write corrections to data/flagged/FILENAME_corrections.json.

Format: [{"line_id": "...", "action": "keep|delete|replace", "corrected": "..."}]

## What you must never do
- Touch any field other than NAME (field 6)
- Change markers on records that were not modified by a rule
- Correct spelling errors in names (BRRITTAIN stays BRRITTAIN)
- Assume an ambiguous name — if genuinely unclear, flag it again with a note
```

### Step 9 — Write `.claude/commands/`

Three slash commands:

**`/analyze`** — Pre-scan before processing. Claude reads the raw file, identifies patterns not in `special_cases.md`, and suggests additions before the engine runs.

**`/resolve`** — Main task. Reads `flagged.json`, applies rules, writes `corrections.json`.

**`/validate`** — Post-processing spot check. Claude reads 20 random corrected records from output and verifies they match expected format.

### Step 10 — Write `tests/test_rules.py`

Use the examples directly from the prompt as test cases:

```python
assert apply_i3("SMITH, IN REM ONLY HARRY") == "SMITH, HARRY"
assert apply_i5("THE, OR DALE GOUGE R") == "GOUGE, DALE R"
assert apply_i5("THE, OR TROY EDWARD MARDIS") == "MARDIS, TROY EDWARD"
assert apply_i8("THE ESTATE OF JIMMY LEE EARLY JR") == "EARLY, JIMMY LEE JR"
```

Run tests after every rule change. This is your regression safety net.

---

## Training Strategy — Small Samples First

Do NOT run the engine on a 5,000-line file until each rule is tested individually.

### Iteration 1 — 10 lines, manual verification
Pick 2-3 expedientes with known corrections. Run only `rules_i.py`. Compare output manually.

### Iteration 2 — 50 lines, B rules
Add 10 expedientes with B records including AND splits and prefix inversions. Verify.

### Iteration 3 — Full sample file (current `ChtxGrayson_1988.txt`)
Run the complete engine. Check `flagged.json` — it should contain only genuinely ambiguous cases.

### Iteration 4 — Production
Run on full-size files with confidence.

---

## Token Budget (Why This Works)

| Stage | Token cost | What happens |
|-------|-----------|-------------|
| Python rules engine | 0 | Handles deterministic cases |
| Claude `/analyze` | ~500–1,000 | One-time pre-scan per file |
| Claude `/resolve` | ~100–300 per flagged case | Only for genuinely ambiguous |
| Claude `/validate` | ~500 | Spot check 20 records |

For a 5,000-line file with ~1,500 expedientes, if 5% are flagged = 75 cases for Claude. At ~200 tokens each = ~15,000 tokens total. Compare to sending the whole file to Claude: ~50,000+ tokens, every time.

---

---

## Name Classification Logic (Person vs Business)

The classifier works in 4 layers. Each layer catches what it can with high confidence. Only cases that fall through all 4 layers are sent to Claude.

### Layer 1 — Hard business suffixes (highest confidence)
If the name ends with or contains: `INC`, `LLC`, `LTD`, `LP`, `PC`, `CORP`, `NA`, `FSB`, `LLP`
→ **B confirmed**, no further analysis needed.

### Layer 2 — Personal markers
If the name ends with: `JR`, `SR`, `II`, `III`, `IV`, `MD`, `PA`
→ **I confirmed**, no further analysis needed.

Structural check: if the name has a comma and a single token before it that is not in BUSINESS_INDICATORS → **I likely**.

### Layer 3 — Keyword density score
Count how many tokens from the name match the BUSINESS_INDICATORS list (350+ terms from the master prompt).

- Score ≥ 2 → **B with high confidence**
- Score = 0 and has comma → **I with high confidence**
- Score = 1 → **ambiguous → flag for Claude**

### Layer 4 — Claude (only for score=1 cases)
Claude receives the full expediente (all lines for that cause_number) plus the rules/ folder. This ensures full context for edge cases like `HOSPITAL WILSON N JONES MEMORIAL` (is score=1: "MEMORIAL" matches but "HOSPITAL" alone might not).

In practice on Grayson 1988 data: Layers 1–3 resolve ~97% of cases. Claude sees only ~3%.

### Implementation

```python
HARD_SUFFIXES = {"INC", "LLC", "LTD", "LP", "PC", "CORP", "NA", "FSB", "LLP"}
PERSONAL_SUFFIXES = {"JR", "SR", "II", "III", "IV", "MD", "PA"}

def classify_name(name: str) -> tuple[str, str]:
    tokens = name.upper().replace(",", " ").split()

    if any(t in HARD_SUFFIXES for t in tokens):
        return "B", "high"
    if tokens and tokens[-1] in PERSONAL_SUFFIXES:
        return "I", "high"
    if "," in name:
        before = name.split(",")[0].strip()
        if len(before.split()) == 1 and before not in BUSINESS_INDICATORS:
            return "I", "high"
    score = sum(1 for ind in BUSINESS_INDICATORS if ind.upper() in name.upper())
    if score >= 2:
        return "B", "high"
    if score == 0 and "," in name:
        return "I", "high"
    return "AMBIGUOUS", "low"  # → send to Claude
```

---

## Available Tools and Their Relevance

### Native environment tools

| Tool | What it does | Relevance |
|------|-------------|-----------|
| `bash_tool` | Run Python/bash directly on Ubuntu 24 | ★★★ Core — run the entire pipeline here |
| `create_file` | Create files in the container | ★★★ Generate all scripts |
| `str_replace` | Edit existing files | ★★ Iterate on rules |
| `present_files` | Deliver downloadable files to user | ★★★ Deliver finished scripts |
| `web_search` + `web_fetch` | Search and read web pages | ★ Research edge cases |
| `visualize:show_widget` | Render SVG/HTML inline | ★★ Flow diagrams and QA dashboards |

### Public skills (specialized instruction sets)

| Skill | Relevance |
|-------|-----------|
| `docx` | ★★ Document rules in Word for non-technical reviewers |
| `xlsx` | ★★★ Generate QA reports with original/corrected columns side by side |
| `pdf` / `pdf-reading` | ★ If source files arrive as PDF |
| `file-reading` | ★★ Direct TSV reading without bash |
| `frontend-design` | ★★ Web UI for reviewing flagged cases |

### Example skills (advanced)

| Skill | Relevance |
|-------|-----------|
| `mcp-builder` | ★★★ Build a custom MCP server giving Claude Code native transformation tools |
| `skill-creator` | ★★★ Package all rules as a reusable skill for future county files |
| `web-artifacts-builder` | ★★ Interactive web app for case review |

### What is NOT available here
- No native agent teams (available via API multi-agent workflows, not claude.ai)

### Recommended tool combination
For this project: `bash_tool` + `create_file` (build and test the pipeline) + `xlsx` (QA reports). 
Next level: `mcp-builder` to give Claude Code native tools instead of relying on file-based communication.

---

## Token Capacity Analysis

### Fixed costs per session
- Rules (prompt content): ~6,500 tokens
- Conversation + system overhead: ~2,000 tokens
- **Available for data: ~191,500 tokens** (within 200K context window)

### Approach A — Direct (entire file to Claude)
Each line costs ~18 tokens input + ~18 tokens output = 36 tokens/line.
- **Max per session: ~5,300 lines**
- **Weekly (Pro, ~21 sessions): ~111,000 lines**

This is why the free version ran out of capacity on large files.

### Approach B — Python + Claude (only flagged ~5%)
- Python handles 95% of lines for free (0 tokens)
- Each flagged case (~5 lines): ~90 tokens input + 60 output = 150 tokens
- Cost per 1,000 input lines: ~7,500 tokens (50 cases × 150)
- **Max per session: ~25,500 lines (5× improvement over Approach A)**
- **Weekly (Pro, ~21 sessions): ~535,000 lines**

### File size feasibility

| File size | Approach A (direct) | Approach B (Python+Claude) |
|-----------|--------------------|-----------------------------|
| 5,000 lines | 1 session | trivial |
| 10,000 lines | 2 sessions | 1 session |
| 50,000 lines | ~10 sessions | 2 sessions |
| 100,000 lines | ~19 sessions | 4 sessions |
| 500,000 lines | ~94 sessions (weeks) | ~20 sessions (~1 week) |

### Plan limits reference
- Context window: 200K tokens (all paid plans), 500K (Enterprise)
- Pro: ~45 messages per 5-hour rolling window
- Limits reset continuously, not at fixed times
- All surfaces (claude.ai, Claude Code, Claude Desktop) share the same pool

---

## Files That Need Updating Over Time

| File | When to update | Why |
|------|---------------|-----|
| `rules/special_cases.md` | Every new county/year | New edge cases |
| `rules_i.py` → `KNOWN_FIRST_NAMES` | When I-4 flags new names repeatedly | Shrinks ambiguous queue |
| `rules_b.py` → `BUSINESS_INDICATORS` | When new business types appear | Improves B-7/B-8 detection |
| `tests/test_rules.py` | Every time a new case is resolved | Prevent regressions |

The rules stay in Python. Claude Code's job stays narrow. The system improves over time without growing more expensive.
