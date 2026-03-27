"""
rules_b.py
All transformation rules for B (business/entity) records.
Rules match the prompt_maestro exactly: B-1 through B-8.

Each rule receives a name string and returns either:
  - str            : corrected name (same marker B)
  - list[dict]     : split into multiple records [{marker, name}, ...]
  - unchanged      : return original (B-1 default)
"""
from __future__ import annotations
import re


class FlagForReview(Exception):
    """Raised when a B record is too ambiguous or weird to process automatically."""
    pass


# ---------------------------------------------------------------------------
# Business prefixes that appear at the START and must move to the END (B-2)
# These are terms that belong after the proper name, not before it
# ---------------------------------------------------------------------------
# Legal entity type suffixes placed at front (CORP X AND Y → two entities, B-4 wins over B-2)
LEGAL_TYPE_PREFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "LLC", "LTD", "LP", "LLP", "PC", "CO",
}

BUSINESS_PREFIXES = [
    # Legal suffixes placed at front
    "INC", "INCORPORATED", "CORP", "CORPORATION", "LLC", "LTD", "LP",
    "LLP", "PC", "CO",
    # Institutional terms placed at front (Grayson-specific)
    "ISD", "ESD",
    # Organizational types
    "ASSOCIATION", "ASSOC", "ASSOCIATES", "PARTNERSHIP", "COMPANY", "ENTERPRISES",
    # Financial
    "BANK", "SAVINGS",
    # Geographic/governmental placed at front
    "HOSPITAL", "CLINIC", "DISTRICT",
    "AUTHORITY", "JAIL", "ESTATE", "COURT", "BOARD", "BUREAU", "FUND",
    "LODGE", "POST", "CLUB", "UNIT", "DIVISION", "OFFICE", "DEPT",
    # NA prefix (banking: NA CITIBANK → CITIBANK NA)
    "NA",
    # Vehicle-related prefixes (CAR/CARS go at end: CARS QUALITY USED → QUALITY USED CARS)
    "CAR", "CARS",
]

# Phrases that must NOT be split even though they contain AND (B-4 exceptions)
NO_SPLIT_PATTERNS = [
    r"\bSEARS ROEBUCK AND CO\b",
    r"\bIND AND\b",                          # individual defendant + truncated
    r"\bAND AS ADM",                         # legal role
    r"\bAND AS ADMINSTARTRIX\b",
    r"\bAND AS NEXT FRIEND\b",
    r"\bA PARTNERSHIP\b",
    r"\bPC\s*$",                             # law firm with PC at end
    r"\bNALL .+ AND\b",                      # known law firms
    r"\bLOCAL UNION\b",
    r"\bSCHOOL DISTRICT\b",
    r"\bFOOD AND COMMERCIAL\b",
    r"\bS AND S INDEPENDENT\b",
    r"^SERVICE\b",              # SERVICE records are businesses, not people
    # Whole name ends with a hard legal suffix → single entity (e.g. LANGFORD AND MONTGOMERY SURVEY COMPANY INC)
    r"\bINC\s*$", r"\bLLC\s*$", r"\bLTD\s*$", r"\bLP\s*$", r"\bLLP\s*$",
    r"\bCORPORATION\s*$", r"\bCORP\s*$",
]

