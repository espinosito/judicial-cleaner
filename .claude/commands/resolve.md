Resolve flagged cases from data/flagged/$ARGUMENTS_flagged.json.

Steps:
1. Read the flagged JSON file — each entry has: case_number, original_marker,
   original_name, reason, and raw_block (the full original TSV lines)
2. Read rules/individuals.md, rules/businesses.md, rules/special_cases.md 
   ONCE at the start — do not re-read between cases
3. For each unique case_number in the flagged list:
   a. Show the raw_block so you can see the full case context
   b. Apply the appropriate rule
   c. If you can confidently correct it → set action "resolved" and provide
      the corrected_block (full corrected TSV lines for that case)
   d. If you still cannot decide → set action "weird"

4. Write ALL decisions to data/flagged/$ARGUMENTS_corrections.json

Corrections format — one entry per unique case_number:
[
  {
    "case_number": "883763",
    "action": "resolved",
    "corrected_block": [
      "19881207\t883763    \tJDG\t02\tTAX CASES\t\t\n",
      "19881207\t883763    \tJDG\t04\tI\tCORNWELL, LORENE\t\n",
      "19881207\t883763    \tJDG\t05\tB\tPOTTSBORO ISD\t\n"
    ]
  },
  {
    "case_number": "881999",
    "action": "weird"
  }
]

Rules:
- "resolved" → corrected_block must be the COMPLETE corrected case (all lines)
- "weird"    → no corrected_block needed, raw original goes to FILENAME_weirdCases.txt
- Never guess. If genuinely unclear → use "weird"
- Preserve exact tab structure of each line
- Do not add explanatory text inside corrected_block lines