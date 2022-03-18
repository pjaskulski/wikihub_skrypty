""" skrypt importujący właściwości z xlsx do wikibase """

import os
import sys
import re
from pathlib import Path
from typing import Union
from openpyxl import load_workbook
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, wbi_datatype
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from dotenv import load_dotenv
from wikidariahtools import element_search


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


def add_property(p_dane: dict) -> tuple:
    """
    funkcja dodaje nową właściwość
    zwraca tuple: (True/False, ID/ERROR)
    """

    # test czy właściwość już nie istnieje
    search_property, search_id = element_search(p_dane['label_en'], 'property', 'en')
    if search_property:
        print(f"Property: '{p_dane['label_en']}' already exists: {search_id}, update mode.")
        wd_item = wbi_core.ItemEngine(item_id=search_id)
    else:
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

        url = f"https://www.wikidata.org/wiki/Property:{p_dane['wiki_id']}"
        references = [
            [
                wbi_datatype.Url(value=url, prop_nr=wikibase_prop.wiki_url, is_reference=True)
            ]
        ]
        wiki_dane = wbi_datatype.ExternalID(value=p_dane['wiki_id'], prop_nr=wikibase_prop.wiki_id,
            references=references)

    # odwrotność właściwości
    inverse_dane = None
    if p_dane['inverse_property']:
        if wikibase_prop.inverse == '':
            wikibase_prop.get_wiki_properties()
        search_inverse, inv_pid = element_search(p_dane['inverse_property'], 'property', 'en')
        if search_inverse and wikibase_prop.inverse != '':
            inverse_dane = wbi_datatype.Property(value=inv_pid, prop_nr=wikibase_prop.inverse)

    # typy danych dla property: 'string', 'wikibase-item', 'wikibase-property',
    # 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url',
    # 'globe-coordinate'
    options = {'property_datatype':p_dane['datatype']}

    try:
        p_new_id = wd_item.write(login_instance, entity_type='property', **options)
        if search_property:
            p_new_id = search_id

        # deklaracje dla właściwości
        data = []
        if wiki_dane:
            data.append(wiki_dane)
        if inverse_dane:
            data.append(inverse_dane)

        if len(data) > 0:
            wd_statement = wbi_core.ItemEngine(item_id=p_new_id, data=data, debug=False)
            wd_statement.write(login_instance, entity_type='property')

        # jeżeli dodano właściwość inverse_property do dla docelowej właściwości należy 
        # dodać odwrotność: nową właściwość jako jej inverse_property
        if inverse_dane:
            add_res, add_info = add_property_statement(inv_pid, wikibase_prop.inverse, p_new_id)
            if not add_res:
                print(f'{add_info}')

        add_result = (True, p_new_id)

    except (MWApiError, KeyError):
        add_result = (False, 'ERROR')

    return add_result


def find_name_qid(name: str, elem_type: str) -> tuple:
    """Funkcja sprawdza czy przekazany argument jest identyfikatorem właściwości/elementu
       jeżeli nie to szuka w wikibase właściwości/elementu o etykiecie (ang) równej argumentowi
       i zwraca jej id
    """
    output = (True, name)               # zakładamy, że w name jest id (np. P47)
                                        # ale jeżeli nie, to szukamy w wikibase
    if elem_type == 'property':
        pattern = r'^P\d{1,9}$'
    elif elem_type == 'item':
        pattern = r'^Q\d{1,9}$'

    match = re.search(pattern, name)
    if not match:
        output = element_search(name, elem_type, 'en')
        if not output[0]:
            output =  (False, f'INVALID DATA, {elem_type}: {name}, {output[1]}')

    return output


