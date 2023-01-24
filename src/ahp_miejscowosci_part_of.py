""" uzupełnienie miejscowości z AHP (XVI wiek) - właściwość part of"""
# pylint: disable=logging-fstring-interpolation

import time
import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import get_properties, search_by_unique_id, write_or_exit
from property_import import create_statement_data


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

line_qid_map = {}

 # tworzenie obiektu loggera
file_log = Path('..') / 'log' / 'ahp_zbiorcza_pkt_prng.log'
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

# standardowe właściwości
print('Przygotowanie właściwości...')
properties = get_properties(['part of', 'has part or parts', 'reference URL', 'retrieved', 'AHP id'])

# wspólna referencja dla wszystkich deklaracji
references = {}
references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'
# kwalifikator z punktem w czasie
qualifiers = {}
qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/9'

# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    # wczytanie słownika z mapowaniem line number -> qid
    file_index = Path('..') / 'data' / 'ahp_line_qid.csv'
    with open(file_index, 'r', encoding='utf-8') as fm:
        lines = fm.readlines()
    lines = [line.strip() for line in lines]
    for line in lines:
        t_line = line.split(',')
        line_qid_map[t_line[0].strip()] = t_line[1].strip()

    # wczytanie tabeli zbiorczej AHP
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
        m_nadrz = t_line[13].strip()

        # wyszukanie elementu miejscowości nadrzędnej w wikibase na podstawie id ahp
        ok, nadrz_qid = search_by_unique_id(properties['AHP id'], m_nadrz)
        if ok:
            data = []
            statement = create_statement_data(properties['part of'],
                                              nadrz_qid,
                                              None, qualifier_dict=qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)
        else:
            logger.info(f'ERROR: nie znaleziono elementu dla identyfikatora: {m_nadrz}')
            continue

        if data:
            line_qid = line_qid_map[line_number]
            wb_item = wbi_core.ItemEngine(item_id=line_qid, data=data)

            element_id = write_or_exit(login_instance, wb_item, logger)

            logger.info(f'{line_number}: uzupełniono właściwość "part of" =  {m_nadrz} = {nadrz_qid}')
