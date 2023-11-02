import sys
from numbers_parser import Document, Table

doc = Document(sys.argv[1])
print(doc)

sheet = doc.sheets[0]

print(sheet.name)

table = sheet.tables[0]

print(table.name)


#doc.save("new.numbers")1