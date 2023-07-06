""" import do prezentacji """
# pylint: disable=logging-fstring-interpolation

import os
import time
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import element_search_adv, get_properties, get_elements
from wikidariahtools import write_or_exit
from property_import import create_statement_data


# instancja testowa nie jest skonfigurowana jak wikidata.org wiec pojawiają się
# (niegroźne) ostrzerzenia
warnings.filterwarnings("ignore")

# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# tokeny do autoryzacji ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# autoryzacja (OAuth)
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

# pomiar czasu wykonania
start_time = time.time()

# czy działanie z zapisem czy tylko testowe
WIKIBASE_WRITE = False

 # tworzenie obiektu loggera
file_log = Path('..') / 'log' / 'import_prezentacja.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler = logging.StreamHandler()
c_handler.setFormatter(log_format)
c_handler.setLevel(logging.DEBUG)
logger.addHandler(c_handler)

# zapis logów do pliku tylko jeżeli uruchomiono z zapisem do wiki
if WIKIBASE_WRITE:
    f_handler = logging.FileHandler(file_log)
    f_handler.setFormatter(log_format)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(f_handler)

# standardowe właściwości i elementy (P i Q są wyszukiwane w wikibase raz i
# trzymane w słownikach każda instancja może mieć inny numer P dla danej
# właściwości, więc lepiej nie używać sztywnych wartości typu P31, chyba że pracujemy
# zawsze z jedną i tą samą instancją)
logger.info('Przygotowanie słowników...')
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'given name',
                             'family name', 'date of birth', 'date of death',
                             'Wikidata ID', 'refine date'
                            ])
elements = get_elements(['human','male given name','family name'])


# ------------------------------------------------------------------------------
if __name__ == '__main__':

    # logowanie do instancji wikibase, skrypt w trybie testowym tylko czyta
    # i nie wymaga logowania
    login_instance = None
    if WIKIBASE_WRITE:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

    logger.info('POCZĄTEK IMPORTU')

    # dane przykładowe
    identyfikator_bn = '1160835' # Bolesław Prus
    label_pl = 'Bolesław Prus TEST 03'
    description_pl = 'pisarz (1847-1912)'
    given_name = 'Bolesław'
    family_name = 'Prus'
    date_of_birth = '+1847-00-00T00:00:00Z/9'
    date_of_death = '+1912-00-00T00:00:00Z/9'

    parameters = [(properties['instance of'], elements['male given name'])]
    ok, name_qid = element_search_adv(given_name, 'en', parameters)

    parameters = [(properties['instance of'], elements['family name'])]
    ok, family_qid = element_search_adv(family_name, 'en', parameters)

    data = []

    # deklaracja instance of = human
    statement = create_statement_data(properties['instance of'],
                                              elements['human'],
                                              None, None, add_ref_dict=None)
    if statement:
        data.append(statement)

    # deklaracja given name
    statement = create_statement_data(properties['given name'],
                                              name_qid,
                                              None, None, add_ref_dict=None)
    if statement:
        data.append(statement)

    # deklaracja family name
    statement = create_statement_data(properties['family name'],
                                              family_qid,
                                              None, None, add_ref_dict=None)
    if statement:
        data.append(statement)


    # tworzenie noweg elementu
    wb_item = wbi_core.ItemEngine(new_item=True, data=data)
    wb_item.set_label(label_pl,lang='pl')
    wb_item.set_description(description_pl, 'pl')

    if WIKIBASE_WRITE:
        element_qid = write_or_exit(login_instance, wb_item, logger)
        message = f'Dodano element: {label_pl} ({description_pl}) = {element_qid}'
        logger.info(message)
    else:
        element_qid = 'TEST'
        logger.info(f"Przygotowano dodanie elementu - {label_pl} ({description_pl})  = {element_qid}")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
