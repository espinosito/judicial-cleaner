# Rules for I (Individual / Person) Records

Field being corrected: **field 6 (NAME)** only.
Correct format always: `LASTNAME, NAME [MIDDLE] [SUFFIX]`

---

## I-1 — Suffix placement
Suffixes `JR`, `SR`, `II`, `III`, `IV` go at the END with no comma before them.
- `CHAMBERS, GARY MADOX, JR` → `CHAMBERS, GARY MADOX JR`

## I-2 — Delete junk rows
Delete the entire row (not the case) only when the name is provably empty:
- Just a comma: `,` or `, `
- Empty string

**Do NOT delete** role labels or legal text (MOVANT, LIENHOLDER, RESPONDENT,
FOR MOTHER- ATTY GEN, single letter N, etc.). These are ambiguous — the entire
case block must go to weirdCases.txt for manual review instead.

## I-3 — Strip legal fragments
Remove these fragments, keep only the real name:
- `IN REM ONLY`, `IN REM`
- `LIENHOLDER IN REM ONLY`, `LIENHOLDER`
- `DECEASED`
- `TRUSTEE`
- `INDIVIDUALLY`
- `AS ADM OF [NAME]` (administrator of an estate — strip entire phrase)

Examples:
- `SMITH, IN REM ONLY HARRY` → `SMITH, HARRY`
- `RAY, LIENHOLDER IN REM ONLY JOE DEE` → `RAY, JOE DEE`
- `HOOGENDOORN, LARRY TRUSTEE W` → `HOOGENDOORN, LARRY W`
- `WHITE, MICHELLE MARIE INDIVIDUALLY` → `WHITE, MICHELLE MARIE`

## I-4 — Inverted names (NAME, LASTNAME → LASTNAME, NAME)
Only applies when the token before the comma is a known first name.

Known inverted first names for Grayson files: `CHERYL`, `CHARLES`, `JIMMY`, `JOHN`, `MARY`

Logic by structure after the comma:
- `CHERYL, WOODALL` → `WOODALL, CHERYL`
- `JOHN, STOVER A` → `STOVER, JOHN A` (last token is initial)
- `JIMMY, LEE EARLY` → `EARLY, JIMMY LEE` (last token is surname)
- `JOHN, DAVID BARNES` → `BARNES, JOHN DAVID` (last token is surname)

**Important:** `JASON`, `RYAN` appear as surnames in this dataset — do NOT invert them.

## I-5 — THE, OR pattern
Format: `THE, OR NAME LASTNAME [INITIAL]`

Logic:
- If last token is a single letter and 3+ words total → it is an initial
- Otherwise last token is the surname

Examples:
- `THE, OR DALE GOUGE R` → `GOUGE, DALE R`
- `THE, OR NANNETT SHIREY` → `SHIREY, NANNETT`
- `THE, OR TROY EDWARD MARDIS` → `MARDIS, TROY EDWARD`
- `THE, OR DELBERT NEJMANOWSKI D` → `NEJMANOWSKI, DELBERT D`

## I-6 — THE-LASTNAME, OR pattern
Format: `THE-LASTNAME, OR INITIALS`

- `THE-ROBERTS, OR JA` → `ROBERTS, JA`
- `THE-ROBERTS, OR KJ` → `ROBERTS, KJ`

## I-7 — FOR, pattern
Format: `FOR, NAME LASTNAME [INITIAL]`
Same logic as I-5.

- `FOR, ELZIE TAYLOR A` → `TAYLOR, ELZIE A`

**Exception:** `FOR, MOTHER- ATTY GEN` → delete row (I-2 applies first)

## I-8 — THE ESTATE OF / THE ESTAET OF
Extract the deceased person's name. The typo `ESTAET` is treated identically.

- `THE ESTATE OF JIMMY LEE EARLY JR` → `EARLY, JIMMY LEE JR`
- `THE ESTAET OF JIMMY LEE EARLY JR` → `EARLY, JIMMY LEE JR`

## I-9 — THE UNKNOWN HEIRS OR DEVISEES...
Extract only the person's name:

- `THE UNKNOWN HEIRS OR DEVISEES OF THE ESTATE OF JIMMY LEE EARLY, DECEASED` → `EARLY, JIMMY LEE`

## I-10 — No comma (fallback)
If name has no comma and no other pattern matched, assume first token is surname:

