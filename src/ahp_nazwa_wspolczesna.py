""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import time
import os
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login


# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

# pomiar czasu wykonania
start_time = time.time()

prng_qid_map = {}


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    # wczytanie słownika z mapowaniem prng -> qid
    file_map = Path('..') / 'data' / 'prng_qid.csv'
    with open(file_map, 'r', encoding='utf-8') as fm:
        map_lines = fm.readlines()
    map_lines = [map_line.strip() for map_line in map_lines]
    for map_line in map_lines:
        t_line = map_line.split(',')
        prng_qid_map[t_line[0].strip()] = t_line[1].strip()

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
        nazwa_wspolczesna = t_line[2].strip()
        zbiorcza_prng = t_line[22].strip()

        # szukanie w wiki po identyfikatorze prng
        if nazwa_wspolczesna:
            if zbiorcza_prng in prng_qid_map:
                qid = prng_qid_map[zbiorcza_prng]
                wb_item = wbi_core.ItemEngine(item_id=qid)
                label_pl = wb_item.get_label('pl')
                if nazwa_wspolczesna != label_pl:
                    with open(Path('..') / 'log' / 'ahp_nazwa_wspołczesna.log', 'a', encoding='utf-8') as fm:
                        fm.write(f"{id_miejscowosci} ({qid}) -> {nazwa_wspolczesna} <> {label_pl}\n")
