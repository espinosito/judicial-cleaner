Spot-check the output file at data/output/$ARGUMENTS_clean.txt.

Steps:
1. Sample 20 random corrected records (records that differ from input)
2. For each sampled record show: original line → corrected line → rule applied
3. Check that no field other than NAME and MARKER was modified
4. Check that IB markers are all unchanged
5. Check that lines with fewer than 6 fields are unchanged
6. Report: X of 20 look correct, list any that seem wrong with reason

Do not modify any file. Report only.
```

---

## How to start Claude Code once everything is set up

Open a terminal, navigate to your project folder, and run:
```
cd judicial-cleaner
claude
```

Claude Code opens an interactive session rooted in that folder. Your first message to it will be:
```
Read CLAUDE.md and confirm you're ready.
Then run /analyze ChtxGrayson_1988.txt