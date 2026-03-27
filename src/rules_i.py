"""
rules_i.py
All transformation rules for I (individual/person) records.
Rules match the prompt exactly: I-1 through I-10.

Each rule receives a name string and returns:
  - str          : corrected name
  - None         : delete this row entirely
  - raises AmbiguousCase : cannot decide, needs Claude
"""
from __future__ import annotations
import re


class AmbiguousCase(Exception):
    """Raised when a rule cannot decide — caller will flag for Claude."""
    pass


class ReclassifyAsB(Exception):
    """Raised when an I record is clearly a business — caller changes marker to B."""
    def __init__(self, new_name: str):
        super().__init__(new_name)
        self.new_name = new_name


# ---------------------------------------------------------------------------
# Known first names that appear INVERTED in Grayson files (rule I-4)
# Add to this list as new files are processed
# ---------------------------------------------------------------------------
KNOWN_INVERTED_FIRST_NAMES = {
    "CHERYL", "CHARLES", "JIMMY", "JOHN", "MARY",
}

# Legal fragments to strip from names (rule I-3)
LEGAL_FRAGMENTS = [
    r"\bIN REM ONLY\b",
    r"\bLIENHOLDER IN REM ONLY\b",
    r"\bIN REM\b",
    r"\bDECEASED\b",
    r"\bTRUSTEE\b",
    r"\bLIENHOLDER\b",
    r"\bINDIVIDUALLY\b",
]

SUFFIXES = {"JR", "SR", "II", "III", "IV"}

# Single-token I records that are known to be games/gambling — always B
GAME_NAMES = {
    "BINGO", "POKER", "LOTTO", "LOTTERY", "KENO", "BLACKJACK", "ROULETTE",
    "CHECKERS", "CHESS", "DOMINOES", "MAHJONG",
}

# Tokens that are business indicators when placed BEFORE the comma in an I record
# Pattern: "MANUFACTURER, JOHN DOOR" → B "JOHN DOOR MANUFACTURER"
BUSINESS_BEFORE_COMMA = {
    "MANUFACTURER", "MANUFACTURERS", "DISTRIBUTOR", "DISTRIBUTORS",
    "CONTRACTOR", "CONTRACTORS", "SUPPLIER", "SUPPLIERS",
    "CHURCH", "CLUB", "YARD", "COUNCIL",
}

# Words that indicate a business when found as a part of a hyphenated "lastname"
# Pattern: "MOVERS-MILLER, HOUSE" → AmbiguousCase (could be business or person)
BUSINESS_WORDS_IN_HYPHEN = {
    "MOVERS", "MOVER", "MOVING", "BUILDERS", "BUILDER", "BUILDING",
    "WRECKING", "CLEANING", "RENTAL", "RENTALS", "ROOFING",
    "PLUMBING", "PAINTING", "WELDING", "HAULING", "TRUCKING",
}

# Tokens that are business indicators when placed AFTER the comma in an I record
# Pattern: "CONSOLIDATION, MANUFACTURERS" → I "MANUFACTURERS CONSOLIDATION"
BUSINESS_AFTER_COMMA = {
    "MANUFACTURERS", "DISTRIBUTORS", "CONTRACTORS", "SUPPLIERS",
}


# ---------------------------------------------------------------------------
# Pre-rules: reclassify checks applied AFTER I-3 strips the trailing comma
# ---------------------------------------------------------------------------

def apply_mc_prefix(name: str) -> str | None:
    """
    MC, DADE WILLIE MAE  →  MCDADE, WILLIE MAE
    When the part before the comma is exactly 'MC' or 'MAC', join it with the
    first token after the comma.  Returns None if pattern does not match.
    """
    if "," not in name:
        return None
    before, after = name.split(",", 1)
    before = before.strip()
    after = after.strip()
    if before.upper() not in ("MC", "MAC"):
        return None
    after_tokens = after.split()
    if not after_tokens:
        return None
    new_last = before + after_tokens[0]          # MCDADE
    rest = " ".join(after_tokens[1:])            # WILLIE MAE
    return f"{new_last}, {rest}" if rest else new_last


def apply_business_before_comma(name: str) -> None:
    """
    Detect a business indicator before the comma and raise ReclassifyAsB.
    MANUFACTURER, JOHN DOOR  →  ReclassifyAsB("JOHN DOOR MANUFACTURER")
    """
    if "," not in name:
        return
    before, after = name.split(",", 1)
    before_token = before.strip().upper()
    if before_token in BUSINESS_BEFORE_COMMA:
        after_clean = after.strip()
        new_name = f"{after_clean} {before_token}".strip() if after_clean else before_token
        raise ReclassifyAsB(new_name)


