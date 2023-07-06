""" weryfikacja parafii """

import re
from pathlib import Path

file_name = Path('..') / 'data' / 'parafie_lista_q.txt'
with open(file_name, 'r', encoding='utf-8') as f:
    lines = f.readlines()

parafie = []
lines = [line.strip() for line in lines]
for line in lines:
    pattern = r'Q\d{6}'
    match = re.search(pattern=pattern, string=line)
    if match:
        qid = match.group()
        if qid in parafie:
            print('ERROR: ', qid, line)
        else:
            parafie.append(qid)
