# Special Cases by County and Year

This file grows as new patterns are discovered. Add a new section when you encounter
a pattern not covered by the standard rules in individuals.md or businesses.md.

---

## Grayson County, Texas — 1998 files

### FATHER as role label in family law cases → FILENAME_reviewCases.txt
In DIV (family law) modification cases, `FATHER,` appears as a placeholder for the
non-custodial parent when the actual name is unknown or not entered.
Treat identically to RESPONDENT/MOVANT — send whole case block to FILENAME_reviewCases.txt.
- `FATHER, ` (marker I) → weird (whole case block)
Seen in: MODIFICATION OF PRIOR ORDER, ALL OTHER FAMILY LAW MATTERS cases.

### Single-letter B record names (e.g. S AND D PROPERTIES, G AND F COMPANY) → leave as-is
B records where one part of an AND split would be a single letter cannot be reliably
split. Leave the full name as-is (B). This is handled by the B-4 flag rule.
- `S AND D PROPERTIES` → leave as-is (B)
- `G AND F COMPANY` → leave as-is (B)
- `C AND D PROPERTIES` → leave as-is (B)

### Alphanumeric ordinal B records (1ST STATE INC) → leave as-is
Business names starting with ordinal numbers (1ST, 2ND, etc.) are legitimate entities.
Leave as-is; the ordinal is part of the proper name.
- `1ST STATE INC` → leave as-is (B)

---

## Grayson County, Texas — 1988 files

### "GUARDIAN OF" / "AS GUARDIAN OF" / "GUARDIAN AD LITEM" → strip (I-3)
Legal role descriptors appended to a person's name. Strip the phrase,
keep only the real name.
- `SMITH, JOHN GUARDIAN OF` → `SMITH, JOHN`
- `JONES, MARY AS GUARDIAN OF` → `JONES, MARY`

### "AN ADULT" / "IN RE ADULT" legal descriptor → strip (I-3)
These phrases appear after a person's name as a legal descriptor.
They are not part of the name — remove them.
- `SMITH, JOHN AN ADULT` → `SMITH, JOHN`
- `JONES, MARY IN RE ADULT` → `JONES, MARY`

### NONE as party placeholder → FILENAME_reviewCases.txt
In ex-parte proceedings (name changes, title petitions), the opposing party field is
filled with `NONE,` to indicate no opposing party. Do NOT delete the row automatically —
send the entire case block to FILENAME_reviewCases.txt for manual review.
- `NONE, ` (marker I) → weird (whole case block)
Seen in: NAME CHANGE PETITION, REMOVE CLOUD FROM TITLE, SUIT ON TRUST cases.

### RESPONDENT / MOVANT / LIENHOLDER as role labels → FILENAME_reviewCases.txt
These are legal role labels, not real names. They are ambiguous (the real party name
may be missing entirely). Do NOT delete the row. Send the entire case block to
FILENAME_reviewCases.txt for manual review.
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

### Single surname with no first name → FILENAME_reviewCases.txt
When an I record has a last name with a trailing comma but no first name entered,
the record is ambiguous — it may be a data entry error or an unknown party.
Send the entire case block to `FILENAME_reviewCases.txt` for human review.
- `BINGO,` (marker I, no first name) → weird (whole case block)
- `SMITH, ` (trailing space, no first name) → weird (whole case block)

**Exceptions — NOT caught by this rule:**
- `, ` — bare comma with no surname (I-2 deletes it)
- `RESPONDENT, `, `MOVANT, `, `LIENHOLDER, ` — role labels, handled upstream

**Note:** this rule fires before I-3 so the trailing comma is still detectable.
It takes priority over the game-name and short-abbreviation checks — `BINGO,`
goes to weird (not B) because the comma signals a person-record entry with a
missing first name.

### Gambling / game names in I records → reclassify as B
Single-token I records (no comma) containing a known game or gambling name are reclassified to B:
- `BINGO` (no comma, standalone) → B: `BINGO`
Known names: `BINGO`, `POKER`, `LOTTO`, `LOTTERY`, `KENO`, `BLACKJACK`, `ROULETTE`,
`CHECKERS`, `CHESS`, `DOMINOES`, `MAHJONG`.

