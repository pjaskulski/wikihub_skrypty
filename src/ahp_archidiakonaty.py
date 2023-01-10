""" import archidiakonatów z AHP (XVI wiek) """

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import element_search_adv, get_properties, get_elements
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

WIKIBASE_WRITE = True

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts'
                            ])

elements = get_elements(['deaconry (Roman Catholic Church)',
                         'provostship (Roman Catholic Church)',
                         'archdeaconry (Roman Catholic Church)',
                         'territory (Roman Catholic Church)',
                         'diocese (Roman Catholic Church)'])

# wspólna referencja dla wszystkich deklaracji
references = {}
references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    if WIKIBASE_WRITE:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

    file_name = Path('..') / 'data' / 'ahp_archidiakonaty.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    references = {}
    references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'
    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/9'

    for line in lines:
        t_line = line.split(',')
        archidiakonat = t_line[0].strip()
        diecezja = t_line[1].strip()

        wyjatki = ['Kielce Dz',
                   'Kielce Pr',
                   'Tarnów Pr',
                   'Wieluń Ter']

        if archidiakonat in wyjatki:
            if archidiakonat == 'Kielce Dz':
                label_pl = "dziekania Kielce"
                label_en = "deaconry Kielce"
                description_pl = "dziekania (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = "deaconry (unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
                instance_of = elements['deaconry (Roman Catholic Church)']
                stated_as = 'Kielce Dz'
            elif archidiakonat == 'Kielce Pr':
                label_pl = "prepozytura Kielce"
                label_en = "provostship Kielce"
                description_pl = "prepozytura (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = "provostship (unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
                instance_of = elements['provostship (Roman Catholic Church)']
                stated_as = 'Kielce Pr'
            elif archidiakonat == 'Tarnów Pr':
                label_pl = "prepozytura Tarnów"
                label_en = "provostship Tarnów"
                description_pl = "prepozytura (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = "provostship (unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
                instance_of = elements['provostship (Roman Catholic Church)']
                stated_as = 'Tarnów Pr'
            elif archidiakonat == 'Wieluń Ter':
                label_pl = "terytorium Wieluń"
                label_en = "territory Wieluń"
                description_pl = "terytorium (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = "territory (unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
                instance_of = elements['territory (Roman Catholic Church)']
                stated_as = 'Wieluń Ter'
        else:
            label_pl = f"archidiakonat {archidiakonat}"
            label_en = f"archdeaconry {archidiakonat}"
            description_pl = "archidiakonat (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
            description_en = "archdeaconry (unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
            instance_of = elements['archdeaconry (Roman Catholic Church)']
            stated_as = archidiakonat

        # przygotowanie struktur wikibase
        data = []

        # instance of
        statement = create_statement_data(properties['instance of'],
                                          instance_of,
                                          None, None, add_ref_dict=references)
        if statement:
            data.append(statement)

        # stated as
        statement = create_statement_data(properties['stated as'],
                                          f'pl:"{stated_as}"',
                                          None, qualifier_dict=qualifiers, add_ref_dict=references)
        if statement:
            data.append(statement)

        # part of
        parameters = [(properties['instance of'], elements['diocese (Roman Catholic Church)'])]
        ok, diocese_qid = element_search_adv(f'diocese {diecezja}', 'en', parameters)
        if ok:
            statement = create_statement_data(properties['part of'],
                                              diocese_qid,
                                              None, qualifier_dict=qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)
        else:
            print('ERROR: nie znaleziono diecezji ', diecezja)
            sys.exit(1)

        # etykiety, description
        wb_item = wbi_core.ItemEngine(new_item=True, data=data)
        wb_item.set_label(label_en, lang='en')
        wb_item.set_label(label_pl,lang='pl')

        wb_item.set_description(description_en, 'en')
        wb_item.set_description(description_pl, 'pl')

        # wyszukiwanie po etykiecie
        parameters = [(properties['instance of'], instance_of),
                      (properties['part of'], diocese_qid)]
        ok, item_id = element_search_adv(label_en, 'en', parameters)
        if not ok:
            if WIKIBASE_WRITE:
                test = 1
                while True:
                    try:
                        new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        print(f'Dodano nowy element: {label_en} / {label_pl} = {new_id}')

                        # uzupełnienie diecezji
                        if diocese_qid != 'NOT FOUND':
                            update_data = []
                            # has part or parts (może być wiele, stąd parametr if_exists!)
                            statement = create_statement_data(properties['has part or parts'],
                                                                new_id,
                                                                None, qualifier_dict=qualifiers,
                                                                add_ref_dict=references, if_exists='APPEND')
                            if statement:
                                update_data.append(statement)
                            wb_item_update = wbi_core.ItemEngine(item_id=diocese_qid, data=update_data, debug=False)
                            wb_item_update.write(login_instance, entity_type='item')
                            print(f"Dodano do elementu {diocese_qid} deklarację: 'has part or parts' -> {new_id}")

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
