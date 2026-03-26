# Rules for I (Individual / Person) Records

Field being corrected: **field 6 (NAME)** only.
Correct format always: `LASTNAME, NAME [MIDDLE] [SUFFIX]`

---

## I-1 — Suffix placement
Suffixes `JR`, `SR`, `II`, `III`, `IV` go at the END with no comma before them.
- `CHAMBERS, GARY MADOX, JR` → `CHAMBERS, GARY MADOX JR`

## I-2 — Delete junk rows
Delete the entire row (not the case) when name is:
- Just a comma: `,` or `, `
- `MOVANT,` or `MOVANT, ` (legal role placeholder)
- `LIENHOLDER,` (legal text, no real name)
- `FOR, MOTHER- ATTY GEN` (legal text)
- Single letter with no context: `N`

## I-3 — Strip legal fragments
Remove these fragments, keep only the real name:
- `IN REM ONLY`, `IN REM`
- `LIENHOLDER IN REM ONLY`, `LIENHOLDER`
- `DECEASED`
- `TRUSTEE`
- `INDIVIDUALLY`

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

## Hard rules
- **Never correct spelling errors** — `BRRITTAIN` stays `BRRITTAIN`
- **Never assume** when genuinely ambiguous — flag with a note instead
- **Never change** fields other than NAME (field 6)
- **IB marker** records are always left exactly as-is
- **Lines with fewer than 6 fields** are left exactly as-is