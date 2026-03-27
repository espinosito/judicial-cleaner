# Special Cases by County and Year

This file grows as new patterns are discovered. Add a new section when you encounter
a pattern not covered by the standard rules in individuals.md or businesses.md.

---

## Grayson County, Texas — 1988 files

### NONE as party placeholder → weirdCases.txt
In ex-parte proceedings (name changes, title petitions), the opposing party field is
filled with `NONE,` to indicate no opposing party. Do NOT delete the row automatically —
send the entire case block to weirdCases.txt for manual review.
- `NONE, ` (marker I) → weird (whole case block)
Seen in: NAME CHANGE PETITION, REMOVE CLOUD FROM TITLE, SUIT ON TRUST cases.

### RESPONDENT / MOVANT / LIENHOLDER as role labels → weirdCases.txt
These are legal role labels, not real names. They are ambiguous (the real party name
may be missing entirely). Do NOT delete the row. Send the entire case block to
weirdCases.txt for manual review.
- `RESPONDENT, ` (marker I) → weird (whole case block)
- `MOVANT, ` (marker I) → weird (whole case block)
- `LIENHOLDER, ` (marker I) → weird (whole case block)

### Incomplete name with no first name → delete row
When an I record has only a last name and an empty first name (e.g. `GOSNELL, `),
and a fuller entry for the same person exists elsewhere in the same case block,
the incomplete row is a data entry error — delete it.
- `GOSNELL, ` → delete (real entry: `GOSNELL, DORTHEA AS ADM OF SONNY` is present)

### HOSP as abbreviation for Hospital → delete row
`HOSP, ` (marker I) appearing in the same case as a B record for a hospital
is a junk duplicate of that B record. Delete the `HOSP,` row.
- `HOSP, ` → delete (real entry: `HOSPITAL MEDICAL PLAZA` present as B)

### Alphanumeric tokens in legitimate B names — reorder tokens then leave as-is
B records containing alphanumeric tokens that are clearly part of a proper name
(highway designations, ordinal numbers like 1ST, trade designators like FB-40)
should have their tokens reordered if needed, then left unchanged:
- `ALSTYNE 1ST SHERMAN BANK BRANCH 1ST NATL BANK VAN` → leave as-is (B)
- `SUCC IN INT 1ST NATL BANK SHER` → leave as-is (B)
- `VENTURE SHERMAN I-75 JOINT` → leave as-is (B, I-75 is a highway)
- `VENTURE TWO FB-40 JOINT` → leave as-is (B, FB-40 is a project designation)
- `HOMES A-1 MOBILE` → B: `A-1 HOMES MOBILE` (token reorder: trade qualifier first)

### WHOPPER-STOPPER → reclassify as B
Whopper Stopper is a fishing lure brand. When found as a single-token I record
in a tax case alongside other fishing-related entities (e.g. LURES, FLIPTAIL),
reclassify to B and drop the comma:
- `WHOPPER-STOPPER, ` (I) → B: `WHOPPER-STOPPER`

### ANITA-GREEN — name inversion with hyphen → I: GREEN, ANITA
`ANITA-GREEN, ` with empty first name, where ANITA is a known first name and
GREEN appears separately in the same case (GREEN, LINDA), is an inverted entry
with a hyphen used instead of space. Resolve via I-4 logic:
- `ANITA-GREEN, ` → I: `GREEN, ANITA`

### IND AND suffix
Records ending in `IND AND` are truncated individual defendants.
Do NOT split. Keep as B, the suffix indicates a second defendant that was cut off.
- `WILLIAMS DAVID IND AND` → leave as-is (B)
- `SHAW DAN JR IND AND AS ADM OF` → leave as-is (B)

### CHILD IN RE CHANGE OF NAME
Legal case text embedded in the name field.
Extract only the person's name before the legal text.
- `FRANKS BILLY RAY A CHILD IN RE CHANGE OF NAME III` → I: `FRANKS, BILLY RAY`

