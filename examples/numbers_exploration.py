import sys
from numbers_parser import Document

doc = Document(sys.argv[1])
print(doc)

sheets = doc.sheets

curr_sheet = sheets[0]
print(curr_sheet.name)
exit()

tables = sheets[0].tables
print(tables)

rows = tables[0].rows()
print(rows)