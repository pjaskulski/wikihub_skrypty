""" dopasowywanie PRNG do miejscowości z przypisanymi nieunikalnymi PRGNG """
import csv
from pathlib import Path

input_path = Path('..') / 'data' / 'dopasowanie_prng_3a.csv'
input_korekta = Path('..') / 'data' / 'AHP_PRNG_korekta.csv'
output_path = Path('..') / 'data' / 'ahp_prng_korekta_auto.csv'

prng_dict = {}

with open(input_path, 'r', encoding='utf-8') as csv_file:
    csv_reader = csv.DictReader(csv_file)
    for row in csv_reader:
        id_ahp = row["id_ahp"]
        skrypt_prng = row["skrypt_prng"]
        skrypt_nazwa = row["skrypt_nazwa_prng"]
        prng_dict[id_ahp] = skrypt_prng+'@'+skrypt_nazwa

with open(input_korekta, 'r', encoding='utf-8') as f:
    lines_korekta = f.readlines()

with open(output_path, 'w', encoding='utf-8') as out:
    out.write('"id_miejscowosci","PRNG count","zbiorcza_prng","prng_korekta","nazwa_korekta"\n')

for line in lines_korekta:
    line = line.strip()
    tmp = line.split(',')
    id_ahp = tmp[0]
    count_ahp = tmp[1]
    prng_ahp = tmp[2]
    prng_korekta = ''
    nazwa_korekta = ''
    if id_ahp in prng_dict:
        korekta = prng_dict[id_ahp]
        tmp_korekta = korekta.split('@')
        prng_korekta = tmp_korekta[0]
        nazwa_korekta = tmp_korekta[1]

    with open(output_path, 'a', encoding='utf-8') as out:
        out.write(f'"{id_ahp}",{count_ahp},"{prng_ahp}","{prng_korekta}","{nazwa_korekta}"  \n')
