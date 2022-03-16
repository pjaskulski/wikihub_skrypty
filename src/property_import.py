""" skrypt importujący właściwości z xlsx do wikibase """

import os
import sys
from pathlib import Path
from openpyxl import load_workbook
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, wbi_datatype
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from dotenv import load_dotenv
from wikidariahtools import element_search


TEST_ONLY = True     # jeżeli True to nie dodaje danych tylko informuje, czy jest to nowa właściwość

# adresy dla API Wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

class BasicProp:
    """ Identyfikatory podstawowych właściwości
    """
    def __init__(self):
        self.wiki_id = ''
        self.wiki_url = ''
        self.inverse = ''

    def get_wiki_properties(self):
        """ funkcja ustala nr podstawowych property związanych z wikidata.org
        """

        if self.wiki_id == '':
            search_result, pid = element_search('Wikidata ID', 'property', 'en')
            if search_result:
                self.wiki_id = pid
        if self.wiki_url == '':
            search_result, pid = element_search('Wikidata URL', 'property', 'en')
            if search_result:
                self.wiki_url = pid
        if self.inverse == '':
            search_result, pid = element_search('inverse property', 'property', 'en')
            if search_result:
                self.inverse = pid


def add_property(p_login_instance: wbi_login.Login, p_dane: dict) -> tuple:
    """
    funkcja dodaje nową właściwość
    zwraca tuple: (True/False, ID/ERROR)
    """

    # test czy właściwość już nie istnieje
    search_result, search_id = element_search(p_dane['label_en'], 'property', 'en')
    if search_result:
        print(f"Property: '{p_dane['label_en']}' already exists: {search_id}")
        return False, f"[{p_dane['label_en']}] exists - > {search_id}"

    if TEST_ONLY:
        print(f"Property: '{p_dane['label_en']}' is new.")
        return True, "ID"

    wd_item = wbi_core.ItemEngine(new_item=True)

    # etykiety i opisy
    wd_item.set_label(p_dane['label_en'], lang='en')
    wd_item.set_description(p_dane['description_en'], lang='en')
    if p_dane['label_pl']:
        wd_item.set_label(p_dane['label_pl'],lang='pl')
    if p_dane['description_pl']:
        wd_item.set_description(p_dane['description_pl'], lang='pl')

    # Wikidata ID i Wikidata URL
    wiki_dane = None
    if p_dane['wiki_id']:
        if wikibase_prop.wiki_id == '' or wikibase_prop.wiki_url == '':
            wikibase_prop.get_wiki_properties()

        wiki_id = p_dane['wiki_id'].strip()
        url = f"https://www.wikidata.org/wiki/Property:{wiki_id}"
        references = [
            [
                wbi_datatype.Url(value=url, prop_nr=wikibase_prop.wiki_url, is_reference=True)
            ]
        ]
        wiki_dane = wbi_datatype.ExternalID(value=wiki_id, prop_nr=wikibase_prop.wiki_id,
            references=references)

    # odwrotność właściwości
    inverse_dane = None
    if dane['inverse_property']:
        if wikibase_prop.inverse == '':
            wikibase_prop.get_wiki_properties()
        search_result, pid = element_search(p_dane['inverse_property'].strip(), 'property', 'en')
        if search_result and wikibase_prop.inverse != '':
            inverse_dane = wbi_datatype.Property(value=pid, prop_nr=wikibase_prop.inverse)

    # typy danych dla property: 'string', 'wikibase-item', 'wikibase-property',
    # 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url',
    # 'globe-coordinate'
    options = {'property_datatype':p_dane['datatype']}

    try:
        p_new_id = wd_item.write(p_login_instance, entity_type='property', **options)

        # deklaracje dla właściwości
        data = []
        if wiki_dane:
            data.append(wiki_dane)
        if inverse_dane:
            data.append(inverse_dane)

        if len(data) > 0:
            wd_statement = wbi_core.ItemEngine(item_id=p_new_id, data=data, debug=False)
            wd_statement.write(p_login_instance, entity_type='property')

        add_result = (True, p_new_id)

    except MWApiError:
        add_result = (False, 'ERROR')

    return add_result


def test_xlsx_columns(t_col_names: dict) -> bool:
    """
    funkcja weryfikuje czy XLSX zawiera oczekiwane kolumny
    """
    expected = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
    is_ok = True
    for item in expected:
        if not item in t_col_names:
            is_ok = False
            break

    return is_ok


def correct_type(t_datatype: str) -> str:
    """
    Funkcja ewentualnie koryguje typ właściwości na właściwy, zgodny z oczekiwanym
    przez Wikibase
    """
    if t_datatype is not None:
        if t_datatype == 'item':
            t_datatype = 'wikibase-item'
        elif t_datatype == 'property':
            t_datatype = 'wikibase-property'
        elif t_datatype == 'external identifier':
            t_datatype = 'external-id'

    return t_datatype


if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)

    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    # podstawowe właściwości Wikibase
    wikibase_prop = BasicProp()

    # ustalenie nr podstawowych property (jeżeli są, jeżeli będą dodawane podczas
    # pracy skryptu, wartości zostaną podczytane pred pierwszym użyciem)
    wikibase_prop.get_wiki_properties()

    # dane z arkusza XLSX, wg ścieżki przekazanej argumentem z linii komend
    # jeżeli nie przekazano, skrypt szuka pliku 'data/arkusz_import.xlsx'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = Path('.') / 'data/arkusz_import.xlsx'

    try:
        wb = load_workbook(filename)
    except IOError:
        print(f"ERROR. Can't open and process file: {filename}")
        sys.exit(1)

    # czy to jest właściwy plik? cz. 1
    SHEET = 'P_list'
    if not SHEET in wb.sheetnames:
        print(f"ERROR. Expected worksheet '{SHEET}' is missing in the file.")
        sys.exit(1)

    ws = wb[SHEET]

    # słownik kolumn w arkuszu
    col_names = {}
    nr_col = 0
    for column in ws.iter_cols(1, ws.max_column):
        col_names[column[0].value] = nr_col
        nr_col += 1

    # czy to właściwy plik?, cz.2
    if not test_xlsx_columns(col_names):
        print('ERROR. There are no expected columns in the worksheet.')
        sys.exit(1)

    max_row = ws.max_row

    for row in ws.iter_rows(2, max_row):
        dane = {}
        dane['label_en'] = row[col_names['Label_en']].value
        dane['description_en'] = row[col_names['Description_en']].value
        datatype = row[col_names['datatype']].value
        dane['datatype'] = correct_type(datatype)
        dane['label_pl'] = row[col_names['Label_pl']].value

        # tylko jeżeli etykieta i opis w języku angielskim oraz typ danych są wypełnione
        if dane['label_en'] and dane['description_en'] and dane['datatype']:
            dane['description_pl'] = row[col_names['Description_pl']].value
            dane['wiki_id'] = row[col_names['Wiki_id']].value
            dane['inverse_property'] = row[col_names['inverse_property']].value

            result, info = add_property(login_instance, dane)
            if result and not TEST_ONLY:
                print(f'Property added: {info}')
