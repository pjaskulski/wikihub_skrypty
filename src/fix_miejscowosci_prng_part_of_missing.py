""" uzupełnienie danych miejscowosci z PRNG - gdy jest part
    of ale docelowy item nie ma has part of parts
"""
# pylint: disable=logging-fstring-interpolation

import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import get_properties
from wikidariahtools import get_claim_value, write_or_exit
from property_import import has_statement, create_statement_data


# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
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

# czy zapis do wikibase czy tylko test
WIKIBASE_WRITE = True


# ----------------------------------- MAIN -------------------------------------

if __name__ == '__main__':

    # tworzenie obiektu loggera
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    c_handler = logging.StreamHandler()
    log_format = logging.Formatter('%(asctime)s - %(message)s')
    c_handler.setFormatter(log_format)
    logger.addHandler(c_handler)

    # miejscowości z PRNG od 99101 do 219941
    start = 219552
    stop =  219941

    # standardowe właściwości
    print('Przygotowanie właściwości...')
    properties = get_properties(['part of', 'has part or parts', 'reference URL', 'retrieved'])

    # wspólna referencja dla wszystkich deklaracji z PRG
    references = {}
    references[properties['reference URL']] = 'https://mapy.geoportal.gov.pl/wss/service/PZGiK/PRNG/WFS/GeographicalNames'
    references[properties['retrieved']] = '2022-09-23'

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    licznik = 0
    for item in range(start, stop + 1):
        qid = f'Q{item}'

        try:
            wb_item = wbi_core.ItemEngine(item_id=qid)
        except (MWApiError, KeyError):
            logger.info(f'Element: {qid} nie istnieje.')
            continue

        lista = wb_item.get_property_list()
        if properties['part of'] in lista:
            value = get_claim_value(qid, properties['part of'], wikibase_item=wb_item)
            for part in value:
                if not has_statement(part, properties['has part or parts'], qid):
                    licznik += 1
                    data = []
                    statement = create_statement_data(properties['has part or parts'], qid, references, None, if_exists='APPEND')
                    if statement:
                        data.append(statement)
                        label_pl = wb_item.get_label('pl')
                        wb_help = wbi_core.ItemEngine(item_id=part, data=data)
                        label_target = wb_help.get_label('pl')
                        wb_item = wbi_core.ItemEngine(item_id=qid, data=data)

                        write_or_exit(login_instance, wb_item, logger)

                        message = f'{licznik}:, {part}, {label_target}, uzupełniono właściwość "has part or parts" =  {qid}, {label_pl}'
                        logger.info(message)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logger.info(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