### Legal role text in B records
These B records contain legal text, not real business names. Leave as-is:
- `PAGE JODIE IND AND AS ADMINSTARTRIX OF`
- `THOMPSON KIM Y IND AND AS NEXT FRIEND OF`
- `WATSON TERRI IND AND AS NEXT FRIEND FOR`

### Known law firms (do not split on AND)
- `BRORSON LAHAIE CULLEN AND ADAMS`
- `MUNSON MUNSON PIERCE AND CARDWELL PC`
- `NALL PELLEY AND WYNNE`
- `NALL STAGNER AND PELLEY A PARTNERSHIP`

### Known person names that appear as B records
These were misclassified at source. Convert to I:
- `VANVORST MICHAEL J 8207424` → strip number → I: `VANVORST, MICHAEL J`

### Inverted first names specific to Grayson
First names known to appear before the comma (inverted format):
`CHERYL`, `CHARLES`, `JIMMY`, `JOHN`, `MARY`

Names that LOOK like first names but are actually surnames in this dataset:
`JASON`, `RYAN` — do NOT invert these.

### MC / MAC prefix split across comma
Occasionally a name is split incorrectly with MC or MAC before the comma:
- `MC, DADE WILLIE MAE` → I: `MCDADE, WILLIE MAE`
- `MAC, DONALD JAMES` → I: `MACDONALD, JAMES`

Rule: if the part before the comma is exactly `MC` or `MAC`, join it with the first
token after the comma to form the real last name. Apply before I-10.

### Business indicator placed before the comma in an I record
Some records were entered with a business/occupational word as the "last name":
- `MANUFACTURER, JOHN DOOR` → B: `JOHN DOOR MANUFACTURER`
- `CHURCH, OPEN DOOR DEL APOSTOLIC` → B: `OPEN DOOR DEL APOSTOLIC CHURCH`
- `CLUB, BANSHEE MOTORCYCLE` → B: `BANSHEE MOTORCYCLE CLUB`
- `YARD, EARL RATCLIFF WRECKING` → B: `EARL RATCLIFF WRECKING YARD`
- `COUNCIL, DENISON CITY` → B: `DENISON CITY COUNCIL`

Known trigger words: `MANUFACTURER`, `MANUFACTURERS`, `DISTRIBUTOR`, `DISTRIBUTORS`,
`CONTRACTOR`, `CONTRACTORS`, `SUPPLIER`, `SUPPLIERS`,
`CHURCH`, `CLUB`, `YARD`, `COUNCIL`.

Rule: reclassify to B and move the business word to the end.

### Business indicator placed after the comma in an I record
Some records have a business/occupational word after the comma that should come first:
- `CONSOLIDATION, MANUFACTURERS` → I: `MANUFACTURERS CONSOLIDATION`

Known trigger words: `MANUFACTURERS`, `DISTRIBUTORS`, `CONTRACTORS`, `SUPPLIERS`.

Rule: swap the two parts and keep marker as I (the word before the comma is the entity name).

### CITY OF — reversed order
Municipal entities appear with `CITY OF` at the end instead of the start:
- `VAN ALSTYNE CITY OF` → B: `CITY OF VAN ALSTYNE`

Rule: handled by B-3. Any record of the form `PLACE CITY OF` becomes `CITY OF PLACE`.

### COUNTY OF — reversed order
County governmental entities appear with `COUNTY OF` at the end instead of the start:
- `GRAYSON COUNTY OF` → B: `COUNTY OF GRAYSON`

Rule: handled by B-3. Any record of the form `PLACE COUNTY OF` becomes `COUNTY OF PLACE`.

### CAR / CARS at the start of a B record
Vehicle-related businesses sometimes have CAR or CARS at the start:
- `CARS QUALITY USED` → B: `QUALITY USED CARS`

Rule: handled by B-2. CAR and CARS are treated as prefixes and moved to the end.

