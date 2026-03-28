"""
main.py
Orchestrator — connects parser, classifier, rules_i, rules_b, and dedup.

Usage:
  python src/main.py data/input/FILE.txt
  python src/main.py data/input/FILE.txt --merge   (after Claude resolves flagged)

Flagged case behavior:
  - Any case with a flagged line → all other lines processed normally
  - Flagged line marked with >>> prefix in flagged.txt
  - Clean output excludes the entire case until --merge
  - On --merge: corrected cases → appended to end of clean file
  - On --merge: weird cases → original raw block written to FILENAME_weirdCases.txt
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from parser import parse_file, print_summary, Line, Case
from classifier import get_classifier
from rules_i import apply_all_i_rules, AmbiguousCase, ReclassifyAsB
from rules_b import apply_all_b_rules, FlagForReview
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
#   output_lines       : corrected lines ready for clean output (empty if any flagged)
#   flagged            : list of flagged dicts (empty if all clean)
#   raw_block          : original raw lines of this case (for weirdCases.txt)
#   flagged_block_lines: processed block with >>> on unresolvable lines
#                        (empty list if no flags)
# ---------------------------------------------------------------------------

def process_case(case: Case, clf) -> tuple[list[str], list[dict], list[str], list[str]]:
    lines, removed = deduplicate(case.lines)

    # Raw block = original lines of this case, used for weirdCases.txt
    raw_block = [l.raw for l in case.lines]

    # Find the header (02) line for context in flagged.json
    header_line = next(
        (l.raw.rstrip("\n") for l in case.lines if l.line_type == "02"),
        ""
    )

    corrected_lines: list[str] = []
    flagged_block_lines: list[str] = []  # for flagged.txt: processed + >>> markers
    flagged: list[dict] = []

    for line in lines:
        if not line.needs_processing:
            corrected_lines.append(line.raw)
            flagged_block_lines.append(line.raw)
            continue

        name = line.name
        marker = line.marker

        try:
            if marker == "I":
                db = clf.db if clf is not None else None
                corrected, rule = apply_all_i_rules(name, db=db)
                if corrected is None:
                    continue
                cl = rebuild_line(line, corrected)
                corrected_lines.append(cl)
                flagged_block_lines.append(cl)

            elif marker == "B":
                result, rule = apply_all_b_rules(name, clf)
                if result is None:
                    continue
                if isinstance(result, list):
                    for record in result:
                        cl = make_split_line(line, record["name"], record["marker"])
                        corrected_lines.append(cl)
                        flagged_block_lines.append(cl)
                elif isinstance(result, dict):
                    cl = make_split_line(line, result["name"], result["marker"])
                    corrected_lines.append(cl)
                    flagged_block_lines.append(cl)
                else:
                    cl = rebuild_line(line, result)
                    corrected_lines.append(cl)
                    flagged_block_lines.append(cl)

        except ReclassifyAsB as e:
            cl = rebuild_line(line, e.new_name, new_marker="B")
            corrected_lines.append(cl)
            flagged_block_lines.append(cl)

        except (AmbiguousCase, FlagForReview) as e:
            flagged.append({
                "case_number": case.case_number,
                "original_marker": marker,
                "original_name": name,
                "reason": str(e),
                "header_line": header_line,
                "flagged_line": line.raw.rstrip("\n"),
            })
            flagged_block_lines.append(">>>" + line.raw)

        except Exception as e:
            flagged.append({
                "case_number": case.case_number,
                "original_marker": marker,
                "original_name": name,
                "reason": f"ERROR: {e}",
                "header_line": header_line,
                "flagged_line": line.raw.rstrip("\n"),
            })
            flagged_block_lines.append(">>>" + line.raw)

    # If anything was flagged → exclude whole case from clean output
    if flagged:
        return [], flagged, raw_block, flagged_block_lines

    return corrected_lines, [], raw_block, []


# ---------------------------------------------------------------------------
# Merge corrections from Claude back into output
# ---------------------------------------------------------------------------

def _parse_flagged_txt(flagged_txt_path: Path) -> dict[str, list[str]]:
    """Parse flagged.txt into a dict of case_number → list of lines (with >>> intact)."""
    lookup: dict[str, list[str]] = {}
    if not flagged_txt_path.exists():
        return lookup
    with open(flagged_txt_path, encoding="utf-8") as f:
        raw = f.read()
    blocks = raw.split("\n\n")
    for block in blocks:
        block = block.strip("\n")
        if not block:
            continue
        lines = [l + "\n" for l in block.split("\n") if l]
        if lines:
            # Strip >>> prefix to extract case_number from field 2
            first_content = lines[0].lstrip(">")
            parts = first_content.split("\t")
            cn = parts[1].strip() if len(parts) > 1 else ""
            if cn and cn not in lookup:
                lookup[cn] = lines
    return lookup


def merge_corrections(input_path: Path, output_path: Path, flagged_path: Path, corrections_path: Path):
    """
    Read corrections JSON written by Claude.

    Each correction entry must have:
      case_number   : the case to handle
      flagged_line  : the original flagged line text (without >>>)
      action        : "replace" | "split" | "delete" | "weird"
      replacement_lines: list of corrected TSV lines (omit for weird)

    replace/split/delete → swap the >>> line, write complete block to clean file.
    weird              → write original raw block to data/flagged/STEM_weirdCases.txt.
    """
    if not corrections_path.exists():
        print(f"No corrections file found: {corrections_path}")
        return

    with open(corrections_path) as f:
        corrections: list[dict] = json.load(f)

    # Parse flagged.txt for processed blocks (>>> markers intact)
    flagged_txt_path = flagged_path.with_suffix(".txt")
    processed_lookup = _parse_flagged_txt(flagged_txt_path)

    # For weird cases: re-parse input file to get original raw blocks
    raw_lookup: dict[str, list[str]] = {}
    if any(str(c.get("action", "")) == "weird" for c in corrections):
        cases_orig, _ = parse_file(input_path)
        for c in cases_orig:
            raw_lookup[c.case_number] = [l.raw for l in c.lines]

    # Group corrections by case_number (a case may have multiple flagged lines)
    corrections_by_case: dict[str, list[dict]] = defaultdict(list)
    for c in corrections:
        corrections_by_case[str(c.get("case_number", ""))].append(c)

    resolved_blocks: list[list[str]] = []
    weird_blocks: list[list[str]] = []

    for cn, case_corrections in corrections_by_case.items():
        # If any correction for this case is weird → whole case goes to weirdCases.txt
        if any(c.get("action") == "weird" for c in case_corrections):
            raw = raw_lookup.get(cn, [])
            if raw:
                weird_blocks.append(raw)
            continue

        # Get the processed block from flagged.txt
        block = list(processed_lookup.get(cn, []))
        if not block:
            print(f"Warning: no flagged.txt block found for case {cn}")
            continue

        # Apply each correction to the block
        for correction in case_corrections:
            flagged_line = correction.get("flagged_line", "")
            action = correction.get("action", "weird")
            replacement_lines = correction.get("replacement_lines", [])

            # Find the >>> line matching this flagged_line
            target = ">>>" + flagged_line
            idx = None
            for i, bl in enumerate(block):
                if bl.rstrip("\n") == target:
                    idx = i
                    break

            if idx is None:
                print(f"Warning: could not find >>> line for case {cn}: {flagged_line[:60]}")
                continue

            # Apply action
            if action in ("replace", "split"):
                corrected = []
                for rl in replacement_lines:
                    if not rl.endswith("\n"):
                        rl += "\n"
                    corrected.append(rl)
                block[idx : idx + 1] = corrected
            elif action == "delete":
                del block[idx]
            # Unknown action: leave as-is (>>> line stays, will be visible in output)

        if block:
            resolved_blocks.append(block)

    # Append resolved blocks to clean file
    if resolved_blocks:
        with open(output_path, "a", encoding="utf-8") as f:
            for block in resolved_blocks:
                for line in block:
                    if not line.endswith("\n"):
                        line += "\n"
                    f.write(line)
        print(f"Appended {len(resolved_blocks)} resolved case(s) to {output_path.name}")

    # Write weird blocks to STEM_weirdCases.txt
    if weird_blocks:
        weird_path = flagged_path.parent / f"{input_path.stem}_weirdCases.txt"
        with open(weird_path, "a", encoding="utf-8") as f:
            for block in weird_blocks:
                for line in block:
                    if not line.endswith("\n"):
                        line += "\n"
                    f.write(line)
                f.write("\n")  # blank line between cases
        print(f"Wrote {len(weird_blocks)} unresolved case(s) to {weird_path.name}")

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
        merge_corrections(input_path, output_path, flagged_path, corrections_path)
        return

    clf = get_classifier("reference")

    print(f"Parsing {input_path.name}...")
    cases, orphans = parse_file(input_path)
    print_summary(cases, orphans, input_path)

    print("Processing cases...")
    all_output: list[str] = []
    all_flagged: list[dict] = []
    # Lookup: case_number → processed block with >>> markers (for flagged.txt)
    flagged_processed: dict[str, list[str]] = {}
    # Lookup: case_number → original raw block (not used in main output, kept for reference)
    flagged_raw: dict[str, list[str]] = {}

    for case in cases:
        out_lines, flagged, raw_block, flagged_block_lines = process_case(case, clf)
        all_output.extend(out_lines)
        all_flagged.extend(flagged)
        if flagged and case.case_number not in flagged_processed:
            flagged_processed[case.case_number] = flagged_block_lines
            flagged_raw[case.case_number] = raw_block

    for orphan in orphans:
        all_output.append(orphan.raw)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(all_output)

    with open(flagged_path, "w", encoding="utf-8") as f:
        json.dump(all_flagged, f, indent=2, ensure_ascii=False)

    # Write flagged.txt: processed blocks with >>> on unresolvable lines
    flagged_txt_path = flagged_dir / f"{stem}_flagged.txt"
    unique_blocks = list(flagged_processed.values())
    if unique_blocks:
        with open(flagged_txt_path, "w", encoding="utf-8") as f:
            for i, block in enumerate(unique_blocks):
                f.writelines(block)
                if i < len(unique_blocks) - 1:
                    f.write("\n")

    total_in  = sum(len(c.lines) for c in cases)
    total_out = len(all_output)
    flagged_cases = len({e["case_number"] for e in all_flagged})

    print(f"\n{'='*50}")
    print(f"Input lines   : {total_in}")
    print(f"Output lines  : {total_out}")
    print(f"Difference    : {total_out - total_in:+d}")
    print(f"Flagged cases : {flagged_cases} (flagged lines marked >>> in flagged.txt)")
    print(f"\nOutput  -> {output_path}")
    print(f"Flagged -> {flagged_path}")
    if all_flagged:
        print(f"        -> {flagged_txt_path}")
    if all_flagged:
        print(f"\nNext step: open Claude Code and run /resolve {stem}")
    else:
        print("\nNo flagged cases — processing complete.")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