# Words that indicate the whole B record is actually a person (B-8)
# If a B record has NONE of these, it may be a misclassified person
BUSINESS_INDICATORS = {
    "INC", "LLC", "LTD", "LP", "PC", "CORP", "CORPORATION", "LLP",
    "COMPANY", "COMPANIES", "BANK", "SAVINGS", "ASSOCIATION", "ASSOC",
    "PARTNERSHIP", "PARTNERS", "GROUP", "ENTERPRISES", "INDUSTRIES",
    "INDUSTRIAL", "SERVICES", "SYSTEMS", "MANAGEMENT", "PROPERTIES",
    "CONSTRUCTION", "DEVELOPMENT", "INVESTMENTS", "FINANCIAL",
    "INSURANCE", "MEDICAL", "HOSPITAL", "CLINIC", "DISTRICT", "SCHOOL",
    "DEPARTMENT", "DEPT", "COUNTY", "STATE", "CITY", "GOVERNMENT",
    "FEDERAL", "NATIONAL", "MEMORIAL", "FOUNDATION", "INSTITUTE",
    "AUTHORITY", "COMMISSION", "AGENCY", "BUREAU", "OFFICE",
    "REALTY", "REALTORS", "MORTGAGE", "TITLE", "SUPPLY", "SUPPLIES",
    "EQUIPMENT", "TRANSPORT", "TRANSPORTATION", "TRUCKING", "FREIGHT",
    "ELECTRIC", "ELECTRICAL", "UTILITIES", "UTILITY", "PETROLEUM",
    "RESTAURANT", "CAFE", "FOOD", "MARKET", "STORE", "SHOP", "SALON",
    "ISD", "ESD", "NA", "FSB", "CBIC",
    "AND",  # most real businesses with AND are firms (SMITH AND JONES PC)
    # Additional confirmed business indicators
    "LUMBER", "FITNESS", "GYM", "CAR", "CARS", "HOMES", "MOBILE",
    "STREET", "AVE", "AVENUE", "BLVD", "BOULEVARD", "USA",
    "MANUFACTURER", "MANUFACTURERS", "DISTRIBUTOR", "DISTRIBUTORS",
}

PERSONAL_SUFFIXES = {"JR", "SR", "II", "III", "IV", "MD", "PA", "DDS"}


# ---------------------------------------------------------------------------
# B-1: Default — do not modify
# ---------------------------------------------------------------------------
def apply_b1(name: str) -> str:
    return name


# ---------------------------------------------------------------------------
# B-2: Move business prefix from START to END
# ISD POTTSBORO          → POTTSBORO ISD
# BANK GRAYSON COUNTY STATE → GRAYSON COUNTY STATE BANK
# HOSPITAL WILSON N JONES MEMORIAL → WILSON N JONES MEMORIAL HOSPITAL
# NA CITIBANK SOUTH DAKOTA → CITIBANK SOUTH DAKOTA NA
# ---------------------------------------------------------------------------
def apply_b2(name: str) -> str | None:
    tokens = name.strip().split()
    if not tokens:
        return name

    first = tokens[0].upper().rstrip(".")

    if first not in [p.upper() for p in BUSINESS_PREFIXES]:
        return None  # rule does not apply

    prefix = tokens[0]
    rest = " ".join(tokens[1:])

    if not rest.strip():
        return name  # nothing after prefix, leave as-is

    return f"{rest} {prefix}"