def create_statement(prop: str, value: str, is_ref: bool = False, refs = None) ->Union[
                                                       wbi_datatype.String,
                                                       wbi_datatype.Property,
                                                       wbi_datatype.ItemID,
                                                       wbi_datatype.ExternalID,
                                                       wbi_datatype.Url,
                                                       wbi_datatype.Quantity,
                                                       wbi_datatype.Time,
                                                       wbi_datatype.GeoShape,
                                                       wbi_datatype.GlobeCoordinate,
                                                       wbi_datatype.MonolingualText]:
    """
    Funkcja tworzy obiekt będący deklaracją lub referencją
    """
    statement = None

    res, property_nr = find_name_qid(prop, 'property')
    if res:
        property_type = get_property_type(property_nr)
        if property_type == 'string':
            statement = wbi_datatype.String(value=value, prop_nr=property_nr,
                                            is_reference=is_ref, references=refs)
        elif property_type == 'wikibase-item':
            res, value_id = find_name_qid(value, 'item')
            if res:
                statement = wbi_datatype.ItemID(value=value_id, prop_nr=property_nr,
                                                is_reference=is_ref, references=refs)
        elif property_type == 'wikibase-property':
            res, value_id = find_name_qid(value, 'property')
            if res:
                statement = wbi_datatype.Property(value=value_id, prop_nr=property_nr,
                                                  is_reference=is_ref, references=refs)
        elif property_type == 'external-id':
            statement = wbi_datatype.ExternalID(value=value, prop_nr=property_nr,
                                                is_reference=is_ref, references=refs)
        elif property_type == 'url':
            statement = wbi_datatype.Url(value=value, prop_nr=property_nr,
                                         is_reference=is_ref, references=refs)
        elif property_type == 'monolingualtext':
            statement = wbi_datatype.MonolingualText(text=value, prop_nr=property_nr,
                                                     is_reference=is_ref, references=refs)
        elif property_type == 'quantity':
            statement = wbi_datatype.Quantity(quantity=value, prop_nr=property_nr,
                                              is_reference=is_ref, references=refs)
        elif property_type == 'time':
            tmp = value.split("/")
            if len(tmp) == 2:
                time_value = tmp[0]
                precision = int(tmp[1])
                statement = wbi_datatype.Time(time_value, prop_nr=property_nr,
                                              precision=precision, is_reference=is_ref,
                                              references=refs)
            else:
                print(f'ERROR: invalid value for time type: {value}.')
        elif property_type == 'geo-shape':
            statement = wbi_datatype.GeoShape(value, prop_nr=property_nr, is_reference=is_ref,
                                              references=refs)
        elif property_type == 'globe-coordinate':
            tmp = value.split(",")
            try:
                latitude = float(tmp[0])
                longitude = float(tmp[1])
                if len(tmp) > 2:
                    precision = float(tmp[2])
                else:
                    precision = 0.1
            except ValueError:
                print(f'ERROR: invalid value for globe-coordinate type: {value}.')
            else:
                statement = wbi_datatype.GlobeCoordinate(latitude, longitude, precision,
                                                         prop_nr=property_nr, is_reference=is_ref,
                                                         references=refs)

    return statement


def create_references(ref_property: str, ref_value: str) ->list:
    """ Funkcja tworzy referencje
    """
    statement = create_statement(ref_property, ref_value, is_ref=True, refs=None)
    if statement:
        new_references = [[ statement ]]
    else:
        new_references = None

    return new_references


def create_statement_data(prop: str, value: str, ref_prop: str, ref_value: str) -> Union[
                                                       wbi_datatype.String,
                                                       wbi_datatype.Property,
                                                       wbi_datatype.ItemID,
                                                       wbi_datatype.ExternalID,
                                                       wbi_datatype.Url,
                                                       wbi_datatype.Quantity,
                                                       wbi_datatype.Time,
                                                       wbi_datatype.GeoShape,
                                                       wbi_datatype.GlobeCoordinate,
                                                       wbi_datatype.MonolingualText]:
    """
    Funkcja tworzy dane deklaracji z opcjonalnymy referencjami
    """
    references = None
    if ref_prop and ref_value :
        references = create_references(ref_prop, ref_value)
        print(references)

    output_data = create_statement(prop, value, is_ref=False, refs=references)

    return output_data


def add_property_statement(p_id: str, prop_label: str, value: str,
                           reference_type: str = '', reference_value: str = '' ) -> tuple:
    """
    Funkcja dodaje deklaracje (statement) do właściwości
    Parametry:
        p_id - etykieta właściwości lub jej P, do której jest dodawana deklaracja
        prop_label - etykieta właściwości
        value - dodawana wartość
    """
    is_ok, p_id = find_name_qid(p_id, 'property')
    if not is_ok:
        return (False, p_id)

    is_ok, prop_id = find_name_qid(prop_label, 'property')
    if not is_ok:
        return (False, prop_id)

    prop_type = get_property_type(prop_id)
    if prop_type == 'wikibase-item':
        is_ok, value_id = find_name_qid(value, 'item')
        if not is_ok:
            return (False, value_id)

    if prop_type == 'wikibase-property':
        is_ok, value_id = find_name_qid(value, 'property')
        if not is_ok:
            return (False, value_id)

    st_data = None
    # jeżeli w prop_label jest ang. etykieta właściwości, zwraca jej ID, jeżeli
    # jest ID, zwraca bez zmian

    st_data = create_statement_data(prop_label, value, reference_type, reference_value)
    if st_data:
        try:
            data =[st_data]
            wd_statement = wbi_core.ItemEngine(item_id=p_id, data=data, debug=False)
            wd_statement.write(login_instance, entity_type='property')
            add_result = (True, f'STATEMENT ADDED, {p_id}: - {prop_id} -> {value}')
        except (MWApiError, KeyError, ValueError):
            add_result = (False, f'ERROR, {p_id}: - {prop_id} -> {value}')
    else:
        add_result = (False, f'INVALID DATA, {p_id}: - {prop_id} -> {value}')

    return add_result


