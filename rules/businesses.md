# Rules for B (Business / Entity) Records

Field being corrected: **field 6 (NAME)** only, unless a rule explicitly changes field 5 (MARKER).
Default: **do not modify** unless a specific rule below applies.

---

## B-1 — Default: no change
If none of B-2 through B-8 apply, leave the record exactly as-is.

## B-2 — Business prefix at start → move to end
When a business/institutional term appears at the START of the name, move it to the END.

Known prefixes: `INC`, `CORP`, `LLC`, `LTD`, `LP`, `LLP`, `PC`, `CO`, `NA`,
`ISD`, `ESD`, `ASSOCIATION`, `ASSOC`, `PARTNERSHIP`, `COMPANY`, `ENTERPRISES`,
`BANK`, `SAVINGS`, `HOSPITAL`, `CLINIC`, `DISTRICT`, `AUTHORITY`, `JAIL`,
`ESTATE`, `COURT`, `BOARD`, `BUREAU`, `FUND`, `LODGE`, `POST`, `CLUB`,
`UNIT`, `DIVISION`, `OFFICE`, `DEPT`

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
- `GRAYSON COUNTY OF` → `GRAYSON COUNTY` (trailing OF dropped)

## B-4 — Split on AND → two B records
When both sides of AND are businesses, split into two B records.

- `CORP COMMTRON CORPORATION AND EMERSON RADIO` → two B records

**Must NOT split (exceptions):**
- `SEARS ROEBUCK AND CO` — company name containing AND
- `BRORSON LAHAIE CULLEN AND ADAMS` — law firm
- `MUNSON MUNSON PIERCE AND CARDWELL PC` — law firm with PC
- `NALL PELLEY AND WYNNE` — law firm
- `NALL STAGNER AND PELLEY A PARTNERSHIP` — partnership entity
- `LOCAL UNION 540 UNITED FOOD AND COMMERCIAL WORKER` — union
- `DISTRICT S AND S INDEPENDENT SCHOOL` — school
- Any record ending in `IND AND` — truncated, do not split

## B-5 — Split on AND → two I records
When both sides of AND are people, split into two I records.
Convert each part from B-format (SURNAME FIRSTNAME) to I-format (SURNAME, FIRSTNAME).

- `MILLS JAMES E AND WIFE LINDA D MILLS` → `MILLS, JAMES E` + `MILLS, LINDA D`
- `STRAIN DONALD AND DOROTHY STRAIN` → `STRAIN, DONALD` + `STRAIN, DOROTHY`
- `YOUNG MARSHA AND DAVID` → `YOUNG, MARSHA` + `YOUNG, DAVID`

**WIFE/HUSBAND pattern:** extract only the named person and their spouse.
- `HEROD JAMES ROBERT SR AND WI` → keep only `HEROD, JAMES ROBERT SR` (WI = truncated WIFE)

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

---

## Hard rules
- **Marker IB** is always left exactly as-is, no exceptions
- **Do not change markers** on records not modified by these rules
- **Do not correct spelling** in business names
- **Lines with fewer than 6 fields** are left exactly as-is