def apply_business_after_comma(name: str) -> str | None:
    """
    Detect a business indicator after the comma and swap the two parts.
    CONSOLIDATION, MANUFACTURERS  →  MANUFACTURERS CONSOLIDATION  (stays I)
    Returns None if pattern does not match.
    """
    if "," not in name:
        return None
    before, after = name.split(",", 1)
    after_token = after.strip().upper()
    if after_token in BUSINESS_AFTER_COMMA:
        return f"{after.strip()} {before.strip()}"
    return None


def check_single_token_reclassify(name: str, db=None) -> None:
    """
    For I records that reduced to a single token after stripping:
    - Hyphenated compound (WHOPPER-STOPPER)  → AmbiguousCase
    - Known game/gambling name (BINGO)       → ReclassifyAsB
    - ≤3 uppercase letters, not a first name → ReclassifyAsB
    - Any other single token not in name db  → AmbiguousCase (flag for review)
    """
    tokens = name.strip().split()
    if len(tokens) != 1:
        return
    token = tokens[0]

    # Hyphenated compound → flag
    if "-" in token:
        raise AmbiguousCase(f"hyphenated non-name token: {token!r}")

    # Known game/gambling names → B
    if token.upper() in GAME_NAMES:
        raise ReclassifyAsB(token.upper())

    # Short abbreviation (≤3 alpha chars), not a known first name → B
    if len(token) <= 3 and token.isalpha():
        if db is None or not db.is_first_name(token):
            raise ReclassifyAsB(token.upper())

    # Single token not in first name database → flag for Claude review
    if db is not None and not db.is_first_name(token):
        raise AmbiguousCase(f"single-token name not in database: {token!r}")


def check_hyphenated_business_before_comma(name: str) -> None:
    """
    If the part before the comma is a hyphenated token containing a known
    business word, this record is ambiguous — raise AmbiguousCase.
    MOVERS-MILLER, HOUSE  →  AmbiguousCase
    """
    if "," not in name:
        return
    before, _ = name.split(",", 1)
    before = before.strip()
    if "-" not in before:
        return
    for part in before.split("-"):
        if part.upper() in BUSINESS_WORDS_IN_HYPHEN:
            raise AmbiguousCase(f"hyphenated business word in name position: {before!r}")


def apply_maiden_name_rule(name: str, db=None) -> str | None:
    """
    Detect a maiden name appended at the end of a full name.
    GARNER, DEBORAH MARGARET ROGERS  →  ROGERS-GARNER, DEBORAH MARGARET

    Applies only when:
      - name has a comma
      - 3+ tokens after the comma
      - first AND second tokens after comma are confirmed first names in the DB
      - last token is not a known suffix (JR, SR, etc.)
    The last token is treated as the birth/maiden surname regardless of whether
    it appears in the first-name DB (e.g. ROGERS is a rare male first name but
    here it is clearly a maiden surname).
    Returns None if pattern does not match.
    """
    if db is None:
        return None
    if "," not in name:
        return None
    before, after = name.split(",", 1)
    before = before.strip()
    after = after.strip()
    tokens = after.split()
    if len(tokens) < 3:
        return None
    first = tokens[0]
    second = tokens[1]
    last = tokens[-1]
    if last.upper() in SUFFIXES:
        return None
    # Both first and second tokens must be confirmed first names
    if not db.is_first_name(first):
        return None
    if not db.is_first_name(second):
        return None
    middle = tokens[2:-1]  # any tokens between second name and maiden name
    new_last = f"{last}-{before}"
    new_rest = " ".join([first, second] + middle)
    return f"{new_last}, {new_rest}"


# ---------------------------------------------------------------------------
# I-1: Normalize suffix placement — no comma before suffix
# CHAMBERS, GARY MADOX, JR  →  CHAMBERS, GARY MADOX JR
# ---------------------------------------------------------------------------
def apply_i1(name: str) -> str:
    for suffix in SUFFIXES:
        # Pattern: ", JR" or ",JR" at end → " JR"
        name = re.sub(rf",\s*\b{suffix}\b\s*$", f" {suffix}", name, flags=re.IGNORECASE)
    return name.strip()


# ---------------------------------------------------------------------------
# I-2: Delete rows where name is empty or just a comma/whitespace.
# Returns None to signal "delete this row".
# Only bare commas and empty strings are safe to auto-delete.
# Ambiguous role labels (MOVANT, LIENHOLDER, RESPONDENT, etc.) are NOT deleted
# here — the pipeline flags those cases for manual review instead.
# ---------------------------------------------------------------------------
JUNK_NAMES = {",", ", ", ""}

