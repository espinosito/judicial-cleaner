# Special Cases by County and Year

This file grows as new patterns are discovered. Add a new section when you encounter
a pattern not covered by the standard rules in individuals.md or businesses.md.

---

## Grayson County, Texas — 1988 files

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

---

## Adding new sections

When you encounter a new pattern, add it here with:
1. A short descriptive title
2. The county and year it applies to
3. One or two examples showing input → output
4. Any exceptions to watch for