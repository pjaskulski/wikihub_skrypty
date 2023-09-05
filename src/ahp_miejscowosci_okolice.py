""" uzupełnienie miejscowości z AHP (XVI wiek) - właściwość part of"""
# pylint: disable=logging-fstring-interpolation

import time
import os
import logging
import sqlite3
import warnings
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import get_properties, search_by_unique_id, write_or_exit, get_elements
from property_import import create_statement_data, has_statement

warnings.filterwarnings("ignore")

# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

env_path = Path(".") / ".env"
# login i hasło ze zmiennych środowiskowych
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

# pomiar czasu wykonania
start_time = time.time()

WIKIBASE_WRITE = True

 # tworzenie obiektu loggera
file_log = Path('..') / 'log' / 'ahp_zbiorcza_okolice.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler = logging.StreamHandler()
c_handler.setFormatter(log_format)
c_handler.setLevel(logging.DEBUG)
logger.addHandler(c_handler)
if WIKIBASE_WRITE:
    f_handler = logging.FileHandler(file_log)
    f_handler.setFormatter(log_format)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(f_handler)

# standardowe właściwości
logger.info('Przygotowanie właściwości...')
properties = get_properties(['neighborhood with', 'point in time', 'reference URL',
                             'retrieved', 'AHP ID', 'refine date', 'stated in'])

logger.info('Przygotowanie elementów definicyjnych...')
elements = get_elements(['second half'])

references = {}
references[properties['stated in']] = 'Q234031' # referencja do elementu AHP w instancji testowej!
references[properties['retrieved']] = '2023-06-15'

qualifiers = {}
qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/7' # XVI wiek
qualifiers[properties['refine date']] = elements['second half']     # druga połowa

# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    db = sqlite3.connect(":memory:")
    cur = db.cursor()

    sql = """
    CREATE TABLE IF NOT EXISTS ahp_zbiorcza (
	    id_miejscowosci text NOT NULL,
	    okolica text NOT NULL);
    """

    cur.execute(sql)

    # wczytanie tabeli zbiorczej AHP
    file_name = Path('..') / 'data' / 'ahp_miejscowosci.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    # przygotowanie danych w bazie sqlite w pamięci RAM
    for line in lines:
        t_line = line.split('@')
        id_miejscowosci = t_line[0].strip()
        m_nadrz = t_line[13].strip()

        sql_add = f"insert into ahp_zbiorcza (id_miejscowosci, okolica) VALUES ('{id_miejscowosci}', '{m_nadrz}');"
        cur.execute(sql_add)

    # właściwy import 'okolic'
    line_number = 0
    for line in lines:
        line_number +=1

        t_line = line.split('@')
        id_miejscowosci = t_line[0].strip()
        m_nadrz = t_line[13].strip()

        if m_nadrz:
            sql = f"select id_miejscowosci from ahp_zbiorcza where okolica = '{m_nadrz}' and id_miejscowosci <> '{id_miejscowosci}';"
            cur.execute(sql)
            result = cur.fetchall()
            if not result:
                continue

            ok, element_qid = search_by_unique_id(properties['AHP ID'], id_miejscowosci)
            if not ok:
                logger.info(f'ERROR: nie znaleziono elementu dla id_ahp: {id_miejscowosci}')
                continue

            for item in result:
                okolica_id = item[0].strip()

                # wyszukanie elementu miejscowości należącej do okolicy z bieżącą miejscowością
                ok, okolica_qid = search_by_unique_id(properties['AHP ID'], okolica_id)
                if ok:
                    data = []
                    statement = create_statement_data(properties['neighborhood with'],
                                                      okolica_qid,
                                                      None,
                                                      qualifier_dict=qualifiers,
                                                      add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)
                else:
                    logger.info(f'ERROR: nie znaleziono elementu dla identyfikatora: {okolica_id}')
                    continue

                if not has_statement(element_qid, properties['neighborhood with'], okolica_qid):
                    if WIKIBASE_WRITE and data:
                        wb_item = wbi_core.ItemEngine(item_id=element_qid, data=data)
                        element_id = write_or_exit(login_instance, wb_item, logger)
                        logger.info(f'{id_miejscowosci} ({element_qid}): uzupełniono właściwość "neighborhood with" =  {okolica_qid} ({okolica_id})')
                    else:
                        logger.info(f'{id_miejscowosci} ({element_qid}): przygotowano właściwość "neighborhood with" =  {okolica_qid} ({okolica_id})')
                else:
                    logger.info(f'{id_miejscowosci} ({element_qid}): już posiada właściwość "neighborhood with" =  {okolica_qid} ({okolica_id})')

    cur.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
