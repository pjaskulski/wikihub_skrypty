""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import get_properties, search_by_unique_id



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

WIKIBASE_WRITE = False

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
print('Przygotowanie słownika właściwości...')
properties = get_properties(['prng id'])


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    if WIKIBASE_WRITE:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

    # tworzenie obiektu loggera
    file_log = Path('..') / 'log' / 'prng_qid.log'

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler(file_log)
    log_format = logging.Formatter('%(asctime)s - %(message)s')
    c_handler.setFormatter(log_format)
    f_handler.setFormatter(log_format)
    c_handler.setLevel(logging.DEBUG)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)


    file_name = Path('..') / 'data' / 'ahp_zbiorcza_pkt_prng.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    line_number = 0
    for line in lines:
        line_number +=1
        print('LINE:', line_number)
        t_line = line.split('@')
        zbiorcza_prng = t_line[22].strip()

        # szukanie w wiki po identyfikatorze prng
        element_qid = ''

        if zbiorcza_prng:
            ok_prng, element_qid = search_by_unique_id(properties['prng id'], zbiorcza_prng)
            if not ok_prng:
                logger.error(f'ERROR: Nie znaleziono elementu dla PRNG {zbiorcza_prng}, {element_qid}')
                continue
            else:
                with open(Path('..') / 'data' / 'prng_qid.csv', 'a', encoding='utf-8') as fm:
                    fm.write(f"{zbiorcza_prng},{element_qid}\n")
