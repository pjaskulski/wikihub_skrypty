""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import time
from pathlib import Path
from langdetect import detect


# pomiar czasu wykonania
start_time = time.time()


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    file_name = Path('..') / 'data' / 'ahp_zbiorcza_pkt_prng.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    line_number = 0
    for line in lines:
        line_number +=1
        print('LINE:', line_number)
        t_line = line.split('@')
        id_miejscowosci = t_line[0].strip()
        nazwa_16w = t_line[4].strip()

        # szukanie w wiki po identyfikatorze prng
        if nazwa_16w:
            lang = detect(nazwa_16w)
            with open(Path('..') / 'data' / 'ahp_lang.csv', 'a', encoding='utf-8') as fm:
                fm.write(f"{nazwa_16w} = {lang}\n")