def apply_i2(name: str) -> str | None:
    stripped = name.strip()
    if stripped in JUNK_NAMES:
        return None
    if re.match(r"^,\s*$", stripped):
        return None
    return name


# ---------------------------------------------------------------------------
# I-3: Strip legal fragments, keep only the real name
# SMITH, IN REM ONLY HARRY  →  SMITH, HARRY
# ---------------------------------------------------------------------------
def apply_i3(name: str) -> str:
    result = name
    for fragment in LEGAL_FRAGMENTS:
        result = re.sub(fragment, " ", result, flags=re.IGNORECASE)
    # Clean up extra spaces
    result = re.sub(r"\s{2,}", " ", result).strip().rstrip(",").strip()
    return result


# ---------------------------------------------------------------------------
# I-4: Fix inverted names (NAME, LASTNAME → LASTNAME, NAME)
# Only applies when the token before the comma is in KNOWN_INVERTED_FIRST_NAMES
# ---------------------------------------------------------------------------
def apply_i4(name: str, extra_known: set[str] | None = None) -> str:
    known = KNOWN_INVERTED_FIRST_NAMES.copy()
    if extra_known:
        known.update(extra_known)

    if "," not in name:
        return name

    before, after = name.split(",", 1)
    before = before.strip()
    after = after.strip()

    if before.upper() not in known:
        return name  # not an inverted name we recognize

    after_tokens = after.split()

    if not after_tokens:
        return name

    # NAME, LASTNAME  (1 word after comma)
    if len(after_tokens) == 1:
        return f"{after_tokens[0]}, {before}"

    # NAME, LASTNAME INICIAL  (last word is 1 letter → it's an initial)
    if len(after_tokens[-1]) == 1:
        lastname = after_tokens[-2]
        middle_and_inicial = after_tokens[:-2] + [after_tokens[-1]]
        middle_str = " ".join(middle_and_inicial)
        return f"{lastname}, {before} {middle_str}".strip()

    # NAME, MEDIO LASTNAME  (last word is the lastname)
    lastname = after_tokens[-1]
    middle_tokens = after_tokens[:-1]
    if middle_tokens:
        return f"{lastname}, {before} {' '.join(middle_tokens)}"
    return f"{lastname}, {before}"


# ---------------------------------------------------------------------------
# I-5: THE, OR pattern
# THE, OR DALE GOUGE R  →  GOUGE, DALE R
# ---------------------------------------------------------------------------
def apply_i5(name: str) -> str:
    m = re.match(r"^THE,\s*OR\s+(.+)$", name.strip(), re.IGNORECASE)
    if not m:
        return name

    rest = m.group(1).strip()
    tokens = rest.split()

    if not tokens:
        return name

    # Last token is a single letter → it's an initial
    if len(tokens[-1]) == 1 and tokens[-1].isalpha():
        if len(tokens) >= 3:
            lastname = tokens[-2]
            name = tokens[0]
            middle = tokens[1:-2]
            parts = [name] + middle + [tokens[-1]]
            return f"{lastname}, {' '.join(parts)}"
        elif len(tokens) == 2:
            # THE, OR NAME INICIAL — not enough for lastname, leave
            return name
    else:
        # Last token is lastname
        lastname = tokens[-1]
        resto = tokens[:-1]
        return f"{lastname}, {' '.join(resto)}"

    return name


# ---------------------------------------------------------------------------
# I-6: THE-LASTNAME, OR INICIALES pattern
# THE-ROBERTS, OR JA  →  ROBERTS, JA
# ---------------------------------------------------------------------------
def apply_i6(name: str) -> str:
    m = re.match(r"^THE-(\w+),\s*OR\s+(.+)$", name.strip(), re.IGNORECASE)
    if not m:
        return name
    lastname = m.group(1).strip()
    iniciales = m.group(2).strip()
    return f"{lastname}, {iniciales}"


