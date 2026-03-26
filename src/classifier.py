"""
classifier.py
Loads name databases and classifies a name as I (person), B (business),
or AMBIGUOUS (needs Claude review).
"""
from __future__ import annotations

import csv
import re
import zipfile
from pathlib import Path

HARD_BUSINESS_SUFFIXES = {
    "INC", "LLC", "LTD", "LP", "PC", "CORP", "CORPORATION",
    "LLP", "FSB", "NA", "CO", "PLC",
}

HARD_PERSONAL_SUFFIXES = {
    "JR", "SR", "II", "III", "IV", "MD", "PA", "DDS", "PHD", "ESQ",
}

BUSINESS_INDICATORS = {
    "INC", "INCORPORATED", "CORPORATION", "CORP", "GROUP", "LIMITED",
    "LTD", "DISCOUNT", "REALTORS", "ASSOC", "ASSOCIATION", "ASSOCIATES",
    "PARTNERS", "DEVELOPMENT", "INSURANCE", "INSUR", "LLP", "LLC",
    "MANAGEMENT", "MGMT", "SUPPLY", "SUPPLIES", "LABORATORY",
    "LABORATORIES", "LABOR", "SCHOOL", "DISTRICT", "THRIFT", "STORE",
    "SYSTEM", "EQUIPMENT", "EMPLOYEES", "HEALTH", "HEALTHCARE", "SOCIETY",
    "SOCIAL", "CLEANERS", "CLEANING", "FOOD", "CENTER", "QUALITY",
    "WAREHOUSE", "LANDSCAPE", "PURCHASE", "EXCAVATING", "COMPANY",
    "REPUBLIC", "NATIONAL", "REGIONAL", "RECEIVABLE", "APARTMENTS",
    "APTS", "PROPERTY", "PROPERTIES", "COMMUNICATIONS", "LUMBER",
    "DEPT", "DEPARTMENT", "SHOP", "CONSTRUCTION", "CONST", "CAFE",
    "RESTORATION", "MEDICAL", "PLUMBING", "SURGERY", "WHOLESALE",
    "BANK", "ENTERPRISES", "SERVICES", "INDUSTRIES", "INDUSTRIAL",
    "ELECTRIC", "INVESTMENTS", "FINANCIAL", "FINANCE", "ATTORNEY",
    "OFFICE", "RESTAURANT", "TRANSMISSION", "TRANSPORT", "TRANSPORTATION",
    "GOLF", "DESIGN", "PROFESSIONAL", "CONTRACTING", "PRODUCTION",
    "SPECIALIST", "RESOURCE", "ADVERTISING", "AUTHORITY", "GLOBAL",
    "INFORMATION", "PHOTOGRAPHY", "CONDOMINIUM", "DENTAL", "HOUSING",
    "INSTITUTE", "CLINIC", "REHABILITATION", "COMMUNITY", "MORTGAGE",
    "CAPITAL", "ACQUISITION", "FOUNDATION", "SOLUTIONS", "BANCORP",
    "COUNTY", "METRO", "PAINTING", "CHIROPRACTIC", "HOSPITAL",
    "MEMORIAL", "ROOFING", "PETROLEUM", "AUTOMOTIVE", "ELECTRONICS",
    "NETWORK", "RETIREMENT", "SYSTEMS", "EXCHANGE", "PARTNERSHIP",
    "CONCRETE", "MARKETING", "COMMERCIAL", "PROCESSING", "CORPORATE",
    "FREIGHT", "PHARMACY", "COUNTRY", "FACTORY", "DAYCARE", "CARPET",
    "RECYCLING", "TOWING", "CONSULTING", "TRUCKING", "TECHNICAL",
    "FEDERAL", "SALON", "BASEBALL", "MOTOR", "TRAILER",
    "SEAFOOD", "BEVERAGE", "PROTECTION", "DISTRIBUTING", "BOUTIQUE",
    "HOMEOWNERS", "WASTEWATER", "ENFORCEMENT",
    "VENTURE", "VENTURES", "GARDENING", "IMPORTS", "RADIOLOGY",
    "SUPERMARKET", "MERCHANDISING", "GARDENS", "RENTALS", "REALTY",
    "TITLE", "REPAIRS", "UTILITY", "SPORTS", "PRODUCTIONS",
    "ISD", "CBIC", "ESD", "DHCS", "VFW",
    "STATE", "CITY", "OF",
}

WEAK_BUSINESS_WORDS = {"OF", "STATE", "CITY", "AND"}

