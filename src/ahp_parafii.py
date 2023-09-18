""" import parafii z AHP (XVI wiek) """

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
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved', 'stated in',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'refine date', 'information status'
                            ])

elements = get_elements(['deanery (Latin Church)',
                         'deaconry (Latin Church)',
                         'provostship (Latin Church)',
                         'archdeaconry (Latin Church)',
                         'territory (Latin Church)',
                         'diocese (Latin Church)',
                         'parish (Latin Church)',
                         'second half',
                         'uncertain'])


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    file_name = Path('..') / 'data' / 'ahp_parafie.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    # słownik dekanatów
    dekanaty = {}
    dekanaty_file_name = Path('..') / 'data' / 'ahp_dekanaty.csv'
    with open(dekanaty_file_name, 'r', encoding='utf-8') as f:
        dekanaty_lines = f.readlines()
        for d_line in dekanaty_lines:
            tmp = d_line.split(',')
            dekanaty[tmp[0]] = tmp[1]

    references = {}
    references[properties['stated in']] = 'Q234031' # referencja do elementu AHP w instancji testowej!
    references[properties['retrieved']] = '2023-06-15'

    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/7' # XVI wiek
    qualifiers[properties['refine date']] = elements['second half']     # druga połowa

    instance_of = elements['parish (Latin Church)']

    for line in lines:
        t_line = line.split('@')
        parafia_zbiorcza = t_line[0].strip()
        label_pl = t_line[1].strip()
        label_en = t_line[2].strip()
        g_dekanat = t_line[3].strip()
        # etykieta dekanatu ze słownika (różni się dla Gniezna i Tarnowa od g_dekanat)
        # jeżeli mamy 2 dekanaty to oba trafiają do etykiety
        if ' lub ' not in g_dekanat:
            if g_dekanat:
                dekanat_label = dekanaty[g_dekanat]
            else:
                dekanat_label = ''
        else:
            dekanat_label = g_dekanat

        g_archidia = t_line[4].strip()
        g_diecezja = t_line[5].strip()
        latitude = t_line[6].strip()
        longitude = t_line[7].strip()

        if dekanat_label:
            description_pl = f"parafia [dekanat {dekanat_label}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, stan na 2 poł. XVI wieku)"
            description_en = f"parish [deanery {dekanat_label}](unit in the religious administrative system: Latin Church, status in the 2nd half of the 16th century)"
        else:
            if g_archidia:
                if g_archidia == 'Kielce Dz':
                    label_archidiakonat_en = 'deaconry Kielce'
                    label_archidiakonat_pl = 'dziekania Kielce'
                elif g_archidia == 'Kielce Pr':
                    label_archidiakonat_en = 'provostship Kielce'
                    label_archidiakonat_pl = 'prepozytura Kielce'
                elif g_archidia == 'Tarnów Pr':
                    label_archidiakonat_en = 'provostship Tarnów'
                    label_archidiakonat_pl = 'prepozytura Tarnów'
                elif g_archidia == 'Wieluń Ter':
                    label_archidiakonat_en = 'territory Wieluń'
                    label_archidiakonat_pl = 'terytorium Wieluń'
                else:
                    label_archidiakonat_en = f"archdeaconry {g_archidia}"
                    label_archidiakonat_pl = f"archidiakonat {g_archidia}"

                description_pl = f"parafia [{label_archidiakonat_pl}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, stan na 2 poł. XVI wieku)"
                description_en = f"parish [{label_archidiakonat_en}](unit in the religious administrative system: Latin Church, status in the 2nd half of the 16th century)"

            elif g_diecezja:
                description_pl = f"parafia [diecezja {g_diecezja}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, stan na 2 poł. XVI wieku)"
                description_en = f"parish [diocese {g_diecezja}](unit in the religious administrative system: Latin Church, status in the 2nd half of the 16th century)"

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
                                          f'pl:"{parafia_zbiorcza}"',
                                          None, qualifier_dict=qualifiers, add_ref_dict=references)
        if statement:
            data.append(statement)

        master_qid = ''
        master_qid2 = ''
        ok2 = None
        uncertainty = False
        if ' lub ' in dekanat_label:
            uncertainty = True
        # part of (dekanat, archidiakonat lub diecezja)
        if dekanat_label and not ' lub ' in dekanat_label:
            parameters = [(properties['instance of'], elements['deanery (Latin Church)'])]
            ok, master_qid = element_search_adv(f'deanery {dekanat_label}', 'en', parameters)
        # jedna z parafii ma przypisane 2 dekanaty...
        elif dekanat_label and ' lub ' in dekanat_label:
            tmp_dekanat = dekanat_label.split(' lub ')
            parameters = [(properties['instance of'], elements['deanery (Latin Church)'])]
            ok, master_qid = element_search_adv(f'deanery {tmp_dekanat[0]}', 'en', parameters)
            ok2, master_qid2 = element_search_adv(f'deanery {tmp_dekanat[1]}', 'en', parameters)
        # może nadrzędną jednostką jest archidiakonat?
        elif g_archidia:
            # może to deaconry, provostship, territory
            if g_archidia == 'Kielce Dz':
                label_archidiakonat = 'deaconry Kielce'
                element_archidiakonat = elements['deaconry (Latin Church)']
            elif g_archidia == 'Kielce Pr':
                label_archidiakonat = 'provostship Kielce'
                element_archidiakonat = elements['provostship (Latin Church)']
            elif g_archidia == 'Tarnów Pr':
                label_archidiakonat = 'provostship Tarnów'
                element_archidiakonat = elements['provostship (Latin Church)']
            elif g_archidia == 'Wieluń Ter':
                label_archidiakonat = 'territory Wieluń'
                element_archidiakonat = elements['territory (Latin Church)']
            else:
                label_archidiakonat = f"archdeaconry {g_archidia}"
                element_archidiakonat = elements['archdeaconry (Latin Church)']

            parameters = [(properties['instance of'], element_archidiakonat)]
            ok, master_qid = element_search_adv(label_archidiakonat, 'en', parameters)
        elif g_diecezja:
            # może jednak diecezja
            parameters = [(properties['instance of'], elements['diocese (Latin Church)'])]
            ok, master_qid = element_search_adv(f'diocese {g_diecezja}', 'en', parameters)
        else:
            print('ERROR: nie znaleziono nadrzędnej jednostki dla' , label_pl)
            sys.exit(1)

        p_qualifiers = qualifiers.copy()
        if uncertainty:
            p_qualifiers[properties['information status']] = elements['uncertain']

        if ok:
            statement = create_statement_data(properties['part of'],
                                              master_qid,
                                              None, qualifier_dict=p_qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)

        if ok2:
            statement = create_statement_data(properties['part of'],
                                              master_qid2,
                                              None, qualifier_dict=p_qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)

        # współrzędne parafii - - Point (23.29833332 52.68194448)
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
        parameters = [(properties['instance of'], instance_of),
                      (properties['part of'], master_qid)]
        ok, item_id = element_search_adv(label_en, 'en', parameters)
        if not ok:
            if WIKIBASE_WRITE:
                test = 1
                while True:
                    try:
                        new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        print(f'Dodano: # [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_en} / {label_pl}]')

                        # uzupełnienie dekanatu, archidiakonatu lub diecezji
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

                        # poprawka na szybko bo wcześniej nie przewidywano 'lub' w dekanatach
                        if master_qid2 != 'NOT FOUND' and master_qid2 != '':
                            update_data = []
                            # has part or parts (może być wiele, stąd parametr if_exists!)
                            statement = create_statement_data(properties['has part or parts'],
                                                                new_id,
                                                                None, qualifier_dict=qualifiers,
                                                                add_ref_dict=references, if_exists='APPEND')
                            if statement:
                                update_data.append(statement)
                            wb_item_update = wbi_core.ItemEngine(item_id=master_qid2, data=update_data, debug=False)
                            wb_item_update.write(login_instance, entity_type='item')
                            print(f"Dodano do elementu {master_qid2} deklarację: 'has part or parts' -> {new_id}")


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

            #sys.exit(1)
        else:
            print(f'Element: # [https://prunus-208.man.poznan.pl/wiki/Item:{item_id} {label_en} / {label_pl}] już istnieje.')
