""" test poprawności importu parafii z AHP (XVI wiek) """

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
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

WIKIBASE_WRITE = False

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location'
                            ])

elements = get_elements(['deanery (Roman Catholic Church)',
                         'deaconry (Roman Catholic Church)',
                         'provostship (Roman Catholic Church)',
                         'archdeaconry (Roman Catholic Church)',
                         'territory (Roman Catholic Church)',
                         'diocese (Roman Catholic Church)',
                         'parish (Roman Catholic Church)'])

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

    file_name = Path('..') / 'data' / 'ahp_granice_koscielne.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    references = {}
    references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'
    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/9'

    instance_of = elements['parish (Roman Catholic Church)']

    for line in lines:
        t_line = line.split('@')
        parafia_zbiorcza = t_line[0].strip()
        parafia_label = t_line[1].strip()
        g_dekanat = t_line[2].strip()
        dekanat_label = t_line[3].strip()
        g_archidia = t_line[4].strip()
        g_diecezja = t_line[5].strip()
        wgs84 = t_line[6].strip()

        label_pl = f"parafia {parafia_label}"
        label_en = f"parish {parafia_label}"
        if dekanat_label:
            description_pl = f"parafia [dekanat {dekanat_label}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
            description_en = f"parish [deanery {dekanat_label}](unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"
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

                description_pl = f"parafia [{label_archidiakonat_pl}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = f"parish [{label_archidiakonat_en}](unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"

            elif g_diecezja:
                description_pl = f"parafia [diecezja {g_diecezja}] (jednostka w systemie administracji kościelnej: Kościół katolicki ob. łacińskiego, wg Atlasu Historycznego Polski, stan na 2 poł. XVI wieku)"
                description_en = f"parish [diocese {g_diecezja}](unit in the religious administrative system: Roman Catholic Church, according to the Historical Atlas of Poland, as of the 2nd half of the XVIth century)"


        # przygotowanie struktur wikibase
        data = []

        master_qid = ''
        # part of (dekanat, archidiakonat lub diecezja)
        if dekanat_label:
            parameters = [(properties['instance of'], elements['deanery (Roman Catholic Church)'])]
            ok, master_qid = element_search_adv(f'deanery {dekanat_label}', 'en', parameters)
        # może nadrzędną jednostką jest archidiakonat?
        elif g_archidia:
            # może to deaconry, provostship, territory
            if g_archidia == 'Kielce Dz':
                label_archidiakonat = 'deaconry Kielce'
                element_archidiakonat = elements['deaconry (Roman Catholic Church)']
            elif g_archidia == 'Kielce Pr':
                label_archidiakonat = 'provostship Kielce'
                element_archidiakonat = elements['provostship (Roman Catholic Church)']
            elif g_archidia == 'Tarnów Pr':
                label_archidiakonat = 'provostship Tarnów'
                element_archidiakonat = elements['provostship (Roman Catholic Church)']
            elif g_archidia == 'Wieluń Ter':
                label_archidiakonat = 'territory Wieluń'
                element_archidiakonat = elements['territory (Roman Catholic Church)']
            else:
                label_archidiakonat = f"archdeaconry {g_archidia}"
                element_archidiakonat = elements['archdeaconry (Roman Catholic Church)']

            parameters = [(properties['instance of'], element_archidiakonat)]
            ok, master_qid = element_search_adv(label_archidiakonat, 'en', parameters)
        elif g_diecezja:
            # może jednak diecezja
            parameters = [(properties['instance of'], elements['diocese (Roman Catholic Church)'])]
            ok, master_qid = element_search_adv(f'diocese {g_diecezja}', 'en', parameters)
        else:
            print('ERROR: nie znaleziono nadrzędnej jednostki dla' , parafia_label)
            sys.exit(1)

        if ok:
            statement = create_statement_data(properties['part of'],
                                              master_qid,
                                              None, qualifier_dict=qualifiers, add_ref_dict=references)
            if statement:
                data.append(statement)



        # wyszukiwanie po etykiecie
        parameters = [(properties['instance of'], instance_of),
                      (properties['part of'], master_qid)]
        ok, item_id = element_search_adv(label_en, 'en', parameters)
        if ok:
            print(f'Znaleziono element: {label_en} / {label_pl} = {item_id}')
        else:
            print(f'ERROR: brak elementu: {label_en} / {label_pl}, dekanat: {dekanat_label} archidiakonat {g_archidia} diecezja {g_diecezja}')