# ---------------------------------------------------------------------------
# I-7: FOR, pattern
# FOR, ELZIE TAYLOR A  →  TAYLOR, ELZIE A
# Same logic as I-5 but prefix is "FOR,"
# ---------------------------------------------------------------------------
def apply_i7(name: str) -> str:
    m = re.match(r"^FOR,\s*(.+)$", name.strip(), re.IGNORECASE)
    if not m:
        return name

    rest = m.group(1).strip()

    # "FOR, MOTHER- ATTY GEN" and similar legal junk → handled by I-2, skip here
    if re.match(r"^MOTHER", rest, re.IGNORECASE):
        return name

    tokens = rest.split()
    if not tokens:
        return name

    if len(tokens[-1]) == 1 and tokens[-1].isalpha():
        if len(tokens) >= 3:
            lastname = tokens[-2]
            name = tokens[0]
            middle = tokens[1:-2]
            parts = [name] + middle + [tokens[-1]]
            return f"{lastname}, {' '.join(parts)}"
    else:
        lastname = tokens[-1]
        resto = tokens[:-1]
        return f"{lastname}, {' '.join(resto)}"

    return name


# ---------------------------------------------------------------------------
# I-8: THE ESTATE OF / THE ESTAET OF (with typo)
# THE ESTATE OF JIMMY LEE EARLY JR  →  EARLY, JIMMY LEE JR
# ---------------------------------------------------------------------------
def apply_i8(name: str) -> str:
    m = re.match(r"^THE\s+ESTA[ET]{2}\s+OF\s+(.+)$", name.strip(), re.IGNORECASE)
    if not m:
        return name

    rest = m.group(1).strip()
    tokens = rest.split()

    if not tokens:
        return name

    # Check for suffix at end
    suffix = ""
    if tokens[-1].upper() in SUFFIXES:
        suffix = tokens[-1].upper()
        tokens = tokens[:-1]

    if not tokens:
        return name

    lastname = tokens[-1]
    name_parts = tokens[:-1]
    result = f"{lastname}, {' '.join(name_parts)}" if name_parts else lastname
    if suffix:
        result = f"{result} {suffix}"
    return result


# ---------------------------------------------------------------------------
# I-9: THE UNKNOWN HEIRS OR DEVISEES OF THE ESTATE OF [NAME], DECEASED
# →  LASTNAME, NAME
# ---------------------------------------------------------------------------
def apply_i9(name: str) -> str:
    m = re.match(
        r"^THE\s+UNKNOWN\s+HEIRS\s+OR\s+DEVISEES\s+OF\s+THE\s+ESTATE\s+OF\s+(.+?),?\s*DECEASED\s*$",
        name.strip(), re.IGNORECASE
    )
    if not m:
        return name

    inner = m.group(1).strip()
    # inner might be "JIMMY LEE EARLY" → apply same logic as I-8
    tokens = inner.split()
    if not tokens:
        return name

    lastname = tokens[-1]
    name_parts = tokens[:-1]
    return f"{lastname}, {' '.join(name_parts)}" if name_parts else lastname


# ---------------------------------------------------------------------------
# I-10: No comma — assume first token is lastname, rest is name
# WRIGHT JENNIFER  →  WRIGHT, JENNIFER
# Only applies when no other pattern matched
# ---------------------------------------------------------------------------
def apply_i10(name: str) -> str:
    if "," in name:
        return name  # already has comma structure
    tokens = name.strip().split()
    if len(tokens) < 2:
        return name  # single token, nothing to do
    lastname = tokens[0]
    name = " ".join(tokens[1:])
    return f"{lastname}, {name}"


