file = open('gui/web/scripts/iso_codes_table.txt', 'r')
lines = file.readlines()
langs = ""

for line in lines:
    line = line.split('|')
    langs += line[1] if line[1] != '' else line[0]
    langs += '\n'

langs = langs.removesuffix('\n')

with open('gui/web/scripts/iso_codes.txt', 'w+') as f:
    f.write(langs)