### ASSOCIATES at the start of a B record
Some business records were entered with ASSOCIATES at the front:
- `ASSOCIATES DONALD L JARVIS AND` → B: `DONALD L JARVIS AND ASSOCIATES`

Rule: handled by B-2. ASSOCIATES is treated as a prefix and moved to the end.

### Names ending with a hard legal suffix — do not split on AND
A B record whose last token is `INC`, `LLC`, `LTD`, `LP`, `LLP`, `CORP`, or `CORPORATION`
is a single entity even if it contains AND:
- `LANGFORD AND MONTGOMERY SURVEY COMPANY INC` → leave as-is (B)

### Garbled / concatenated tokens — flag for review
Records where a split part would consist entirely of single-letter tokens,
or where a token appears to be multiple words concatenated (e.g. `ASSOCIIATESINC`):
- `C P AND ASSOCIIATESINC` → flagged

### Alphanumeric tokens in B records — flag for review
B records containing tokens that mix letters and digits (e.g. `A-1`, `B2`) cannot
be reliably processed and are sent to the flagged file:
- `HOMES A-1 MOBILE` → flagged
Exception: pure trailing numbers (ID/license codes) are stripped normally by B-8.

### Gambling / game names in I records → reclassify as B
Single-token I records containing a known game or gambling name are reclassified to B:
- `BINGO,` → B: `BINGO`
Known names: `BINGO`, `POKER`, `LOTTO`, `LOTTERY`, `KENO`, `BLACKJACK`, `ROULETTE`,
`CHECKERS`, `CHESS`, `DOMINOES`, `MAHJONG`.

### Short abbreviations in I records → reclassify as B
Single-token I records with ≤ 3 alphabetic characters that are not a known first name
are reclassified to B:
- `MCI,` → B: `MCI`

### Hyphenated compound words in I records → flag
Single-token I records containing a hyphen (other than MC-/MAC- prefixes) are flagged:
- `WHOPPER-STOPPER,` → flagged

### Hyphenated business word in "lastname" position → flag
When the part before the comma is hyphenated and one component is a known business word,
the record is ambiguous (could be a business entity or a person with a hyphenated surname).
It is flagged for review rather than auto-classified:
- `MOVERS-MILLER, HOUSE` → flagged (MOVERS indicates a possible moving company)

Legitimate hyphenated surnames (e.g. `SMITH-JONES, MARY`) pass through normally.

### Unknown single-token names in I records → flag
When the full pipeline runs with the name database loaded, any I record that reduces to
a single token not found in the first-name database is flagged for review:
- `LUCILLES,` → flagged (resolved as B: `LUCILLES` by reviewer)

### Maiden/birth surname appended at end of full name → hyphenated lastname
When a married woman's record includes her birth/maiden surname as the last word after
the comma, the pipeline detects and combines both surnames using a hyphen:
- `GARNER, DEBORAH MARGARET ROGERS` → I: `ROGERS-GARNER, DEBORAH MARGARET`

**Detection criteria (requires name database):**
- 3+ tokens after the comma
- Both the first AND second tokens are confirmed first names in the DB
- Last token is not a known suffix (JR, SR, etc.)

The last token is treated as the maiden surname regardless of whether it also appears
in the first-name database (e.g. ROGERS is occasionally used as a male given name but
here it is the birth surname).

### WIFE/HUSBAND pattern — single surname → B record
When a B record has the form `SURNAME AND WIFE FIRSTNAME` where the left side is a
single last name only, produce one B record instead of splitting into two I records:
- `HEROD AND WIFE STACYE` → B: `HEROD, STACYE`
This applies only when `person1` is a single token. For full names on the left (e.g.
`MILLS JAMES E AND WIFE LINDA D MILLS`), the standard B-5 split into two I records applies.

---

## Adding new sections

When you encounter a new pattern, add it here with:
1. A short descriptive title
2. The county and year it applies to
3. One or two examples showing input → output
4. Any exceptions to watch for
