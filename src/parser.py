"""
parser.py
Reads a judicial TSV file and groups lines into Case objects by case_number.

Field map (1-indexed):
  1  date         e.g. 19881207
  2  case_number  e.g. 883763
  3  court_type   e.g. JDG, DIV
  4  line_type    e.g. 02, 04, 05
  5  marker       e.g. I, B, IB  (may be empty)
  6  name         e.g. CORNWELL, LORENE  (may be empty)
"""

from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, field


@dataclass
class Line:
    raw: str            # original line exactly as read, including \n
    fields: list[str]   # all fields after splitting on tab
    line_number: int     # 1-based line number in source file

    @property
    def date(self) -> str:
        return self.fields[0].strip() if len(self.fields) > 0 else ""

    @property
    def case_number(self) -> str:
        return self.fields[1].strip() if len(self.fields) > 1 else ""

    @property
    def court_type(self) -> str:
        return self.fields[2].strip() if len(self.fields) > 2 else ""

    @property
    def line_type(self) -> str:
        return self.fields[3].strip() if len(self.fields) > 3 else ""

    @property
    def marker(self) -> str:
        return self.fields[4].strip() if len(self.fields) > 4 else ""

    @property
    def name(self) -> str:
        return self.fields[5].strip() if len(self.fields) > 5 else ""

    @property
    def is_short(self) -> bool:
        """Lines with fewer than 6 fields — never touch these."""
        return len(self.fields) < 6

    @property
    def is_header(self) -> bool:
        """Line type 02 — block header, never touch."""
        return self.line_type == "02"

    @property
    def is_skippable(self) -> bool:
        """IB marker, short lines, headers — leave exactly as-is."""
        return self.marker == "IB" or self.is_short or self.is_header

    @property
    def needs_processing(self) -> bool:
        return self.marker in ("I", "B") and not self.is_short


@dataclass
class Case:
    case_number: str
    lines: list[Line] = field(default_factory=list)

    def add_line(self, line: Line):
        self.lines.append(line)

    @property
    def i_lines(self) -> list[Line]:
        return [l for l in self.lines if l.marker == "I" and not l.is_short]

    @property
    def b_lines(self) -> list[Line]:
        return [l for l in self.lines if l.marker == "B" and not l.is_short]

    def __repr__(self):
        return (f"Case({self.case_number!r}, "
                f"{len(self.lines)} lines, "
                f"{len(self.i_lines)}xI, "
                f"{len(self.b_lines)}xB)")


def parse_file(filepath: str | Path) -> tuple[list[Case], list[Line]]:
    """
    Read a TSV file and return:
      - cases: list of Case objects, each with all their lines, in file order
      - orphans: lines that have no case_number (should not happen, but safe)

    Lines are never reordered or modified. Each Line keeps its raw original.
    Cases preserve the order they first appear in the file.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    cases: dict[str, Case] = {}   # case_number -> Case, insertion-ordered
    orphans: list[Line] = []

    with open(filepath, encoding="utf-8", errors="replace") as fh:
        for line_number, raw in enumerate(fh, start=1):
            fields = raw.rstrip("\n").split("\t")
            line = Line(raw=raw, fields=fields, line_number=line_number)

            cn = line.case_number
            if not cn:
                orphans.append(line)
                continue

            if cn not in cases:
                cases[cn] = Case(case_number=cn)
            cases[cn].add_line(line)

    return list(cases.values()), orphans


def print_summary(cases: list[Case], orphans: list[Line], filepath: Path):
    """Print a human-readable summary of what was parsed."""
    total_lines = sum(len(c.lines) for c in cases) + len(orphans)
    total_i = sum(len(c.i_lines) for c in cases)
    total_b = sum(len(c.b_lines) for c in cases)

    print(f"\n{'='*50}")
    print(f"File     : {filepath.name}")
    print(f"Cases    : {len(cases)}")
    print(f"Lines    : {total_lines}")
    print(f"  I      : {total_i}")
    print(f"  B      : {total_b}")
    print(f"  Other  : {total_lines - total_i - total_b}")
    if orphans:
        print(f"  Orphans: {len(orphans)}")
    print(f"{'='*50}\n")


if __name__ == "__main__":
    import sys
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/input/ChtxGrayson_1988.txt")
    cases, orphans = parse_file(path)
    print_summary(cases, orphans, path)

    # Show first 3 cases as a sanity check
    print("First 3 cases:")
    for case in cases[:3]:
        print(f"\n  {case}")
        for line in case.lines:
            marker = f"[{line.marker}]" if line.marker else "[  ]"
            name = line.name or "(no name)"
            print(f"    {line.line_type} {marker:6} {name}")