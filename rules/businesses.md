# Rules for B (Business / Entity) Records

Field being corrected: **field 6 (NAME)** only, unless a rule explicitly changes field 5 (MARKER).
Default: **do not modify** unless a specific rule below applies.

---

## B-1 — Default: no change
If none of B-2 through B-8 apply, leave the record exactly as-is.

## B-2 — Business prefix at start → move to end
When a business/institutional term appears at the START of the name, move it to the END.

Known prefixes: `INC`, `CORP`, `LLC`, `LTD`, `LP`, `LLP`, `PC`, `CO`, `NA`,
`ISD`, `ESD`, `ASSOCIATION`, `ASSOC`, `ASSOCIATES`, `PARTNERSHIP`, `COMPANY`, `ENTERPRISES`,
`BANK`, `SAVINGS`, `HOSPITAL`, `CLINIC`, `DISTRICT`, `AUTHORITY`, `JAIL`,
`ESTATE`, `COURT`, `BOARD`, `BUREAU`, `FUND`, `LODGE`, `POST`, `CLUB`,
`UNIT`, `DIVISION`, `OFFICE`, `DEPT`,
`CAR`, `CARS`, `APPAREL`

**CAR/CARS rule:** vehicle-related words at the start must move to the end.
- `CARS QUALITY USED` → `QUALITY USED CARS`
- `CAR LOT FIRST CLASS` → `FIRST CLASS CAR LOT`

**ASSOCIATES rule:** when a record starts with ASSOCIATES, move it to the end.
- `ASSOCIATES DONALD L JARVIS AND` → `DONALD L JARVIS AND ASSOCIATES`

**APPAREL rule:** retail/clothing type word at the start must move to the end.
- `APPAREL S AND K` → `S AND K APPAREL`

Examples:
- `ISD POTTSBORO` → `POTTSBORO ISD`
- `HOSPITAL WILSON N JONES MEMORIAL` → `WILSON N JONES MEMORIAL HOSPITAL`
- `BANK GRAYSON COUNTY STATE` → `GRAYSON COUNTY STATE BANK`
- `NA CITIBANK SOUTH DAKOTA` → `CITIBANK SOUTH DAKOTA NA`
- `AUTHORITY DENISON HOSPITAL` → `DENISON HOSPITAL AUTHORITY`
- `JAIL GRAYSON COUNTY` → `GRAYSON COUNTY JAIL`
- `ESTATE JIM HARROD REAL` → `JIM HARROD REAL ESTATE`

## B-3 — Reversed geographic/governmental names
- `TEXAS STATE OF` → `STATE OF TEXAS`
- `GRAYSON COUNTY OF` → `COUNTY OF GRAYSON` (**COUNTY OF** moves to front)
- `VAN ALSTYNE CITY OF` → `CITY OF VAN ALSTYNE` (**CITY OF** moves to front)

**COUNTY OF pattern:** any record of the form `PLACE COUNTY OF` becomes `COUNTY OF PLACE`.

**CITY OF pattern:** any record of the form `PLACE CITY OF` becomes `CITY OF PLACE`.

## B-4 — Split on AND → two B records
When both sides of AND are businesses, split into two B records.

- `CORP COMMTRON CORPORATION AND EMERSON RADIO` → two B records

**Must NOT split (exceptions):**
- `SEAFOOD J AND J` — seafood business name (any record containing SEAFOOD)
- `SEARS ROEBUCK AND CO` — company name containing AND
- `BRORSON LAHAIE CULLEN AND ADAMS` — law firm
- `MUNSON MUNSON PIERCE AND CARDWELL PC` — law firm with PC
- `NALL PELLEY AND WYNNE` — law firm
- `NALL STAGNER AND PELLEY A PARTNERSHIP` — partnership entity
- `LOCAL UNION 540 UNITED FOOD AND COMMERCIAL WORKER` — union
- `DISTRICT S AND S INDEPENDENT SCHOOL` — school
- Any record ending in `IND AND` — truncated, do not split
- **Any record whose last token is `INC`, `LLC`, `LTD`, `LP`, `LLP`, `CORP`, or `CORPORATION`** — the whole name is a single entity
  - `LANGFORD AND MONTGOMERY SURVEY COMPANY INC` → leave as-is (B)

