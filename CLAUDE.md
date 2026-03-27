# Judicial Records Cleaner

## What this project does
Cleans judicial TSV records. Each file has 3,839+ lines of court records
with names that need standardization. Python handles ~99% automatically.
Your job is to fix edge cases, update rules, and improve the code.

## Project structure
```
src/
  parser.py      — reads TSV, groups lines by case_number
  classifier.py  — classifies names as I (person) / B (business) / AMBIGUOUS
  rules_i.py     — 10 rules for person records (I-1 to I-10)
  rules_b.py     — 8 rules for business records (B-1 to B-8)
  dedup.py       — deduplication per case block
  main.py        — orchestrator, entry point

rules/
  individuals.md       — all I rules explained
  businesses.md        — all B rules explained
  special_cases.md     — edge cases per county/year
  known_first_names.txt — first names not in SSA database

reference/
  names.zip            — SSA name database (100K+ names)
  nombres_es_*.csv     — Spanish names
  nombres_hispanic.csv — Hispanic names

data/input/            — drop raw files here
data/output/           — cleaned files appear here
data/flagged/          — JSON files with cases needing review

tests/
  test_rules.py        — 67 regression tests
```

## Field map (1-indexed, tab-separated)
```
Field 1  date         19881207
Field 2  case_number  883763
Field 3  court_type   JDG, DIV
Field 4  line_type    02, 04, 05
Field 5  marker       I, B, IB, or empty
Field 6  name         CORNWELL, LORENE
```

## Session start — always do this first
1. Run `python tests/test_rules.py` to confirm all 67 tests pass
2. Read `rules/individuals.md`
3. Read `rules/businesses.md`
4. Read `rules/special_cases.md`
Then say: "Ready. X/67 tests passing."

## How to process a file
```bash
python src/main.py data/input/FILENAME.txt
```
Produces:
- `data/output/FILENAME_clean.txt` — corrected file
- `data/flagged/FILENAME_flagged.json` — cases needing review (ideally 0)
- `data/flagged/FILENAME_flagged.txt` — same flagged cases as raw TSV blocks, one blank line between cases (only written when there are flagged cases)

## When resolving flagged cases
Use fast pattern matching only — do not over-analyze.
Decision logic:
  - Matches a known rule in rules/ → resolved, apply it
  - Does not match any rule → weird, no further analysis
  - Maximum 2 seconds of reasoning per case
If you are not immediately certain → mark as weird.

## Token efficiency when resolving flagged cases
- Process cases silently — do not quote or repeat the original data back
- For each case print only: case_number | action | corrected_name (one line)
- Do not explain reasoning unless the action is "weird"
- Do not confirm what you read — just process and output decisions

## How to resolve flagged cases
1. Read `data/flagged/FILENAME_flagged.json` — contains `header_line` + `flagged_line` per entry (no raw_block)
2. Read `data/flagged/FILENAME_flagged.txt` — full original TSV blocks, used to build corrected_block
3. Apply the rule from rules/ that fits best
4. If it's a new pattern not in rules/ — document it in `rules/special_cases.md`
5. Write corrections to `data/flagged/FILENAME_corrections.json`
   - For `resolved`: copy the full block from flagged.txt and apply corrections → `corrected_block`
   - For `weird`: no corrected_block needed (main.py reads flagged.txt on --merge)
6. **REQUIRED — do not skip:** Run `python src/main.py data/input/FILENAME.txt --merge`
   This appends resolved cases to the clean file and writes weird cases to weirdCases.txt.
   The task is NOT complete until this command runs and you confirm the output.

Corrections format — one entry per unique case_number:
```json
[
  {
    "case_number": "883763",
    "action": "resolved",
    "corrected_block": [
      "19881207\t883763    \tJDG\t02\tTAX CASES\t\t\n",
      "19881207\t883763    \tJDG\t04\tI\tCORNWELL, LORENE\t\n"
    ]
  },
  {
    "case_number": "881999",
    "action": "weird"
  }
]
```
Actions: `resolved` (corrected_block required) | `weird` (goes to weirdCases.txt)

Resolved cases are appended to the end of the clean file.
Weird cases go to data/flagged/weirdCases.txt for manual review.

## How to add a new rule to the code
When you find a pattern that repeats across multiple cases:
1. Add the logic to `src/rules_i.py` or `src/rules_b.py`
2. Add a test to `tests/test_rules.py`
3. Run `python tests/test_rules.py` — must still pass 67+ tests
4. Update `rules/individuals.md` or `rules/businesses.md` to document it
5. Run `python src/main.py data/input/FILENAME.txt` to verify improvement

## How to add a new first name
When a name is flagged only because it's not in the name database:
1. Add it to `rules/known_first_names.txt` (one per line, uppercase)
2. Re-run `python src/main.py` — it loads the file automatically

## Hard rules — never break these
- Only modify field 6 (name) and field 5 (marker) when a rule explicitly requires it
- Never correct spelling errors — BRRITTAIN stays BRRITTAIN
- Never assume when ambiguous — flag with a note instead
- Marker IB is always left exactly as-is
- Lines with fewer than 6 fields are left completely unchanged
- Never touch data/input/ files

## Running tests after any code change
```bash
python tests/test_rules.py
```
If any test fails, fix the code before touching the data.

## Token conservation (Pro plan)
- Print summaries only, not line-by-line corrections
- Use /compact if context grows large mid-session
- Process one file fully before starting the next

## After every code change
Before ending any session where you modified src/ files:
1. Update the corresponding rules/ markdown file
2. Run python tests/test_rules.py and confirm all pass
3. Report: X tests passing, Y files updated