""" import województw z pliku wojewodztwa.xlsx z danymi z PRG"""
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
import openpyxl
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import find_name_qid, element_search_adv, get_property_type
from property_import import create_statement_data


# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

# pomiar czasu wykonania
start_time = time.time()

WIKIBASE_WRITE = False

# standardowe właściwości i elementy
ok, p_instance_of = find_name_qid('instance of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'instance of' w instancji Wikibase")
    sys.exit(1)

ok, p_stated_as = find_name_qid('stated as', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated as' w instancji Wikibase")
    sys.exit(1)

ok, p_reference_url = find_name_qid('reference URL', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'reference URL' w instancji Wikibase")
    sys.exit(1)

ok, p_retrieved = find_name_qid('retrieved', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'retrieved' w instancji Wikibase")
    sys.exit(1)

ok, p_id_sdi = find_name_qid('id SDI', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'id SDI' w instancji Wikibase")
    sys.exit(1)

ok, p_part_of = find_name_qid('part of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'part of' w instancji Wikibase")
    sys.exit(1)

ok, p_teryt = find_name_qid('TERYT', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'TERYT' w instancji Wikibase")
    sys.exit(1)

# elementy definicyjne
# symbol QID elementu definicyjnego 'administrative unit', w wersji testowej: 'Q79096'
ok, q_administrative_unit = find_name_qid('administrative unit', 'item', strict=True)
if not ok:
    print("ERROR: brak elementu 'administrative unit' w instancji Wikibase")
    sys.exit(1)

# symbol QID elementu definicyjnego 'voivodship (The Republic of Poland (1999-2016))',
# wyszukiwanie po purl, w wersji testowej: Q80001
ok, q_voivodship = find_name_qid('http://purl.org/ontohgis#administrative_type_47', 'item',
                                 strict=True)
if not ok:
    print("ERROR: brak elementu 'http://purl.org/ontohgis#administrative_type_47' w instancji Wikibase")
    sys.exit(1)

# wspólna referencja dla wszystkich deklaracji z PRG
references = {}
references[p_reference_url] = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'
references[p_retrieved] = '2022-09-05'

# wspólna referencja dla wszystkich deklaracji z PRG
onto_references = {}
onto_references[p_reference_url] = 'https://ontohgis.pl'


def get_label_en(qid: str) -> str:
    """ zwraca angielską etykietę dla podanego QID """

    wb_item_test = wbi_core.ItemEngine(item_id=qid)
    result = wb_item_test.get_label('en')

    return result


# ----------------------------------- MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD, token_renew_period=28800)

    xlsx_input = '../data_prng/wojewodztwa.xlsx'
    wb = openpyxl.load_workbook(xlsx_input)
    ws = wb["wojewodztwa"]

    col_names = {}
    nr_col = 0
    for column in ws.iter_cols(1, ws.max_column):
        col_names[column[0].value] = nr_col
        nr_col += 1

    for index, row in enumerate(ws.iter_rows(2, ws.max_row), start=1):
        #time_00 = time.time()

        # wczytanie danych z xlsx
        nazwa = row[col_names['JPT_NAZWA_']].value
        if not nazwa:
            continue

        label_pl = label_en = 'województwo' + ' ' + nazwa

        teryt = row[col_names['JPT_KOD_JE']].value
        idiip = row[col_names['IIP_IDENTY']].value

        description_pl = 'województwo (jednostka administracyjna wg PRG)'
        description_en = 'województwo (jednostka administracyjna wg PRG)'

        # przygotowanie struktur wikibase
        data = []
        aliasy = []

        # time_01 = time.time()
        # time_diff = time_01 - time_00
        # time_01_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('przed statements :', time_01_len)

        # instance of
        statement = create_statement_data(p_instance_of, q_voivodship, None, None, add_ref_dict=onto_references)
        if statement:
            data.append(statement)

        # time_02 = time.time()
        # time_diff = time_02 - time_01
        # time_02_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('instance of      :', time_02_len)

        # id SDI
        if idiip:
            statement = create_statement_data(p_id_sdi, idiip, None, None, add_ref_dict=references)
            if statement:
                data.append(statement)

        # time_03 = time.time()
        # time_diff = time_03 - time_02
        # time_03_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('idiip            :', time_03_len)

        # TERYT
        if teryt:
            statement = create_statement_data(p_teryt, teryt, None, None, add_ref_dict=references)
            if statement:
                data.append(statement)

        # time_04 = time.time()
        # time_diff = time_04 - time_03
        # time_04_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('teryt            :', time_04_len)

        # JPT_NAZWA_
        aliasy.append(nazwa)
        statement = create_statement_data(p_stated_as, f'pl:"{nazwa}"', None, None, add_ref_dict=references)
        if statement:
            data.append(statement)

        # time_05 = time.time()
        # time_diff = time_05 - time_04
        # time_05_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('stated as        :', time_05_len)

        # etykiety, description, aliasy
        wb_item = wbi_core.ItemEngine(new_item=True, data=data)
        wb_item.set_label(label_en, lang='en')
        wb_item.set_label(label_pl,lang='pl')

        # description
        wb_item.set_description(description_en, 'en')
        wb_item.set_description(description_pl, 'pl')

        # time_06 = time.time()
        # time_diff = time_06 - time_05
        # time_06_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('label/description:', time_06_len)

        if aliasy:
            for value_alias in aliasy:
                wb_item.set_aliases(value_alias, 'pl')

        # time_07 = time.time()
        # time_diff = time_07 - time_06
        # time_07_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('aliasy           :', time_07_len)

        # wyszukiwanie po etykiecie, właściwości instance of oraz po opisie
        parameters = [(p_instance_of, q_voivodship)]
        ok, item_id = element_search_adv(label_en, 'en', parameters, description_en)

        # time_08 = time.time()
        # time_diff = time_08 - time_07
        # time_08_len = timedelta(seconds=time_diff, milliseconds=time_diff)
        # print('element search   :', time_08_len)

        if not ok:
            if WIKIBASE_WRITE:
                new_id = wb_item.write(login_instance, bot_account=True, entity_type='item')
                if new_id:
                    print(f'{index}/{ws.max_row - 1} Dodano nowy element: {label_en} / {label_pl} = {new_id}')
            else:
                new_id = 'TEST'
                print(f"{index}/{ws.max_row - 1} Przygotowano dodanie elementu - {label_en} / {label_pl}  = {new_id}")
        else:
            print(f'{index}/{ws.max_row - 1} Element: {label_en} / {label_pl} już istnieje: {item_id}')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
