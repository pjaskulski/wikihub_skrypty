""" import parafii prawosławnych z AHP (XVI wiek) """
import os
import sys
import time
import warnings
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import element_search_adv, get_properties, get_elements
from property_import import create_statement_data


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
                             'refine date', 'stated in'
                            ])

elements = get_elements(['parish (Orthodox Church)', 'second half'])


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    references = {}
    references[properties['stated in']] = 'Q234031' # referencja do elementu AHP w instancji testowej!
    references[properties['retrieved']] = '2023-06-15'

    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/7' # XVI wiek
    qualifiers[properties['refine date']] = elements['second half']     # druga połowa


    file_name = Path('..') / 'data' / 'ahp_parafie_prawoslawne.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        lines = [line.strip() for line in lines]

    for line in lines:
        tmp = line.split('@')
        id_miejscowosci = tmp[0].strip()
        nazwa_16w = tmp[1].strip()
        parafia_nazwa = tmp[2].strip() # to chyba nazwa katolickiej parafii, do pominięcia
        varia = tmp[3].strip()         # to pomijamy
        powiat_p = tmp[4].strip()      # to pomijamy - z wyj. parafi Czarna
        kraj = tmp[5].strip()          # to pomijamy
        latitude = tmp[6].strip()
        longitude = tmp[7].strip()

        instance_of = elements['parish (Orthodox Church)']

        label_pl = f"parafia prawosławna {nazwa_16w}"
        label_en = f"orthodox parish {nazwa_16w}"

        # jeden wyjątek - parafia Czarna występuje 2x - w różnych powiatach
        if nazwa_16w == 'Czarna':
            description_pl = f"parafia prawosławna [powiat {powiat_p}] (jednostka w systemie administracji kościelnej: Kościół prawosławny, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
            description_en = f"orthodox parish [district {powiat_p}] (unit in the religious administrative system: Orthodox Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
        else:
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

        # współrzędne parafii
        if latitude and longitude:
            coordinate = f'{latitude},{longitude}'
            statement = create_statement_data(properties['coordinate location'],
                                              coordinate, None, None, add_ref_dict=references)
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
        ok, item_id = element_search_adv(label_en, 'en', parameters, description=description_en)
        if not ok:
            if WIKIBASE_WRITE:
                test = 1
                while True:
                    try:
                        new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        print(f'Dodano: # [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_en} / {label_pl}]')
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
                print(f"Przygotowano dodanie: # [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_en} / {label_pl}]")
        else:
            print(f'Element: # [https://prunus-208.man.poznan.pl/wiki/Item:{item_id} {label_en} / {label_pl}] już istnieje.')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