# ---------------------------------------------------------------------------
# B-3: Reversed geographic/institutional names (subset of B-2)
# TEXAS STATE OF  → STATE OF TEXAS
# GRAYSON COUNTY OF → GRAYSON COUNTY  (drop trailing OF)
# ---------------------------------------------------------------------------
def apply_b3(name: str) -> str | None:
    stripped = name.strip()

    # Pattern: "WORD STATE OF" → STATE OF WORD  (e.g. TEXAS STATE OF → STATE OF TEXAS)
    m = re.match(r"^(.+?)\s+STATE\s+OF\s*$", stripped, re.IGNORECASE)
    if m:
        place = m.group(1).strip()
        return f"STATE OF {place}"

    # Pattern: "PLACE COUNTY OF" → "COUNTY OF PLACE"  (e.g. GRAYSON COUNTY OF → COUNTY OF GRAYSON)
    m = re.match(r"^(.+?)\s+COUNTY\s+OF\s*$", stripped, re.IGNORECASE)
    if m:
        place = m.group(1).strip()
        return f"COUNTY OF {place}"

    # Pattern: "PLACE CITY OF" → "CITY OF PLACE"  (e.g. VAN ALSTYNE CITY OF → CITY OF VAN ALSTYNE)
    m = re.match(r"^(.+?)\s+CITY\s+OF\s*$", stripped, re.IGNORECASE)
    if m:
        place = m.group(1).strip()
        return f"CITY OF {place}"

    # Pattern: anything ending in bare OF → drop the OF
    m = re.match(r"^(.+?)\s+OF\s*$", stripped, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    return None  # rule does not apply


# ---------------------------------------------------------------------------
# Helpers for AND splitting (B-4, B-5)
# ---------------------------------------------------------------------------

def _should_not_split(name: str) -> bool:
    """Return True if this record must NOT be split despite having AND."""
    for pattern in NO_SPLIT_PATTERNS:
        if re.search(pattern, name, re.IGNORECASE):
            return True
    return False


def _split_on_and(name: str) -> list[str] | None:
    """
    Split 'NAME1 AND NAME2' into [NAME1, NAME2].
    Returns None if AND is not a clean separator.
    Handles trailing AND (VOGDS VOGDS AND → just VOGDS VOGDS).
    """
    # Remove trailing AND
    clean = re.sub(r"\s+AND\s*$", "", name.strip())

    # Split on AND surrounded by spaces
    parts = re.split(r"\s+AND\s+", clean, flags=re.IGNORECASE)

    if len(parts) < 2:
        return None

    # Clean each part
    parts = [p.strip() for p in parts if p.strip()]
    return parts if len(parts) >= 2 else None


def _looks_like_person(name: str) -> bool:
    """
    Quick check: does this name look like a person rather than a business?
    Used after splitting to decide marker.
    """
    tokens = name.upper().split()
    # Has any business indicator → not a person
    if any(t in BUSINESS_INDICATORS for t in tokens):
        return False
    # Has personal suffix → definitely a person
    if tokens and tokens[-1] in PERSONAL_SUFFIXES:
        return True
    # Short (2-3 tokens), no business words → likely a person
    if len(tokens) <= 3:
        return True
    return False


# ---------------------------------------------------------------------------
# B-4: Split B record with AND into two B records
# CORP COMMTRON CORPORATION AND EMERSON RADIO → two B records
# ---------------------------------------------------------------------------
def apply_b4(name: str) -> list[dict] | None:
    if "AND" not in name.upper():
        return None
    if _should_not_split(name):
        return None

    parts = _split_on_and(name)
    if not parts:
        return None

    # Flag if any part consists entirely of single-letter tokens (e.g. "C P")
    for part in parts:
        tokens = part.strip().split()
        if tokens and all(len(t) == 1 for t in tokens):
            raise FlagForReview(f"split part has only single-letter tokens: {part!r} in {name!r}")

    # If at least one side is clearly a business, split both as B
    # (EMERSON RADIO has no suffix but is still a business in context)
    has_business_side = any(not _looks_like_person(p) for p in parts)
    has_person_side = any(_looks_like_person(p) for p in parts)

    if has_business_side and not has_person_side:
        # Both clearly businesses
        return [{"marker": "B", "name": p} for p in parts]

    if has_business_side and has_person_side:
        # Mixed: one clear business, one ambiguous short name
        # Keep both as B (original marker) — safer than guessing
        return [{"marker": "B", "name": p} for p in parts]

    return None  # both look like people — let B-5 handle


# ---------------------------------------------------------------------------
# B-5: Split B record with AND into two I records (both sides are people)
# MILLS JAMES E AND WIFE LINDA D MILLS → two I records
# YOUNG MARSHA AND DAVID → ambiguous, flag
# ---------------------------------------------------------------------------
# Legal suffixes that appear at end of B names — strip before splitting
TRAILING_LEGAL = [
    r"\s+IN\s+THE\s*$",          # DENSMORE ... IN THE
    r"\s+IN\s+RE\b.*$",          # IN RE ... (legal case reference)
    r"\s+ET\s+AL\.?\s*$",       # ET AL
    r"\s+AS\s+NEXT\s+FRIEND.*$", # AS NEXT FRIEND OF
]

def _strip_trailing_legal(name: str) -> str:
    """Remove trailing legal phrases that are not part of the name."""
    result = name
    for pattern in TRAILING_LEGAL:
        result = re.sub(pattern, "", result, flags=re.IGNORECASE).strip()
    return result


def apply_b5(name: str, classifier=None) -> list[dict] | None:
    if "AND" not in name.upper():
        return None
    if _should_not_split(name):
        return None

    # "WIFE" pattern — extract only the named person, skip WIFE
    m = re.match(r"^(.+?)\s+AND\s+(WIFE|HUSBAND)\s*(.*)$", name.strip(), re.IGNORECASE)
    if m:
        person1_raw = m.group(1).strip()
        extra = m.group(3).strip()

        # Single last name + AND WIFE/HUSBAND + first name → B: LASTNAME, FIRSTNAME
        # (e.g. HEROD AND WIFE STACYE → B: HEROD, STACYE)
        if len(person1_raw.split()) == 1 and extra and len(extra.split()) <= 2:
            return [{"marker": "B", "name": f"{person1_raw}, {extra}"}]

        # person1 is a B-format name (e.g. MILLS JAMES E) → convert to I
        person1 = _b_name_to_i(person1_raw)
        results = [{"marker": "I", "name": person1}]
        if extra:
            # "LINDA D MILLS" where MILLS matches p1 first token → surname at end
            p1_tokens = person1_raw.split()
            ex_tokens = extra.split()
            p1_surname = p1_tokens[0].upper() if p1_tokens else ""
            if ex_tokens and ex_tokens[-1].upper() == p1_surname:
                surname = ex_tokens[-1]
                resto = " ".join(ex_tokens[:-1])
                person2 = f"{surname}, {resto}" if resto else surname
            else:
                person2 = _b_name_to_i(extra)
            results.append({"marker": "I", "name": person2})
        return results

    # Strip trailing legal text before splitting (DENSMORE ... IN THE)
    clean_name = _strip_trailing_legal(name)
    parts = _split_on_and(clean_name)
    if not parts or len(parts) != 2:
        return None

    # Flag if any part consists entirely of single-letter tokens (e.g. "C P")
    for part in parts:
        toks = part.strip().split()
        if toks and all(len(t) == 1 for t in toks):
            raise FlagForReview(f"split part has only single-letter tokens: {part!r} in {name!r}")

    # Both sides look like people → split into I records
    if all(_looks_like_person(p) for p in parts):
        records = []
        p0_tokens = parts[0].split()
        p1_tokens = parts[1].split()

        # Detect shared surname:
        # Case A: both parts end with same word  (MILLS JAMES / LINDA MILLS)
        # Case B: first part starts with surname, second part ends with it
        #         (STRAIN DONALD / DOROTHY STRAIN)
        # Case C: second part is a single token (just a first name)
        #         (YOUNG MARSHA / DAVID) → surname from first part
        # Case D: first part has 3+ tokens (SURNAME FIRST MIDDLE) and second
        #         part has no overlap with first → inherit surname from p0[0]
        #         (DENSMORE SHAWN WESTLY / CHRISTY LYNN)
        shared_surname = None
        if p0_tokens and p1_tokens:
            p0_upper = {t.upper() for t in p0_tokens}
            p1_upper = {t.upper() for t in p1_tokens}
            if p0_tokens[-1].upper() == p1_tokens[-1].upper():
                shared_surname = p1_tokens[-1]          # Case A
            elif p0_tokens[0].upper() == p1_tokens[-1].upper():
                shared_surname = p0_tokens[0]           # Case B
            elif len(p1_tokens) == 1:
                shared_surname = p0_tokens[0]           # Case C
            elif len(p0_tokens) >= 3 and not p0_upper & p1_upper:
                # Case D: no common tokens, first part has surname+first+middle
                # Assume p0[0] is the shared surname
                shared_surname = p0_tokens[0]

        for part in parts:
            tok = part.split()
            if shared_surname:
                tok_upper = {t.upper() for t in tok}
                if shared_surname.upper() not in tok_upper:
                    # Surname not present in this part at all → prepend it
                    # CHRISTY LYNN → DENSMORE, CHRISTY LYNN
                    # DAVID        → YOUNG, DAVID
                    name_i = f"{shared_surname}, {part.strip()}"
                elif tok and tok[-1].upper() == shared_surname.upper():
                    # Surname at end → move to front
                    # DOROTHY STRAIN → STRAIN, DOROTHY
                    surname = tok[-1]
                    resto = " ".join(tok[:-1])
                    name_i = f"{surname}, {resto}" if resto else surname
                else:
                    # Surname already at front → standard B→I conversion
                    # DENSMORE SHAWN WESTLY → DENSMORE, SHAWN WESTLY
                    name_i = _b_name_to_i(part)
            else:
                name_i = _b_name_to_i(part)
            records.append({"marker": "I", "name": name_i})
        return records

    return None  # mixed B+I → ambiguous


def _b_name_to_i(name: str) -> str:
    """
    Convert a B-style name (no comma) to I format (APELLIDO, NOMBRE).
    MILLS JAMES E → MILLS, JAMES E
    Only applies when no comma already present.

    Heuristic: first token is apellido (standard Grayson format).
    Exception: if last token matches first token (DOROTHY STRAIN → STRAIN, DOROTHY)
    or if last token is clearly a surname repeated from context.
    """
    if "," in name:
        return name
    tokens = name.strip().split()
    if len(tokens) < 2:
        return name
    # If last token is same as first → surname is at end (DOROTHY STRAIN format)
    # In split records the surname often appears at end: DOROTHY STRAIN
    # We keep first token as apellido — it's the most reliable signal in this dataset
    apellido = tokens[0]
    resto = " ".join(tokens[1:])
    return f"{apellido}, {resto}"


# ---------------------------------------------------------------------------
# B-6: N K A (now known as) split
# SMITH JOHN N K A JOHNSON JOHN → two records
# ---------------------------------------------------------------------------
def apply_b6(name: str) -> list[dict] | None:
    m = re.search(r"\bN\s*K\s*A\b", name, re.IGNORECASE)
    if not m:
        return None

    before = name[:m.start()].strip()
    after = name[m.end():].strip()

    if not before or not after:
        return None

    marker_before = "I" if _looks_like_person(before) else "B"
    marker_after = "I" if _looks_like_person(after) else "B"

    result = []
    if before:
        n = _b_name_to_i(before) if marker_before == "I" else before
        result.append({"marker": marker_before, "name": n})
    if after:
        n = _b_name_to_i(after) if marker_after == "I" else after
        result.append({"marker": marker_after, "name": n})

    return result if result else None


# ---------------------------------------------------------------------------
# B-7: After a split, reclassify each part as I or B
# (called internally by B-4/B-5 via _looks_like_person)
# Exposed here for explicit use if needed
# ---------------------------------------------------------------------------
def apply_b7(name: str) -> str:
    """Returns 'I' or 'B' for the given name."""
    return "I" if _looks_like_person(name) else "B"


# ---------------------------------------------------------------------------
# B-8: B record that is actually a person — convert to I
# VANVORST MICHAEL J 8207424 → I: VANVORST, MICHAEL J
# ROBERT LEE KITCHEN → I: KITCHEN, ROBERT LEE
# ---------------------------------------------------------------------------
def apply_b8(name: str, classifier=None) -> dict | None:
    tokens = name.upper().split()

    # Strip trailing numbers (ID/license numbers)
    clean_tokens = [t for t in tokens if not re.match(r"^\d+$", t)]
    clean_name = " ".join(clean_tokens)

    # If it has business indicators → stay B
    if any(t in BUSINESS_INDICATORS for t in clean_tokens):
        return None

    # If it looks like a person (short, no business words) → convert to I
    if _looks_like_person(clean_name):
        i_name = _b_name_to_i(clean_name)
        return {"marker": "I", "name": i_name}

    return None


# ---------------------------------------------------------------------------
# Master function: apply B rules in the correct order
# Returns one of:
#   (str, str)         — (corrected_name, rule_applied), same marker B
#   (list[dict], str)  — split records, each has marker+name
#   (None, str)        — delete record (rare)
# ---------------------------------------------------------------------------
def apply_all_b_rules(name: str, classifier=None) -> tuple:
    original = name

    # Early guard: flag B records containing alphanumeric tokens (e.g. A-1, B2)
    # Pure numbers are excluded — only mixed letter+digit tokens trigger this.
    _tokens = name.upper().split()
    _clean = [t for t in _tokens if not re.match(r"^\d+$", t)]
    if any(re.search(r'\d', t) for t in _clean):
        raise FlagForReview(f"B record with alphanumeric token: {name!r}")

    # B-6 first — N K A splits are unambiguous
    result = apply_b6(name)
    if result:
        return result, "B-6"

    # B-2 priority: move prefix to end BEFORE AND splits — but only for
    # descriptive prefixes (COMPANY, HOSPITAL...). Legal type prefixes
    # (CORP, INC, LLC...) at the front mean the first entity has that type,
    # so AND separates two distinct entities → let B-4 handle it.
    first_token = name.strip().split()[0].upper().rstrip(".") if name.strip() else ""
    first_is_legal_type = first_token in LEGAL_TYPE_PREFIXES
    first_is_prefix = first_token in [p.upper() for p in BUSINESS_PREFIXES]

    if first_is_prefix and not first_is_legal_type:
        # Descriptive prefix (COMPANY, HOSPITAL, etc.) — B-2 wins over AND splits
        result = apply_b2(name)
        if result:
            return result, "B-2"

    # B-3 — reversed geographic names
    result = apply_b3(name)
    if result:
        return result, "B-3"

    # B-4 / B-5 — AND splits (only after prefix check)
    if "AND" in name.upper() and not _should_not_split(name):
        # Try B-5 first (person split) — more specific
        result = apply_b5(name, classifier)
        if result:
            return result, "B-5"
        # Then B-4 (business split)
        result = apply_b4(name)
        if result:
            return result, "B-4"

    # B-2 — prefix at start → move to end (for non-AND cases not caught above)
    result = apply_b2(name)
    if result:
        return result, "B-2"

    # B-8 — misclassified person
    result = apply_b8(name, classifier)
    if result:
        return result, "B-8"

    # B-1 — no change
    return original, "B-1"


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        # (rule, input, expected)
        ("B-2", "ISD POTTSBORO",                          "POTTSBORO ISD"),
        ("B-2", "HOSPITAL WILSON N JONES MEMORIAL",       "WILSON N JONES MEMORIAL HOSPITAL"),
        ("B-2", "BANK GRAYSON COUNTY STATE",              "GRAYSON COUNTY STATE BANK"),
        ("B-2", "CO CONSTRUCTION",                        "CONSTRUCTION CO"),
        ("B-2", "COMPANY GILLORD-HILL AND",               "GILLORD-HILL AND COMPANY"),
        ("B-2", "COMPANY RUSHING PAVING",                 "RUSHING PAVING COMPANY"),
        ("B-2", "LP LATTIMORE MATERIALS COMPANY",         "LATTIMORE MATERIALS COMPANY LP"),
        ("B-2", "ASSOCIATION SUNBELT SAVINGS",            "SUNBELT SAVINGS ASSOCIATION"),
        ("B-2", "NA CITIBANK SOUTH DAKOTA",               "CITIBANK SOUTH DAKOTA NA"),
        ("B-3", "TEXAS STATE OF",                         "STATE OF TEXAS"),
        ("B-3", "GRAYSON COUNTY OF",                      "GRAYSON COUNTY"),
        ("B-4", "CORP COMMTRON CORPORATION AND EMERSON RADIO",
                [{"marker": "B", "name": "CORP COMMTRON CORPORATION"},
                 {"marker": "B", "name": "EMERSON RADIO"}]),
        ("B-5", "MILLS JAMES E AND WIFE LINDA D MILLS",
                [{"marker": "I", "name": "MILLS, JAMES E"},
                 {"marker": "I", "name": "MILLS, LINDA D"}]),
        ("B-5", "STRAIN DONALD AND DOROTHY STRAIN",
                [{"marker": "I", "name": "STRAIN, DONALD"},
                 {"marker": "I", "name": "STRAIN, DOROTHY"}]),
        ("B-1", "SEARS ROEBUCK AND CO",                   "SEARS ROEBUCK AND CO"),
        ("B-1", "MIT-CON INC",                            "MIT-CON INC"),
        ("B-1", "BULK-PACK INC",                          "BULK-PACK INC"),
        ("B-8", "VANVORST MICHAEL J 8207424",
                {"marker": "I", "name": "VANVORST, MICHAEL J"}),
    ]

    passed = 0
    failed = 0
    print(f"{'Rule':<6} {'Result':<5} Input")
    print("-" * 80)
    for rule, name, expected in tests:
        got, applied = apply_all_b_rules(name)
        ok = got == expected
        mark = "✓" if ok else "✗"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"{rule:<6} {mark}      {name}")
        if not ok:
            print(f"{'':>13} expected : {expected!r}")
            print(f"{'':>13} got      : {got!r}")

    print(f"\n{passed}/{passed+failed} passed")