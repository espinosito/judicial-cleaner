import json
# Show all B lines that still have institutional prefix at start
lines = open('data/output/ChtxGrayson_1988_clean.txt').readlines()
prefixes = ['AUTHORITY','JAIL','COURT','OFFICE','DEPT','BUREAU','BOARD','FUND','PLAN','TRUST','ESTATE','CLUB','LODGE','POST','UNIT','DIVISION','SECTION']
for l in lines:
    fields = l.split('\t')
    if len(fields) > 5 and fields[4].strip() == 'B':
        name = fields[5].strip()
        first = name.split()[0].upper() if name else ''
        if first in prefixes:
            print(name)