# ---------------------------------------------------------------------------
# Master function: apply all I rules in sequence
# Returns (corrected_name, rule_applied) or (None, rule_applied) for delete
# ---------------------------------------------------------------------------
def apply_all_i_rules(name: str, extra_known: set[str] | None = None, db=None) -> tuple[str | None, str]:
    original = name

    # I-2 first — if it's junk, delete immediately
    result = apply_i2(name)
    if result is None:
        return None, "I-2"

    # I-9 and I-8 BEFORE I-3 — they need DECEASED and ESTATE intact to match
    if re.match(r"^THE\s+UNKNOWN\s+HEIRS\b", name, re.IGNORECASE):
        return apply_i9(name), "I-9"

    if re.match(r"^THE\s+ESTA[ET]{2}\s+OF\b", name, re.IGNORECASE):
        return apply_i8(name), "I-8"

    # I-3 — strip legal fragments (after estate/heirs patterns are handled)
    name = apply_i3(name)

    # MC prefix — MC, DADE WILLIE MAE → MCDADE, WILLIE MAE
    mc_result = apply_mc_prefix(name)
    if mc_result is not None:
        return mc_result, "I-MC"

    # Business indicator before comma → reclassify as B (raises ReclassifyAsB)
    apply_business_before_comma(name)

    # Business indicator after comma → swap order, keep I
    bac_result = apply_business_after_comma(name)
    if bac_result is not None:
        return bac_result, "I-BAC"

    # Single-token reclassify checks (game names, abbreviations, unknown names)
    check_single_token_reclassify(name, db)

    # Hyphenated business word in name position → ambiguous, flag for review
    check_hyphenated_business_before_comma(name)

    # I-6 — THE-LASTNAME, OR  (before I-5 to avoid prefix conflict)
    if re.match(r"^THE-\w+,\s*OR\b", name, re.IGNORECASE):
        return apply_i6(name), "I-6"

    # I-5 — THE, OR
    if re.match(r"^THE,\s*OR\b", name, re.IGNORECASE):
        return apply_i5(name), "I-5"

    # I-7 — FOR,
    if re.match(r"^FOR,", name, re.IGNORECASE):
        result = apply_i7(name)
        if result is None:
            return None, "I-7"
        return result, "I-7"

    # I-4 — inverted first names
    name = apply_i4(name, extra_known)

    # Maiden name appended at end: GARNER, DEBORAH MARGARET ROGERS → ROGERS-GARNER, DEBORAH MARGARET
    maiden = apply_maiden_name_rule(name, db)
    if maiden is not None:
        name = maiden

    # I-1 — suffix normalization (always apply)
    name = apply_i1(name)

    # I-10 — no comma fallback
    if "," not in name:
        name = apply_i10(name)

    # Return None if unchanged and original was already correct,
    # otherwise return corrected name
    rule = "none" if name == original else "I-1/I-4/I-10"
    return name, rule


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    tests = [
        # (rule, input, expected_output)
        ("I-1",  "CHAMBERS, GARY MADOX, JR",              "CHAMBERS, GARY MADOX JR"),
        ("I-2",  ",",                                       None),
        ("I-2",  ", ",                                      None),
        ("I-2",  "MOVANT, ",                               None),
        ("I-3",  "SMITH, IN REM ONLY HARRY",               "SMITH, HARRY"),
        ("I-3",  "RAY, LIENHOLDER IN REM ONLY JOE DEE",   "RAY, JOE DEE"),
        ("I-3",  "HOOGENDOORN, LARRY TRUSTEE W",           "HOOGENDOORN, LARRY W"),
        ("I-3",  "NEALE, IN REM JIM",                      "NEALE, JIM"),
        ("I-3",  "WHITE, MICHELLE MARIE INDIVIDUALLY",     "WHITE, MICHELLE MARIE"),
        ("I-4",  "CHERYL, WOODALL",                        "WOODALL, CHERYL"),
        ("I-4",  "JOHN, STOVER A",                         "STOVER, JOHN A"),
        ("I-4",  "JIMMY, LEE EARLY",                       "EARLY, JIMMY LEE"),
        ("I-4",  "JOHN, DAVID BARNES",                     "BARNES, JOHN DAVID"),
        ("I-5",  "THE, OR DALE GOUGE R",                   "GOUGE, DALE R"),
        ("I-5",  "THE, OR NANNETT SHIREY",                 "SHIREY, NANNETT"),
        ("I-5",  "THE, OR TROY EDWARD MARDIS",             "MARDIS, TROY EDWARD"),
        ("I-5",  "THE, OR DELBERT NEJMANOWSKI D",          "NEJMANOWSKI, DELBERT D"),
        ("I-6",  "THE-ROBERTS, OR JA",                     "ROBERTS, JA"),
        ("I-6",  "THE-ROBERTS, OR KJ",                     "ROBERTS, KJ"),
        ("I-7",  "FOR, ELZIE TAYLOR A",                    "TAYLOR, ELZIE A"),
        ("I-8",  "THE ESTATE OF JIMMY LEE EARLY JR",       "EARLY, JIMMY LEE JR"),
        ("I-8",  "THE ESTAET OF JIMMY LEE EARLY JR",       "EARLY, JIMMY LEE JR"),
        ("I-9",  "THE UNKNOWN HEIRS OR DEVISEES OF THE ESTATE OF JIMMY LEE EARLY, DECEASED",
                                                            "EARLY, JIMMY LEE"),
        ("I-10", "WRIGHT JENNIFER",                        "WRIGHT, JENNIFER"),
    ]

    passed = 0
    failed = 0
    print(f"{'Rule':<6} {'Result':<5} {'Input':<50} {'Expected'}")
    print("-" * 100)
    for rule, name, expected in tests:
        got, applied = apply_all_i_rules(name)
        ok = got == expected
        mark = "✓" if ok else "✗"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"{rule:<6} {mark}      {name:<50} {str(expected)}")
        if not ok:
            print(f"{'':>13} got: {got!r}")

    print(f"\n{passed}/{passed+failed} passed")