**Note:** `BINGO,` (with trailing comma) is caught by the single-surname-only rule above
and goes to weird instead of B.

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

### AND WIFE + legal suffix → FILENAME_reviewCases.txt
B records where "AND WIFE" is followed by legal-role text (IND AND, A-N-F, AS NEXT FRIEND,
AS ADM, etc.) or where AND WIFE appears alone at the end are too complex to parse
automatically. The **entire case block** is sent to `FILENAME_reviewCases.txt`.

**Trigger:** name contains `AND WIFE` (standalone phrase, case-insensitive) AND either:
- nothing follows AND WIFE (incomplete entry), OR
- the text after AND WIFE contains: `IND AND`, `A-N-F`, `AS NEXT FRIEND`, `AS ADM`,
  `AS ADMINISTRATOR`, or a trailing single letter `O`

**Examples that trigger:**
- `WINKLER CHARLES K AND WIFE CAROL WINKLER IND AND A-N-F O` → weird
- `DAVIS DON AND WIFE SUSIE DAVIS IND AND` → weird
- `SPARKS JOE E AND WIFE` → weird (bare AND WIFE, no name after)

**Examples that do NOT trigger (B-5 handles these normally):**
- `MILLS JAMES E AND WIFE LINDA D MILLS` → B-5 splits into two I records
- `MIDWIFE MEDICAL CENTER` → not triggered (WIFE is part of MIDWIFE, no AND before)

**Detection:** pre-scan fires before any I/B rule, same as currency pre-scan.
During `--merge`: auto-routed to `FILENAME_reviewCases.txt` without a corrections entry.

Seen in: Grayson County 1989 files (cases 890229, 890359, 891631).

---

## Grayson County, Texas — 1989 files

### "IND AND AS NEXT FRIEND OF/FOR" in B or I record → reviewCases.txt
These are legal role phrases attached to a person's name that were misclassified as
B records (or occasionally appear in I records). The real party identity is ambiguous —
the pipeline cannot determine whose "next friend" this is or whether JERRY/BILLY/etc.
is a first name, last name, or something else. Send the **entire case block** to
`FILENAME_reviewCases.txt`.

**Variants caught:**
- `IND AND AS NEXT FRIEND OF`
- `INDIVIDUALLY AND AS NEXT FRIEND OF`
- `IND AND AS NEXT FRIEND FOR`
- `INDIVIDUALLY AND AS NEXT FRIEND FOR`

**Examples that trigger:**
- `THOMAS NANCY IND AND AS NEXT FRIEND OF JERRY` (B) → weird (whole case block)
- `JONES MARY INDIVIDUALLY AND AS NEXT FRIEND OF BILLY` (B) → weird
- `SMITH JAMES IND AND AS NEXT FRIEND FOR SUE` (B) → weird

**Detection:** `NEXT_FRIEND_RE` regex fires in `apply_all_b_rules` (raises `FlagForReview`)
and in `apply_all_i_rules` (raises `AmbiguousCase`) before any split or transform logic.

**General reminder:** when reviewing a B record that has no recognizable business
indicator (INC, CO, CORP, LLC, BANK, ISD, etc.) AND contains a personal name followed
by legal role text — do NOT leave it as B. Send to weird immediately. When in doubt → weird.

Seen in: case 890842.

### Exact garbled/placeholder names → FILENAME_reviewCases.txt
These strings appear verbatim and cannot be parsed. Send entire case block
to reviewCases.txt. Match is exact (stripped), not partial.
- `TEXAS, SAVINGS OF`        → weird (garbled entity name)
- `DEFENDANT, NO`            → weird (legal role placeholder)
- `DEFENDANT, NONE`          → weird (legal role placeholder)
- `PLAINTIFF--, --DEFENDANT` → weird (malformed dual-role entry)

---

## All files — non-name content detection → FILENAME_reviewCases.txt

### Lines clearly not names → auto-routed to reviewCases (no review needed)
Cases where any I or B line's name field contains content that is obviously not a person
or business name are automatically sent to `FILENAME_reviewCases.txt` during `--merge`
without any entry in `corrections.json`.