def test_xlsx_columns(t_col_names: dict, expected: list) -> tuple:
    """
    funkcja weryfikuje czy XLSX zawiera oczekiwane kolumny
    """
    missing_cols = []
    res = True
    for col in expected:
        if not col in t_col_names:
            missing_cols.append(col)
            res = False

    return res, ",".join(missing_cols)


def get_col_names(sheet) -> dict:
    """ funkcja zwraca słownik nazw kolumn
    """
    names = {}
    nr_col = 0
    for column in sheet.iter_cols(1, sheet.max_column):
        names[column[0].value] = nr_col
        nr_col += 1

    return names


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


def get_property_list(sheet) -> list:
    """ zwraca listę właściwości do dodania
    """
    max_row = sheet.max_row
    p_list = []
    for row in sheet.iter_rows(2, max_row):
        basic_cols = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
        p_item = {}
        for col in basic_cols:
            key = col.lower()
            p_item[key] = row[col_names[col]].value
            if p_item[key] is not None:
                p_item[key] = p_item[key].strip()
                if key == 'datatype':
                    p_item[key] = correct_type(p_item[key])

        # tylko jeżeli etykieta i opis w języku angielskim oraz typ danych są wypełnione
        # dane właściwości są dodawane do listy
        if p_item['label_en'] and p_item['description_en'] and p_item['datatype']:
            extend_cols = ['Description_pl', 'Wiki_id', 'inverse_property']
            for col in extend_cols:
                key = col.lower()
                p_item[key] = row[col_names[col]].value
                if p_item[key] is not None:
                    p_item[key] = p_item[key].strip()

            p_list.append(p_item)

    return p_list


def get_statement_list(sheet) -> list:
    """ zwraca listę deklaracji do dodania
    """
    max_row = sheet.max_row
    s_list = []
    for row in sheet.iter_rows(2, max_row):
        basic_cols = ['Label_en', 'P', 'value', 'reference_property', 'reference_value']
        s_item = {}
        for col in basic_cols:
            key = col.lower()
            s_item[key] = row[col_names[col]].value
            if s_item[key] is not None:
                s_item[key] = s_item[key].strip()

        # tylko jeżeli etykieta w języku angielskim, właściwość i wartość są wypełnione
        # dane deklaracji są dodawane do listy
        if s_item['label_en'] and s_item['p'] and s_item['value']:
            s_list.append(s_item)

    return s_list


def get_property_type(p_id: str) -> str:
    """ Funkcja zwraca typ właściwości na podstawie jej identyfikatora
    """
    params = {'action': 'wbgetentities', 'ids': p_id,
              'props': 'datatype'}

    search_results = mediawiki_api_call_helper(data=params, login=None, mediawiki_api_url=None,
                                               user_agent=None, allow_anonymous=True)
    data_type = None
    if search_results:
        data_type = search_results['entities'][p_id]['datatype']

    return data_type


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
    SHEETS = ['P_list', 'P_statments']
    for item in SHEETS:
        if not item in wb.sheetnames:
            print(f"ERROR. Expected worksheet '{item}' is missing in the file.")
            sys.exit(1)

    ws = wb[SHEETS[0]]

    # słownik kolumn w arkuszu
    col_names = get_col_names(ws)

    # czy to właściwa struktura skoroszytu arkusza xmlx?
    exp_col_names = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
    result, info = test_xlsx_columns(col_names, exp_col_names)
    if not result:
        print(f'ERROR. The expected columns ({info}) are missing.')
        sys.exit(1)

    dane = get_property_list(ws)
    for wb_property in dane:
        result, info = add_property(wb_property)
        if result:
            print(f'Property added: {info}')

    ws = wb[SHEETS[1]]

    # słownik kolumn w arkuszu
    col_names = get_col_names(ws)

    # czy to właściwa struktura skoroszytu arkusza xmlx?
    exp_col_names = ['Label_en', 'P', 'value']
    result, info = test_xlsx_columns(col_names, exp_col_names)
    if not result:
        print(f'ERROR. The expected columns ({info}) are missing.')
        sys.exit(1)

    dane = get_statement_list(ws)
    for stm in dane:
        result, info = add_property_statement(stm['label_en'], stm['p'], stm['value'],
                                              stm['reference_property'], stm['reference_value'])
        print(f'{info}')