**Flag for review — do NOT split:**
- Any record where a split part would consist entirely of single-letter tokens (e.g. `C P`)
  - `C P AND ASSOCIIATESINC` → flagged (likely typo or garbled text)

## B-5 — Split on AND → two I records
When both sides of AND are people, split into two I records.
Convert each part from B-format (SURNAME FIRSTNAME) to I-format (SURNAME, FIRSTNAME).

- `MILLS JAMES E AND WIFE LINDA D MILLS` → `MILLS, JAMES E` + `MILLS, LINDA D`
- `STRAIN DONALD AND DOROTHY STRAIN` → `STRAIN, DONALD` + `STRAIN, DOROTHY`
- `YOUNG MARSHA AND DAVID` → `YOUNG, MARSHA` + `YOUNG, DAVID`
- `SCHNITKER RONALD J AND DOROTHY JEAN INDV AS` → `SCHNITKER, RONALD J` + `SCHNITKER, DOROTHY JEAN`

**Trailing legal text stripped before splitting:** `IN THE`, `IN RE`, `ET AL`, `AS NEXT FRIEND`, `INDV AS`
- Strip these from the end of the full name before splitting on AND.

**WIFE/HUSBAND pattern — single surname:**
When the pattern is `SURNAME AND WIFE FIRSTNAME` (single last name only, no first name on left),
produce ONE B record in the format `SURNAME, FIRSTNAME`.
- `HEROD AND WIFE STACYE` → B: `HEROD, STACYE`

**WIFE/HUSBAND pattern — full name:**
When the left side has a full name (surname + first name), produce two I records as usual.
- `HEROD JAMES ROBERT SR AND WIFE` → I: `HEROD, JAMES ROBERT SR` (spouse omitted if unnamed)

## B-6 — N K A (now known as) split
Split into two records at the N K A marker.

## B-7 — Reclassify after split
After any split, determine correct marker for each part:
- Contains business indicator → B
- Looks like a person (short name, no business words) → I

## B-8 — Misclassified person → convert to I
When a B record contains a person's name with no business indicators, convert to I.
Strip trailing ID/license numbers.

- `VANVORST MICHAEL J 8207424` → I: `VANVORST, MICHAEL J`
- `ROBERT LEE KITCHEN` → I: `KITCHEN, ROBERT LEE`

**Business indicators (B-8 will NOT convert these to I):**
The following words protect a record from B-8 conversion. This list includes:
`INC`, `LLC`, `CORP`, `COMPANY`, `BANK`, `HOSPITAL`, `SCHOOL`, `DISTRICT`,
`LUMBER`, `FITNESS`, `GYM`, `CAR`, `CARS`, `HOMES`, `MOBILE`, `STREET`,
`AVE`, `AVENUE`, `BLVD`, `BOULEVARD`, `USA`,
`MANUFACTURER`, `MANUFACTURERS`, `DISTRIBUTOR`, `DISTRIBUTORS`,
and many others — see `BUSINESS_INDICATORS` in `src/rules_b.py` for the full list.

**Flag for review instead of converting:**
- Records containing **alphanumeric tokens** (letters mixed with digits, e.g. `A-1`, `B2`) are
  flagged rather than converted. Pure trailing numbers (ID/license codes) are still stripped normally.
  - `HOMES A-1 MOBILE` → flagged
  - `VANVORST MICHAEL J 8207424` → I: `VANVORST, MICHAEL J` (pure number stripped, not flagged)

---

## Hard rules
- **Marker IB** is always left exactly as-is, no exceptions
- **Do not change markers** on records not modified by these rules
- **Do not correct spelling** in business names
- **Lines with fewer than 6 fields** are left exactly as-is