Three detection signals (all conservative — if in doubt, do NOT flag):

**Signal 1 — Double dash (`--`) anywhere in the name field:**
- `PLAINTIFF-- --DEFENDANT AND THIRD PARTY` → weird
- `DEFENDANT--PLAINTIFF` → weird

**Signal 2 — Single standalone generic category word (entire field = one word):**
Only triggers when the ENTIRE name field is exactly one of these words. Does NOT trigger
if the word appears alongside any proper noun.
- `RESTAURANTS` → weird
- `FIREARMS` → weird (note: if also contains currency term, currency scan fires first)
- `RESTAURANTS GARCIA` → NOT flagged (has a proper noun)

**Signal 3 — Exact legal role phrase (entire field = role text, no name present):**
- `PLAINTIFF` → weird
- `DEFENDANT` → weird
- `THIRD PARTY` → weird
- `UNKNOWN PARTIES` → weird
- `ALL PERSONS` → weird
- `UNKNOWN HEIRS` → weird (standalone; the full THE UNKNOWN HEIRS OR DEVISEES OF…
  phrase is handled by I-9 and does not trigger this rule)

**What does NOT trigger:**
- `HULL DAVID AND ASSOCIATES` → valid business name (B-1)
- `CORROON AND BLACK` → valid law firm (B-1)
- `CABLE, POST-NEWSWEEK` → valid I record (hyphen in token, not double dash)
- `RESTAURANTS GARCIA` → has a proper noun after the generic word
- Any name with 2+ meaningful tokens that are not role labels

**Detection order:** fires after currency and AND WIFE pre-scans, before I/B rules.
During `--merge`: auto-routed to `FILENAME_reviewCases.txt` — no `corrections.json` entry required.

---

## All files — monetary / currency term records → FILENAME_reviewCases.txt

### Currency/monetary terms in name field → auto-routed to reviewCases (no review needed)
Cases where any I or B line's name field contains a standalone monetary token are
automatically sent to `FILENAME_reviewCases.txt` during `--merge` without any
entry in `corrections.json`. No human review step is required.

**Trigger tokens** (case-insensitive, standalone words only):
`DOLLARS`, `CENTS`, `CURRENCY`, `MONEY`, `CASH`, `FUNDS`,
`PROCEEDS`, `SEIZED`, `SEIZURE`, `SEIZE`

Multi-word phrases `US CURRENCY` and `UNITED STATES CURRENCY` are covered because
`CURRENCY` is already in the token list.

**Detection:** split the name field on non-alpha characters and check each token.
This ensures `DOLLARD` (a surname) and `CENTSMITH` (a surname) do NOT trigger.

**Examples that trigger:**
- `CENTS FIVE HUNDRED TWENTY-EIGHT DOLLARS AND SEVENTY` (I) → weird
- `ZIRCONIA IN US CURRENCY AND SIX CUBIC` (B) → weird
- `FIVE HUNDRED DOLLARS AND NO CENTS` (I) → weird
- `SEIZED CURRENCY` (B) → weird
- `CURRENCY, FIVE HUNDRED SEVENTY-TWO DOLLARS IN US` (I) → weird

**Examples that do NOT trigger:**
- `DOLLARD, JAMES` (DOLLARD is a surname, not the token DOLLARS)
- `CENTSMITH, MARY` (CENTSMITH is a surname, not the token CENTS)

**Pipeline behavior:**
- Pre-scan fires before I/B rules — no rule is applied to any line in the case
- Triggering line gets `>>>` in `flagged.txt`; flagged.json entry has reason
  `"contains monetary/currency terms — send to weird"`
- During `--merge`: all cases with that reason are automatically routed to
  `FILENAME_reviewCases.txt` — no `corrections.json` entry required

Seen in: Grayson County forfeiture cases, e.g. 17 cases in ChtxGrayson_1989.

---

## Adding new sections

When you encounter a new pattern, add it here with:
1. A short descriptive title
2. The county and year it applies to
3. One or two examples showing input → output
4. Any exceptions to watch for
