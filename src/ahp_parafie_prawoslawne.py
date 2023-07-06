""" import parafii prawosławnych z AHP (XVI wiek) """

import os
import sys
import time
import warnings
import sqlite3
from sqlite3 import Error
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import element_search_adv, get_properties, get_elements
from property_import import create_statement_data


def create_connection(db_file, with_extension=False):
    """ tworzy połączenie z bazą SQLite
        db_file - ścieżka do pliku bazy
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        if with_extension:
            conn.enable_load_extension(True)
            conn.load_extension("../fuzzy.so")
            conn.load_extension("../spellfix.so")
            conn.load_extension("../unicode.so")

    except Error as sql_error:
        print(sql_error)

    return conn


def field_strip(value:str) -> str:
    """ funkcja przetwarza wartość pola z bazy/arkusza """
    if value:
        value = value.strip()
    else:
        value = ''

    return value


warnings.filterwarnings("ignore")

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

WIKIBASE_WRITE = True

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'refine date'
                            ])

elements = get_elements(['parish (Orthodox Church)', 'second half'])


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    if WIKIBASE_WRITE:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

    file_name = Path('..') / 'data' / 'ahp_parafie_prawoslawne2.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    db_path = Path('..') / 'data' / 'ahp_zbiorcza.sqlite'
    db = create_connection(db_path, with_extension=False)

    # wspólna referencja dla wszystkich deklaracji
    now = datetime.now()
    retrieved = now.strftime("%Y-%m-%d")
    references = {}
    references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'
    references[properties['retrieved']] = retrieved

    # wspólny kwalifikator
    qualifiers = {}
    qualifiers[properties['point in time']] = '+1501-00-00T00:00:00Z/7' # XVI wiek
    qualifiers[properties['refine date']] = elements['second half']     # druga połowa

    instance_of = elements['parish (Orthodox Church)']

    for line in lines:
        tmp = line.strip().split(',')
        if tmp[1] != '1': # tylko parafie prawosławne
            continue

        parafia_id = tmp[0].strip()
        sql = f"""SELECT ahp_zbiorcza_pkt_prng_import.nazwa_16w as nazwa_16w
                 FROM ahp_zbiorcza_pkt_prng_import
                 WHERE ahp_zbiorcza_pkt_prng_import.id_miejscowosci = '{parafia_id}'
        """
        parafia = ''
        cur_prng = db.cursor()
        cur_prng.execute(sql)
        results = cur_prng.fetchone()
        if results:
            parafia = field_strip(results[0])

        if not parafia:
            print('ERROR: brak parafii dla id:', parafia_id)
            continue

        label_pl = f"parafia prawosławna {parafia}"
        label_en = f"orthodox parish {parafia}"
        description_pl = "parafia prawosławna (jednostka w systemie administracji kościelnej: Kościół prawosławny, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
        description_en = "orthodox parish (unit in the religious administrative system: Orthodox Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"

        # przygotowanie struktur wikibase
        data = []

        # instance of
        statement = create_statement_data(properties['instance of'],
                                          instance_of,
                                          None, None, add_ref_dict=references)
        if statement:
            data.append(statement)

        # etykiety, description
        wb_item = wbi_core.ItemEngine(new_item=True, data=data)
        wb_item.set_label(label_en, lang='en')
        wb_item.set_label(label_pl,lang='pl')

        wb_item.set_description(description_en, 'en')
        wb_item.set_description(description_pl, 'pl')

        # wyszukiwanie po etykiecie
        parameters = [(properties['instance of'], instance_of)]
        ok, item_id = element_search_adv(label_en, 'en', parameters)
        if not ok:
            if WIKIBASE_WRITE:
                test = 1
                while True:
                    try:
                        new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        print(f'Dodano nowy element: {label_en} / {label_pl} = {new_id}')
                        break
                    except MWApiError as wb_error:
                        err_code = wb_error.error_msg['error']['code']
                        message = wb_error.error_msg['error']['info']
                        print(f'ERROR: {err_code}, {message}')
                        # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                        # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                        if err_code in ['assertuserfailed', 'badtoken']:
                            if test == 1:
                                print('Generate edit credentials...')
                                login_instance.generate_edit_credentials()
                                test += 1
                                continue
                        sys.exit(1)
            else:
                new_id = 'TEST'
                print(f"Przygotowano dodanie elementu - {label_en} / {label_pl}  = {new_id}")
        else:
            print(f'Element: {label_en} / {label_pl} już istnieje: {item_id}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')