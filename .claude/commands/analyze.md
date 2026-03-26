Pre-scan the file at data/input/$ARGUMENTS before running the pipeline.

Steps:
1. Count total lines, unique case_numbers, and breakdown by marker (I, B, IB, 02)
2. Extract all unique B names and list any that have no match in
   BUSINESS_INDICATORS and no known suffix (INC, LLC, etc.)
3. Extract all unique I names with no comma and check if any token
   before a space could be an inverted first name not in known_first_names.txt
4. List any names starting with: THE, FOR, NA, patterns not covered by rules
5. Report findings and suggest additions to rules/special_cases.md
   before processing begins

Do not modify any file. Report only.