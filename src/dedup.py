"""
dedup.py
Deduplication within a case block (same case_number).
Rules from prompt:
  - Remove exact duplicate rows, keep first occurrence
  - Exception: two records differing only by suffix (JR vs no suffix) are NOT duplicates
"""
from __future__ import annotations
import re


SUFFIXES = {"JR", "SR", "II", "III", "IV"}


def _normalize_for_dedup(name: str) -> str:
    """
    Strip trailing suffixes so we can compare the base name.
    EARLY, JIMMY LEE JR  →  EARLY, JIMMY LEE
    EARLY, JIMMY LEE     →  EARLY, JIMMY LEE
    """
    tokens = name.strip().split()
    if tokens and tokens[-1].upper() in SUFFIXES:
        return " ".join(tokens[:-1]).strip()
    return name.strip()


def deduplicate(lines: list) -> tuple[list, int]:
    """
    Given all lines of a case, return (deduplicated_lines, removed_count).
    Only I and B lines are deduplicated. All other lines pass through unchanged.
    Comparison is on (marker, normalized_name) — case-insensitive.
    """
    seen: set[tuple[str, str]] = set()
    result = []
    removed = 0

    for line in lines:
        # Only deduplicate processable I and B lines
        if not line.needs_processing:
            result.append(line)
            continue

        marker = line.marker.upper()
        name = line.name.strip().upper()
        base_name = _normalize_for_dedup(name)
        has_suffix = name != base_name

        # A record is a duplicate only if EXACT full name already seen
        full_key = (marker, name)

        if full_key in seen:
            removed += 1  # exact duplicate
        else:
            seen.add(full_key)
            # Also register the base name — but ONLY if this record has no suffix.
            # If it has a suffix (JR), we do NOT block the base name,
            # so that EARLY, JIMMY LEE (no suffix) can still be kept later.
            if not has_suffix:
                seen.add((marker, base_name))
            result.append(line)

    return result, removed


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from dataclasses import dataclass, field

    @dataclass
    class FakeLine:
        marker: str
        name: str
        raw: str = ""
        line_number: int = 0

        @property
        def needs_processing(self):
            return self.marker in ("I", "B")

        @property
        def is_short(self):
            return False

    tests = [
        {
            "desc": "exact duplicate removed",
            "lines": [
                FakeLine("I", "SMITH, JOHN"),
                FakeLine("I", "SMITH, JOHN"),
            ],
            "expected_count": 1,
            "expected_removed": 1,
        },
        {
            "desc": "JR vs no suffix are NOT duplicates",
            "lines": [
                FakeLine("I", "EARLY, JIMMY LEE JR"),
                FakeLine("I", "EARLY, JIMMY LEE"),
            ],
            "expected_count": 2,
            "expected_removed": 0,
        },
        {
            "desc": "different markers not deduped",
            "lines": [
                FakeLine("I", "SMITH, JOHN"),
                FakeLine("B", "SMITH, JOHN"),
            ],
            "expected_count": 2,
            "expected_removed": 0,
        },
        {
            "desc": "three lines, one duplicate",
            "lines": [
                FakeLine("I", "JONES, MARY"),
                FakeLine("I", "JONES, MARY"),
                FakeLine("I", "JONES, MARY ANN"),
            ],
            "expected_count": 2,
            "expected_removed": 1,
        },
        {
            "desc": "case insensitive",
            "lines": [
                FakeLine("I", "SMITH, JOHN"),
                FakeLine("I", "smith, john"),
            ],
            "expected_count": 1,
            "expected_removed": 1,
        },
    ]

    passed = 0
    for t in tests:
        result, removed = deduplicate(t["lines"])
        ok = len(result) == t["expected_count"] and removed == t["expected_removed"]
        mark = "✓" if ok else "✗"
        if ok:
            passed += 1
        print(f"{mark} {t['desc']}")
        if not ok:
            print(f"  expected {t['expected_count']} lines, {t['expected_removed']} removed")
            print(f"  got      {len(result)} lines, {removed} removed")

    print(f"\n{passed}/{len(tests)} passed")