# Words the SSA has as first names but are NEVER person first names in this context
NEVER_FIRST_NAME = {
    "TEXAS", "OREGON", "WASHINGTON", "CALIFORNIA", "FLORIDA", "GEORGIA",
    "VIRGINIA", "CAROLINA", "INDIANA", "ILLINOIS", "KENTUCKY", "LOUISIANA",
    "AMERICA", "AMERICAN", "NATIONAL", "FEDERAL", "UNITED", "STATES",
    "COUNTY", "DISTRICT", "CITY", "STATE", "NORTH", "SOUTH", "EAST", "WEST",
    "CENTRAL", "GENERAL", "REGIONAL", "MEMORIAL", "HOSPITAL", "BANK",
    "FIRST", "SECOND", "THIRD", "NEW", "OLD", "GREAT", "GRAND",
}


class NameDatabase:
    def __init__(self, reference_dir="reference"):
        self.reference_dir = Path(reference_dir)
        self.first_names = set()
        self._loaded = False

    def load(self):
        if self._loaded:
            return
        count = 0

        self._load_ssa_zip()
        print(f"  SSA names loaded       : {len(self.first_names) - count:,}")

        count = len(self.first_names)
        self._load_spanish_csv("nombres_es_hombres.csv", col=0)
        self._load_spanish_csv("nombres_es_mujeres.csv", col=0)
        print(f"  Spanish names loaded   : {len(self.first_names) - count:,}")

        count = len(self.first_names)
        self._load_hispanic_csv()
        print(f"  Hispanic names loaded  : {len(self.first_names) - count:,}")

        count = len(self.first_names)
        self._load_known_names()
        print(f"  Known names loaded     : {len(self.first_names) - count:,}")

        print(f"  Total unique names     : {len(self.first_names):,}")
        self._loaded = True

    def _load_ssa_zip(self):
        names_dir = self.reference_dir / "names"
        if names_dir.exists():
            for txt_file in names_dir.glob("yob*.txt"):
                with open(txt_file, encoding="utf-8", errors="replace") as f:
                    for line in f:
                        parts = line.strip().split(",")
                        if parts:
                            self.first_names.add(parts[0].upper())
            return
        zip_path = self.reference_dir / "names.zip"
        if zip_path.exists():
            with zipfile.ZipFile(zip_path) as zf:
                for entry in zf.namelist():
                    if entry.endswith(".txt"):
                        with zf.open(entry) as f:
                            for line in f:
                                parts = line.decode("utf-8").strip().split(",")
                                if parts:
                                    self.first_names.add(parts[0].upper())

    def _load_spanish_csv(self, filename, col=0):
        path = self.reference_dir / filename
        if not path.exists():
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            sample = f.read(512)
            f.seek(0)
            sep = ";" if sample.count(";") > sample.count(",") else ","
            reader = csv.reader(f, delimiter=sep)
            for row in reader:
                if row and len(row) > col:
                    name = row[col].strip().upper()
                    if name and name.isalpha():
                        self.first_names.add(name)

    def _load_hispanic_csv(self):
        path = self.reference_dir / "nombres_hispanic.csv"
        if not path.exists():
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 1:
                    name = row[1].strip().upper()
                    if name and name.isalpha():
                        self.first_names.add(name)

    def _load_known_names(self):
        path = self.reference_dir / "known_first_names.txt"
        if not path.exists():
            return
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                name = line.strip().upper()
                if name and name.isalpha():
                    self.first_names.add(name)

    def is_first_name(self, token):
        t = token.upper()
        return t in self.first_names and t not in NEVER_FIRST_NAME