- `WRIGHT JENNIFER` → `WRIGHT, JENNIFER`

---

## I-MC — MC / MAC prefix joined with surname
When the part before the comma is exactly `MC` or `MAC`, it is a prefix that was split
from the surname. Join it with the first token after the comma.

- `MC, DADE WILLIE MAE` → `MCDADE, WILLIE MAE`
- `MAC, DONALD JAMES` → `MACDONALD, JAMES`

Applied after I-3 and before I-6.

## I-BC — Business indicator before comma → reclassify as B
When the token before the comma is a known business/occupational word, the record was
misclassified as I. Reclassify marker to B and move the business word to the end.

Trigger words: `MANUFACTURER`, `MANUFACTURERS`, `DISTRIBUTOR`, `DISTRIBUTORS`,
`CONTRACTOR`, `CONTRACTORS`, `SUPPLIER`, `SUPPLIERS`,
`CHURCH`, `CLUB`, `YARD`, `COUNCIL`.

- `MANUFACTURER, JOHN DOOR` → **B**: `JOHN DOOR MANUFACTURER`
- `CHURCH, OPEN DOOR DEL APOSTOLIC` → **B**: `OPEN DOOR DEL APOSTOLIC CHURCH`
- `CLUB, BANSHEE MOTORCYCLE` → **B**: `BANSHEE MOTORCYCLE CLUB`
- `YARD, EARL RATCLIFF WRECKING` → **B**: `EARL RATCLIFF WRECKING YARD`
- `COUNCIL, DENISON CITY` → **B**: `DENISON CITY COUNCIL`

## I-BAC — Business indicator after comma → swap order, keep I
When the token after the comma is a known business/occupational word, the two parts
are inverted. Swap them and keep marker as I.

Trigger words: `MANUFACTURERS`, `DISTRIBUTORS`, `CONTRACTORS`, `SUPPLIERS`.

- `CONSOLIDATION, MANUFACTURERS` → I: `MANUFACTURERS CONSOLIDATION`

## I-Hyphen — Hyphenated business word in "lastname" position → flag
When the part before the comma is a hyphenated token AND one of its components is a
known business/occupational word, the record is ambiguous (could be a business or a person
with a hyphenated surname). Flag for review — do not auto-classify.

Known business words that trigger this check: `MOVERS`, `MOVER`, `MOVING`, `BUILDERS`,
`BUILDER`, `BUILDING`, `WRECKING`, `CLEANING`, `RENTAL`, `RENTALS`, `ROOFING`,
`PLUMBING`, `PAINTING`, `WELDING`, `HAULING`, `TRUCKING`.

- `MOVERS-MILLER, HOUSE` → **flagged** (MOVERS is a business word; could be a moving company or a person)

Legitimate hyphenated surnames like `SMITH-JONES` pass through normally.

## I-Maiden — Maiden/birth surname appended at end → hyphenated lastname
When a name follows the pattern `MARRIED_LAST, FIRSTNAME MIDDLENAME BIRTH_LAST`,
the birth/maiden surname is appended as the last word after the comma. Combine it with
the married name using a hyphen and move it before the comma.

**Requires the name database to be loaded.** Applies only when:
- There are 3+ tokens after the comma
- Both the first AND second tokens are confirmed first names in the database
- The last token is not a known suffix (JR, SR, etc.)

- `GARNER, DEBORAH MARGARET ROGERS` → `ROGERS-GARNER, DEBORAH MARGARET`

The last token is treated as the maiden surname regardless of whether it also appears
in the first-name database (e.g. ROGERS is a rare male first name but here it is the
birth surname).

## Single-token reclassification (applied after I-3)
These checks run for any I record that reduces to a single token after stripping:

| Pattern | Action |
|---------|--------|
| Hyphenated compound (e.g. `WHOPPER-STOPPER`) | Flag for review |
| Known game/gambling name (e.g. `BINGO`) | Reclassify to **B** |
| ≤ 3 alpha chars, not a first name (e.g. `MCI`) | Reclassify to **B** |
| Single token not in first-name database (full pipeline only) | Flag for review |

---

## Hard rules
- **Never correct spelling errors** — `BRRITTAIN` stays `BRRITTAIN`
- **Never assume** when genuinely ambiguous — flag with a note instead
- **Never change** fields other than NAME (field 6)
- **IB marker** records are always left exactly as-is
- **Lines with fewer than 6 fields** are left exactly as-is