""" import dekanatów z AHP (XVI wiek) """

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
                             'point in time', 'part of', 'has part or parts',
                             'refine date', 'stated in'
                            ])

elements = get_elements(['deanery (Latin Church)',
                         'deaconry (Latin Church)',
                         'provostship (Latin Church)',
                         'archdeaconry (Latin Church)',
                         'territory (Latin Church)',
                         'diocese (Latin Church)',
                         'second half'])




# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    file_name = Path('..') / 'data' / 'ahp_dekanaty.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    references = {}
    references[properties['stated in']] = 'Q234031' # referencja do elementu AHP w instancji testowej!
    references[properties['retrieved']] = '2023-06-15'

    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/7' # XVI wiek
    qualifiers[properties['refine date']] = elements['second half']     # druga połowa

    instance_of = elements['deanery (Latin Church)']

    for line in lines:
        t_line = line.split(',')
        g_dekanat = t_line[0].strip()
        dekanat_label = t_line[1].strip()
        archidiakonat = t_line[2].strip()
        diecezja = t_line[3].strip()

        label_pl = f"dekanat {dekanat_label}"
        label_en = f"deanery {dekanat_label}"
        description_pl = "dekanat (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, stan na 2 poł. XVI wieku)"
        description_en = "deanery (unit in the religious administrative system: Latin Church, status in the 2nd half of the 16th century)"

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
                                          f'pl:"{g_dekanat}"',
                                          None, qualifier_dict=qualifiers, add_ref_dict=references)
        if statement:
            data.append(statement)

        # part of (archidiakonat lub diecezja)
        if archidiakonat:
            parameters = [(properties['instance of'], elements['archdeaconry (Latin Church)'])]
            ok, master_qid = element_search_adv(f'archdeaconry {archidiakonat}', 'en', parameters)

            # może to deaconry, provostship, territory
            if not ok:
                if archidiakonat == 'Kielce Dz':
                    label_archidiakonat = 'deaconry Kielce'
                    element_archidiakonat = elements['deaconry (Latin Church)']
                elif archidiakonat == 'Kielce Pr':
                    label_archidiakonat = 'provostship Kielce'
                    element_archidiakonat = elements['provostship (Latin Church)']
                elif archidiakonat == 'Tarnów Pr':
                    label_archidiakonat = 'provostship Tarnów'
                    element_archidiakonat = elements['provostship (Latin Church)']
                elif archidiakonat == 'Wieluń Ter':
                    label_archidiakonat = 'territory Wieluń'
                    element_archidiakonat = elements['territory (Latin Church)']
                else:
                    print('ERROR: nie znaleziono jednostki nadrzędnej:', g_dekanat, archidiakonat, diecezja)

                parameters = [(properties['instance of'], element_archidiakonat)]
                ok, master_qid = element_search_adv(label_archidiakonat, 'en', parameters)
        else:
            parameters = [(properties['instance of'], elements['diocese (Latin Church)'])]
            ok, master_qid = element_search_adv(f'diocese {diecezja}', 'en', parameters)

        if ok:
            statement = create_statement_data(properties['part of'],
                                              master_qid,
                                              None, qualifier_dict=qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)
        else:
            print('ERROR: nie znaleziono nadrzędnego archidiakonatu', archidiakonat, '(diecezja', diecezja , ')')
            sys.exit(1)

        # etykiety, description
        wb_item = wbi_core.ItemEngine(new_item=True, data=data)
        wb_item.set_label(label_en, lang='en')
        wb_item.set_label(label_pl,lang='pl')

        wb_item.set_description(description_en, 'en')
        wb_item.set_description(description_pl, 'pl')

        # wyszukiwanie po etykiecie
        parameters = [(properties['instance of'], instance_of),
                      (properties['part of'], master_qid)]
        ok, item_id = element_search_adv(label_en, 'en', parameters)
        if not ok:
            if WIKIBASE_WRITE:
                test = 1
                while True:
                    try:
                        new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        print(f'Dodano:  # [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_en} / {label_pl}]')

                        # uzupełnienie archidiakonatu lub diecezji
                        if master_qid != 'NOT FOUND':
                            update_data = []
                            # has part or parts (może być wiele, stąd parametr if_exists!)
                            statement = create_statement_data(properties['has part or parts'],
                                                                new_id,
                                                                None, qualifier_dict=qualifiers,
                                                                add_ref_dict=references, if_exists='APPEND')
                            if statement:
                                update_data.append(statement)
                            wb_item_update = wbi_core.ItemEngine(item_id=master_qid, data=update_data, debug=False)
                            wb_item_update.write(login_instance, entity_type='item')
                            print(f"Dodano do elementu {master_qid} deklarację: 'has part or parts' -> {new_id}")

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
                print(f"Przygotowano dodanie:  # [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_en} / {label_pl}]")
        else:
            print(f'Element:  # [https://prunus-208.man.poznan.pl/wiki/Item:{item_id} {label_en} / {label_pl}] już istnieje.')