class Classifier:
    def __init__(self, db):
        self.db = db

    def classify(self, name):
        if not name or not name.strip():
            return self._result("I", "high", 0, 0, ["empty name"])

        tokens = self._tokenize(name)
        reasons = []
        person_score = 0
        business_score = 0

        # Layer 1 — hard business suffix on last token
        if tokens and tokens[-1] in HARD_BUSINESS_SUFFIXES:
            reasons.append(f"hard business suffix: {tokens[-1]}")
            return self._result("B", "high", 0, 10, reasons)

        # Hard business token anywhere (excluding weak words)
        for t in tokens:
            if t in HARD_BUSINESS_SUFFIXES and t not in WEAK_BUSINESS_WORDS:
                reasons.append(f"hard business token: {t}")
                return self._result("B", "high", 0, 10, reasons)

        # Layer 2 — hard personal suffix on last token
        if tokens and tokens[-1] in HARD_PERSONAL_SUFFIXES:
            reasons.append(f"hard personal suffix: {tokens[-1]}")
            return self._result("I", "high", 10, 0, reasons)

        # Layer 3 — first name database
        if "," in name:
            after_comma = name.split(",", 1)[1]
            after_tokens = self._tokenize(after_comma)
            for t in after_tokens:
                if len(t) > 1 and self.db.is_first_name(t):
                    person_score += 3
                    reasons.append(f"first name after comma: {t}")
                    break
        else:
            meaningful = [t for t in tokens if len(t) > 1 and t.isalpha()]
            for t in meaningful[1:]:
                if self.db.is_first_name(t):
                    person_score += 3
                    reasons.append(f"first name found: {t}")
                    break
            if meaningful and self.db.is_first_name(meaningful[0]):
                person_score += 1
                reasons.append(f"first token is first name: {meaningful[0]}")

        # Layer 4 — business keyword density
        strong = [t for t in tokens if t in BUSINESS_INDICATORS and t not in WEAK_BUSINESS_WORDS]
        weak   = [t for t in tokens if t in WEAK_BUSINESS_WORDS]
        # Strong institutional words (HOSPITAL, BANK, SCHOOL, etc.) get +3 each
        # because they almost never appear in personal names
        INSTITUTIONAL = {
            "HOSPITAL", "BANK", "SCHOOL", "DISTRICT", "COUNTY", "MEMORIAL",
            "INSTITUTE", "UNIVERSITY", "CHURCH", "DEPARTMENT", "DEPT",
            "ASSOCIATION", "FOUNDATION", "AUTHORITY", "COMMISSION",
            "ISD", "ESD",
        }
        for kw in strong:
            weight = 3 if kw in INSTITUTIONAL else 2
            business_score += weight
        business_score += len(weak) * 1
        if strong:
            reasons.append(f"business keywords: {strong}")
        if weak:
            reasons.append(f"weak business words: {weak}")

        # Layer 5 — structural heuristics
        if "," in name:
            before = name.split(",")[0].strip().split()
            if len(before) == 1:
                # Stronger signal: LASTNAME, NAME is the canonical person format
                person_score += 3
                reasons.append("single token before comma (canonical person format)")

        # Initials only count as person signal when name has a comma
        # (in long names without comma, initials are unreliable)
        initials = [t for t in tokens if len(t) == 1 and t.isalpha()]
        if initials and "," in name:
            person_score += 2
            reasons.append(f"has middle initial: {initials}")

        if len(tokens) >= 5 and "," not in name:
            business_score += 1
            reasons.append("long name without comma")

        # Decision
        diff = person_score - business_score
        if diff >= 3:
            return self._result("I", "high", person_score, business_score, reasons)
        elif diff <= -2:
            return self._result("B", "high", person_score, business_score, reasons)
        else:
            return self._result("AMBIGUOUS", "low", person_score, business_score, reasons)

    def _tokenize(self, name):
        return [t.upper() for t in re.split(r"[\s,]+", name) if t.strip()]

    def _result(self, result, confidence, ps, bs, reasons):
        return {
            "result": result,
            "confidence": confidence,
            "person_score": ps,
            "business_score": bs,
            "reasons": reasons,
        }


_db = None
_classifier = None

def get_classifier(reference_dir="reference"):
    global _db, _classifier
    if _classifier is None:
        print("Loading name databases...")
        _db = NameDatabase(reference_dir)
        _db.load()
        _classifier = Classifier(_db)
        print("Classifier ready.\n")
    return _classifier


if __name__ == "__main__":
    import sys
    ref = sys.argv[1] if len(sys.argv) > 1 else "reference"
    clf = get_classifier(ref)

    test_names = [
        ("I", "CORNWELL, LORENE"),
        ("I", "PULLIAM, GORDON C"),
        ("I", "SPINDLE, BILLY CARL"),
        ("I", "GARCIA, PAULA DENISE"),
        ("I", "MILLS JAMES E"),
        ("B", "ISD POTTSBORO"),
        ("B", "TEXAS STATE OF"),
        ("B", "HOSPITAL WILSON N JONES MEMORIAL"),
        ("B", "CO CONSTRUCTION"),
        ("B", "GRAYSON COUNTY OF"),
        ("B", "BANK GRAYSON COUNTY STATE"),
        ("B", "PARTNERSHIP STEEPLECHASE COUNTY ESTATES A LIMITED"),
        ("B", "CORP COMMTRON CORPORATION AND EMERSON RADIO"),
        ("B", "COMPANY GILLORD-HILL AND"),
        ("?", "CARSON JEFFREY AND WALKER STEVE"),
        ("?", "YOUNG MARSHA AND DAVID"),
        ("?", "MILLS JAMES E AND WIFE LINDA D MILLS"),
    ]

    print(f"{'Exp':<5} {'Got':<12} {'P':>4} {'B':>4}  Name")
    print("-" * 72)
    correct = 0
    definite = 0
    for expected, name in test_names:
        r = clf.classify(name)
        result = r["result"]
        if expected != "?":
            definite += 1
            ok = result == expected
            if ok:
                correct += 1
            mark = "✓" if ok else "✗"
        else:
            mark = "~"
        print(f"{mark} {expected:<4} {result:<12} {r['person_score']:>4} {r['business_score']:>4}  {name}")
        if result != expected or result == "AMBIGUOUS":
            for reason in r["reasons"]:
                print(f"{'':>32} → {reason}")

    print(f"\n{correct}/{definite} correct on definite cases")