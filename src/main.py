"""
main.py
Orchestrator — connects parser, classifier, rules_i, rules_b, and dedup.

Usage:
  python src/main.py data/input/FILE.txt
  python src/main.py data/input/FILE.txt --merge   (after Claude resolves flagged)

Flagged case behavior:
  - Any case with a flagged line → entire case block removed from clean output
  - On --merge: resolved cases → appended to end of clean file
  - On --merge: unresolved cases → written to data/flagged/weirdCases.txt
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parser import parse_file, print_summary, Line, Case
from classifier import get_classifier
from rules_i import apply_all_i_rules, AmbiguousCase
from rules_b import apply_all_b_rules
from dedup import deduplicate


# ---------------------------------------------------------------------------
# Output line builder
# ---------------------------------------------------------------------------

def rebuild_line(original: Line, new_name: str, new_marker: str | None = None) -> str:
    fields = list(original.fields)
    if len(fields) > 5:
        fields[5] = new_name
    else:
        while len(fields) <= 5:
            fields.append("")
        fields[5] = new_name
    if new_marker is not None and len(fields) > 4:
        fields[4] = new_marker
    result = "\t".join(fields)
    if not result.endswith("\n"):
        result += "\n"
    return result


def make_split_line(original: Line, new_name: str, new_marker: str) -> str:
    fields = list(original.fields)
    if len(fields) > 4:
        fields[4] = new_marker
    if len(fields) > 5:
        fields[5] = new_name
    result = "\t".join(fields)
    if not result.endswith("\n"):
        result += "\n"
    return result


# ---------------------------------------------------------------------------
# Process a single case
# Returns:
#   output_lines : corrected lines (empty if any line was flagged)
#   flagged      : list of flagged dicts (empty if all clean)
#   raw_block    : original raw lines of this case (for exclusion/restore)
# ---------------------------------------------------------------------------

def process_case(case: Case, clf) -> tuple[list[str], list[dict], list[str]]:
    lines, removed = deduplicate(case.lines)

    # Raw block = original lines of this case, used if we need to write to weirdCases
    raw_block = [l.raw for l in case.lines]

    corrected_lines: list[str] = []
    flagged: list[dict] = []

    for line in lines:
        if not line.needs_processing:
            corrected_lines.append(line.raw)
            continue

        name = line.name
        marker = line.marker

        try:
            if marker == "I":
                corrected, rule = apply_all_i_rules(name)
                if corrected is None:
                    continue
                corrected_lines.append(rebuild_line(line, corrected))

            elif marker == "B":
                result, rule = apply_all_b_rules(name, clf)
                if result is None:
                    continue
                if isinstance(result, list):
                    for record in result:
                        corrected_lines.append(
                            make_split_line(line, record["name"], record["marker"])
                        )
                elif isinstance(result, dict):
                    corrected_lines.append(
                        make_split_line(line, result["name"], result["marker"])
                    )
                else:
                    corrected_lines.append(rebuild_line(line, result))

        except AmbiguousCase as e:
            flagged.append({
                "case_number": case.case_number,
                "original_marker": marker,
                "original_name": name,
                "reason": str(e),
                "raw_block": raw_block,
            })

        except Exception as e:
            flagged.append({
                "case_number": case.case_number,
                "original_marker": marker,
                "original_name": name,
                "reason": f"ERROR: {e}",
                "raw_block": raw_block,
            })

    # If anything was flagged → exclude the whole case from clean output
    if flagged:
        return [], flagged, raw_block

    return corrected_lines, [], raw_block


# ---------------------------------------------------------------------------
# Merge corrections from Claude back into output
# ---------------------------------------------------------------------------

def merge_corrections(output_path: Path, flagged_path: Path, corrections_path: Path):
    """
    Read corrections JSON written by Claude.

    Each correction entry must have:
      case_number    : the case to handle
      action         : "resolved" | "weird"
      corrected_block: list of corrected TSV line strings (only for "resolved")

    Resolved cases → appended to end of clean file.
    Weird cases    → written to data/flagged/weirdCases.txt (raw original block).
    """
    if not corrections_path.exists():
        print(f"No corrections file found: {corrections_path}")
        return

    with open(corrections_path) as f:
        corrections: list[dict] = json.load(f)

    with open(flagged_path) as f:
        flagged: list[dict] = json.load(f)

    # Build lookup: case_number → raw_block (for weird cases)
    raw_lookup: dict[str, list[str]] = {}
    for entry in flagged:
        cn = entry["case_number"]
        if cn not in raw_lookup:
            raw_lookup[cn] = entry.get("raw_block", [])

    resolved_blocks: list[list[str]] = []
    weird_blocks: list[list[str]] = []

    for c in corrections:
        cn = str(c.get("case_number", ""))
        action = c.get("action", "weird")

        if action == "resolved":
            block = c.get("corrected_block", [])
            if block:
                resolved_blocks.append(block)
        else:
            # weird — use original raw block
            raw = raw_lookup.get(cn, [])
            if raw:
                weird_blocks.append(raw)

    # Append resolved blocks to clean file
    if resolved_blocks:
        with open(output_path, "a", encoding="utf-8") as f:
            for block in resolved_blocks:
                for line in block:
                    if not line.endswith("\n"):
                        line += "\n"
                    f.write(line)
        print(f"Appended {len(resolved_blocks)} resolved case(s) to {output_path.name}")

    # Write weird blocks to weirdCases.txt
    if weird_blocks:
        weird_path = output_path.parent.parent / "flagged" / "weirdCases.txt"
        with open(weird_path, "a", encoding="utf-8") as f:
            for block in weird_blocks:
                for line in block:
                    if not line.endswith("\n"):
                        line += "\n"
                    f.write(line)
                f.write("\n")  # blank line between cases
        print(f"Wrote {len(weird_blocks)} unresolved case(s) to weirdCases.txt")

    if not resolved_blocks and not weird_blocks:
        print("Nothing to merge.")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/main.py data/input/FILE.txt [--merge]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    do_merge = "--merge" in sys.argv

    if not input_path.exists():
        print(f"File not found: {input_path}")
        sys.exit(1)

    stem = input_path.stem
    output_dir = Path("data/output")
    flagged_dir = Path("data/flagged")
    output_dir.mkdir(parents=True, exist_ok=True)
    flagged_dir.mkdir(parents=True, exist_ok=True)

    output_path  = output_dir / f"{stem}_clean.txt"
    flagged_path = flagged_dir / f"{stem}_flagged.json"
    corrections_path = flagged_dir / f"{stem}_corrections.json"

    if do_merge:
        print(f"Merging corrections into {output_path.name}...")
        merge_corrections(output_path, flagged_path, corrections_path)
        return

    clf = get_classifier("reference")

    print(f"Parsing {input_path.name}...")
    cases, orphans = parse_file(input_path)
    print_summary(cases, orphans, input_path)

    print("Processing cases...")
    all_output: list[str] = []
    all_flagged: list[dict] = []

    for case in cases:
        out_lines, flagged, raw_block = process_case(case, clf)
        all_output.extend(out_lines)
        all_flagged.extend(flagged)

    for orphan in orphans:
        all_output.append(orphan.raw)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(all_output)

    with open(flagged_path, "w", encoding="utf-8") as f:
        json.dump(all_flagged, f, indent=2, ensure_ascii=False)

    total_in  = sum(len(c.lines) for c in cases)
    total_out = len(all_output)
    flagged_cases = len({e["case_number"] for e in all_flagged})

    print(f"\n{'='*50}")
    print(f"Input lines   : {total_in}")
    print(f"Output lines  : {total_out}")
    print(f"Difference    : {total_out - total_in:+d}")
    print(f"Flagged cases : {flagged_cases} (entire blocks excluded from output)")
    print(f"\nOutput  → {output_path}")
    print(f"Flagged → {flagged_path}")
    if all_flagged:
        print(f"\nNext step: open Claude Code and run /resolve {stem}")
    else:
        print("\nNo flagged cases — processing complete.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()