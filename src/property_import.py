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


class WDHSpreadsheet:
    """ Plik arkusza kalkulacyjnego z modelem danych dla Wikibase
    """
    def __init__(self, path: str):
        self.path = path
        self.sheets = ['P_list', 'P_statments', 'Q_list', 'Q_statements']
        self.p_list = None          # arkusz z listą właściwości
        self.p_statements = None    # arkusz z listą deklaracji dla właściwości
        self.workbook = None
        self.property_columns = []
        self.statement_columns = []
        self.i_list = None          # arkusz z listą elementów (item)
        self.i_statements = None    # arkusz z listą deklaracji dla elementów
        self.item_columns = []
        self.item_statement_columns = []

    @property
    def path(self) -> str:
        """ get path """
        return self._path

    @path.setter
    def path(self, value: str):
        """ set path """
        self._path = value

    def open(self):
        """ odczyt pliku i weryfikacja poprawności """
        try:
            self.workbook = load_workbook(self.path)
        except IOError:
            print(f"ERROR. Can't open and process file: {self.path}")
            sys.exit(1)

        # czy to jest właściwy plik? cz. 1
        for sheet in self.sheets:
            if not sheet in self.workbook.sheetnames:
                print(f"ERROR. Expected worksheet '{sheet}' is missing in the file.")
                sys.exit(1)

        # arlkusz właściwości
        self.p_list = self.workbook[self.sheets[0]]
        self.property_columns = self.get_col_names(self.p_list)
        p_list_expected = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
        res, inf = self.test_columns(self.property_columns, p_list_expected)
        if not res:
            print(f'ERROR. Worksheet {self.sheets[0]}. The expected columns ({inf}) are missing.')
            sys.exit(1)

        # arkusz deklaracji dla właściwości
        self.p_statements = self.workbook[self.sheets[1]]
        self.statement_columns = self.get_col_names(self.p_statements)
        p_statements_expected = ['Label_en', 'P', 'value', 'reference_property', 'reference_value']
        res, inf = self.test_columns(self.statement_columns, p_statements_expected)
        if not res:
            print(f'ERROR. Worksheet {self.sheets[1]}. The expected columns ({inf}) are missing.')
            sys.exit(1)

        # arkusz elementów
        self.i_list = self.workbook[self.sheets[2]]
        self.item_columns = self.get_col_names(self.i_list)
        i_list_expected = ['Label_en', 'Label_pl', 'also_known_as_en', 'also_known_as_pl',
                           'Description_en', 'Description_pl', 'Wiki_id']
        res, inf = self.test_columns(self.item_columns, i_list_expected)
        if not res:
            print(f'ERROR. Worksheet {self.sheets[2]}. The expected columns ({inf}) are missing.')
            sys.exit(1)

        # arkusz deklaracji dla elementów
        self.i_statements = self.workbook[self.sheets[3]]
        self.item_statement_columns = self.get_col_names(self.i_statements)
        i_statements_expected = ['Label_en', 'Label_pl', 'Value']
        res, inf = self.test_columns(self.item_statement_columns, i_statements_expected)
        if not res:
            print(f'ERROR. Worksheet {self.sheets[3]}. The expected columns ({inf}) are missing.')
            sys.exit(1)


    def test_columns(self, t_col_names: dict, expected: list) -> tuple:
        """ weryfikuje czy arkusz zawiera oczekiwane kolumny """
        missing_cols = []
        res = True
        for col in expected:
            if not col in t_col_names:
                missing_cols.append(col)
                res = False

        return res, ",".join(missing_cols)


    def get_col_names(self, sheet) -> dict:
        """ funkcja zwraca słownik nazw kolumn
        """
        names = {}
        nr_col = 0
        for column in sheet.iter_cols(1, sheet.max_column):
            names[column[0].value] = nr_col
            nr_col += 1

        return names


    def correct_type(self, t_datatype: str) -> str:
        """ Funkcja ewentualnie koryguje typ właściwości na właściwy, zgodny z oczekiwanym
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

    def get_property_list(self) -> list:
        """ zwraca listę właściwości (w formie obiektów WDHProperty) do dodania
        """
        p_list = []
        for row in self.p_list.iter_rows(2, self.p_list.max_row):
            basic_cols = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
            p_item = {}
            p_item = WDHProperty()
            for col in basic_cols:
                key = col.lower()
                col_value = row[self.property_columns[col]].value
                if key == 'label_en':
                    p_item.label_en = col_value
                elif key == 'description_en':
                    p_item.description_en = col_value
                elif key == 'datatype':
                    p_item.datatype = col_value
                elif key == 'label_pl':
                    p_item.label_pl = col_value

            # tylko jeżeli etykieta i opis w języku angielskim oraz typ danych są wypełnione
            # dane właściwości są dodawane do listy
            if p_item.label_en and p_item.description_en and p_item.datatype and p_item.label_pl:
                extend_cols = ['Description_pl', 'Wiki_id', 'inverse_property']
                for col in extend_cols:
                    key = col.lower()
                    col_value = row[self.property_columns[col]].value
                    if key == 'description_pl':
                        p_item.description_pl = col_value
                    elif key == 'wiki_id':
                        p_item.wiki_id = col_value
                    elif key == 'inverse_property':
                        p_item.inverse_property = col_value

                p_list.append(p_item)

        return p_list

    def get_statement_list(self) -> list:
        """ zwraca listę obiektów deklaracji do dodania
        """
        s_list = []
        for row in self.p_statements.iter_rows(2, self.p_statements.max_row):
            basic_cols = ['Label_en', 'P', 'value', 'reference_property', 'reference_value']
            s_item = WDHStatement()
            for col in basic_cols:
                key = col.lower()
                col_value = row[self.statement_columns[col]].value

                if key == 'label_en':
                    s_item.label_en = col_value
                elif key == 'p':
                    s_item.statement_property = col_value
                elif key == 'value':
                    s_item.statement_value = col_value
                elif key == 'reference_property':
                    s_item.reference_property = col_value
                elif key == 'reference_value':
                    s_item.reference_value = col_value

            # tylko jeżeli etykieta w języku angielskim, właściwość i wartość są wypełnione
            # dane deklaracji są dodawane do listy
            if s_item.label_en and s_item.statement_property and s_item.statement_value:
                s_list.append(s_item)

        return s_list

    def get_item_list(self) -> list:
        """ zwraca listę elementów (w formie obiektów WDHItem) do dodania
        """
        i_list = []
        for row in self.i_list.iter_rows(2, self.i_list.max_row):
            basic_cols = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
            p_item = WDHItem()
            for col in basic_cols:
                key = col.lower()
                col_value = row[self.property_columns[col]].value
                if key == 'label_en':
                    p_item.label_en = col_value
                elif key == 'description_en':
                    p_item.description_en = col_value
                elif key == 'datatype':
                    p_item.datatype = col_value
                elif key == 'label_pl':
                    p_item.label_pl = col_value

            # tylko jeżeli etykieta i opis w języku angielskim oraz typ danych są wypełnione
            # dane właściwości są dodawane do listy
            if p_item.label_en and p_item.description_en and p_item.datatype and p_item.label_pl:
                extend_cols = ['Description_pl', 'Wiki_id', 'inverse_property']
                for col in extend_cols:
                    key = col.lower()
                    col_value = row[self.property_columns[col]].value
                    if key == 'description_pl':
                        p_item.description_pl = col_value
                    elif key == 'wiki_id':
                        p_item.wiki_id = col_value
                    elif key == 'inverse_property':
                        p_item.inverse_property = col_value

                p_list.append(p_item)

        return p_list


class WDHProperty:
    """ Klasa dla właściwości (property)
    """
    def __init__(self, label_en: str = '', description_en: str = '', datatype: str = '',
                 label_pl: str = '', description_pl: str = '', wiki_id: str = '',
                 inverse_property: str = ''):
        self.label_en = label_en
        self.description_en = description_en
        self.datatype = datatype
        self.label_pl = label_pl
        self.description_pl = description_pl
        self.wiki_id = wiki_id
        self.inverse_property = inverse_property

    @property
    def label_en(self) -> str:
        """ get label_en """
        return self._label_en

    @label_en.setter
    def label_en(self, value: str):
        """ set label_en """
        if value:
            self._label_en = value.strip()
        else:
            self._label_en = ''

    @property
    def description_en(self) -> str:
        """ get description_en """
        return self._description_en

    @description_en.setter
    def description_en(self, value: str):
        """ set description_en """
        if value:
            self._description_en = value.strip()
        else:
            self._description_en = ''

    @property
    def datatype(self) -> str:
        """ get datatype """
        return self._datatype

    @datatype.setter
    def datatype(self, value: str):
        """ set datatype """
        if value:
            if value == 'item':
                value = 'wikibase-item'
            elif value == 'property':
                value = 'wikibase-property'
            elif value == 'external identifier':
                value = 'external-id'
            self._datatype = value.strip()
        else:
            self._datatype = ''

    @property
    def label_pl(self) -> str:
        """ get label_pl """
        return self._label_pl

    @label_pl.setter
    def label_pl(self, value: str):
        """ set label_pl """
        if value:
            self._label_pl = value.strip()
        else:
            self._label_pl = ''

    @property
    def description_pl(self) -> str:
        """ get description_pl """
        return self._description_pl

    @description_pl.setter
    def description_pl(self, value: str):
        """ set description_pl """
        if value:
            self._description_pl = value.strip()
        else:
            self._description_pl = ''

    @property
    def wiki_id(self) -> str:
        """ get wiki_id """
        return self._wiki_id

    @wiki_id.setter
    def wiki_id(self, value: str):
        """ set wiki_id """
        if value:
            self._wiki_id = value.strip()
        else:
            self._wiki_id = ''

    @property
    def inverse_property(self) -> str:
        """ get inverse_property """
        return self._inverse_property

    @inverse_property.setter
    def inverse_property(self, value: str):
        """ set inverse_property """
        if value:
            self._inverse_property = value.strip()
        else:
            self._inverse_property = ''

    def write_to_wikibase(self):
        """ zapis właściwości w instancji wikibase """
        pass


class WDHStatement:
    """ Klasa dla deklaracji (statement)
    """
    def __init__(self, label_en: str = '', statement_property: str = '',
                 statement_value: str = '', reference_property: str = '',
                 reference_value: str = ''):
        self.label_en = label_en
        self.statement_property = statement_property
        self.statement_value = statement_value
        self.reference_property = reference_property
        self.reference_value = reference_value

    @property
    def label_en(self) -> str:
        """ getter: label_en """
        return self._label_en

    @label_en.setter
    def label_en(self, value: str):
        """ setter: label_en """
        if value:
            self._label_en = value.strip()
        else:
            self._label_en = ''

    @property
    def statement_property(self) -> str:
        """ get statement_property """
        return self._statement_property

    @statement_property.setter
    def statement_property(self, value: str):
        """ set statement_property"""
        if value:
            self._statement_property = value.strip()
        else:
            self._statement_property = ''

    @property
    def statement_value(self):
        """ get statement_value """
        return self._statement_value

    @statement_value.setter
    def statement_value(self, value: str):
        """ set statement_value"""
        if value:
            self._statement_value = value.strip()
        else:
            self._statement_value = ''

    @property
    def reference_property(self):
        """ get reference_property """
        return self._reference_property

    @reference_property.setter
    def reference_property(self, value: str):
        """ set reference_property"""
        if value:
            self._reference_property = value.strip()
        else:
            self._reference_property = ''

    @property
    def reference_value(self):
        """ gettet: reference_value """
        return self._reference_value

    @reference_value.setter
    def reference_value(self, value: str):
        """ setter: reference_value"""
        if value:
            self._reference_value = value.strip()
        else:
            self._reference_property = ''

    def write_to_wikibase(self):
        """ zapis deklaracji w instancji wikibase """
        pass



class WDHItem:
    """ Klasa dla elementu (item)
    """
    def __init__(self, label_en: str = '', description_en: str = '', alias_en: str = '',
                 label_pl: str = '', description_pl: str = '', alias_pl: str = '',
                 wiki_id: str = ''):
        self.label_en = label_en
        self.description_en = description_en
        self.alias_en = alias_en
        self.label_pl = label_pl
        self.description_pl = description_pl
        self.alias_pl = alias_pl
        self.wiki_id = wiki_id

    @property
    def label_en(self) -> str:
        """ get label_en """
        return self._label_en

    @label_en.setter
    def label_en(self, value: str):
        """ set label_en """
        if value:
            self._label_en = value.strip()
        else:
            self._label_en = ''

    @property
    def description_en(self) -> str:
        """ get description_en """
        return self._description_en

    @description_en.setter
    def description_en(self, value: str):
        """ set description_en """
        if value:
            self._description_en = value.strip()
        else:
            self._description_en = ''

    @property
    def alias_en(self) -> str:
        """ get alias_en """
        return self._alias_en

    @alias_en.setter
    def alias_en(self, value: str):
        """ set alias_en """
        if value:
            tmp = value.split('|')
            self._alias_en = [element.strip() for element in tmp]
        else:
            self._alias_en = []

    @property
    def label_pl(self) -> str:
        """ get label_pl """
        return self._label_pl

    @label_pl.setter
    def label_pl(self, value: str):
        """ set label_pl """
        if value:
            self._label_pl = value.strip()
        else:
            self._label_pl = ''

    @property
    def description_pl(self) -> str:
        """ get description_pl """
        return self._description_pl

    @description_pl.setter
    def description_pl(self, value: str):
        """ set description_pl """
        if value:
            self._description_pl = value.strip()
        else:
            self._description_pl = ''

    @property
    def alias_pl(self) -> str:
        """ get alias_pl """
        return self._alias_pl

    @alias_pl.setter
    def alias_pl(self, value: str):
        """ set alias_pl """
        if value:
            tmp = value.split('|')
            self._alias_pl = [element.strip() for element in tmp]
        else:
            self._alias_pl = []

    @property
    def wiki_id(self) -> str:
        """ get wiki_id """
        return self._wiki_id

    @wiki_id.setter
    def wiki_id(self, value: str):
        """ set wiki_id """
        if value:
            self._wiki_id = value.strip()
        else:
            self._wiki_id = ''

    def write_to_wikibase(self):
        """ zapis właściwości w instancji wikibase """
        pass


def add_property(p_dane: WDHProperty) -> tuple:
    """
    funkcja dodaje nową właściwość
    zwraca tuple: (True/False, ID/ERROR)
    """

    # test czy właściwość już nie istnieje
    search_property, search_id = element_search(p_dane.label_en, 'property', 'en')
    if search_property:
        print(f"Property: '{p_dane.label_en}' already exists: {search_id}, update mode.")
        wd_item = wbi_core.ItemEngine(item_id=search_id)
        mode = 'updated: '
    else:
        wd_item = wbi_core.ItemEngine(new_item=True)
        mode = 'added: '

    # etykiety i opisy
    wd_item.set_label(p_dane.label_en, lang='en')
    wd_item.set_description(p_dane.description_en, lang='en')
    if p_dane.label_pl:
        wd_item.set_label(p_dane.label_pl,lang='pl')
    if p_dane.description_pl:
        wd_item.set_description(p_dane.description_pl, lang='pl')

    # Wikidata ID i Wikidata URL
    wiki_dane = None
    if p_dane.wiki_id:
        if wikibase_prop.wiki_id == '' or wikibase_prop.wiki_url == '':
            wikibase_prop.get_wiki_properties()

        url = f"https://www.wikidata.org/wiki/Property:{p_dane.wiki_id}"
        references = [
            [
                wbi_datatype.Url(value=url, prop_nr=wikibase_prop.wiki_url, is_reference=True)
            ]
        ]
        wiki_dane = wbi_datatype.ExternalID(value=p_dane.wiki_id, prop_nr=wikibase_prop.wiki_id,
            references=references)

    # odwrotność właściwości
    inverse_dane = None
    if p_dane.inverse_property:
        if wikibase_prop.inverse == '':
            wikibase_prop.get_wiki_properties()
        search_inverse, inv_pid = element_search(p_dane.inverse_property, 'property', 'en')
        if search_inverse and wikibase_prop.inverse != '':
            inverse_dane = wbi_datatype.Property(value=inv_pid, prop_nr=wikibase_prop.inverse)

    # typy danych dla property: 'string', 'wikibase-item', 'wikibase-property',
    # 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url',
    # 'globe-coordinate'
    options = {'property_datatype':p_dane.datatype}

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
            inv_statement = WDHStatement(inv_pid, wikibase_prop.inverse, p_new_id)
            add_res, add_info = add_property_statement(inv_statement)
            if not add_res:
                print(f'{add_info}')

        add_result = (True, mode + p_new_id)

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

    output_data = create_statement(prop, value, is_ref=False, refs=references)

    return output_data


def add_property_statement(s_item: WDHStatement) -> tuple:
    """
    Funkcja dodaje deklaracje (statement) do właściwości
    Parametry:
        s_item - obiekt z deklaracją
    """
    is_ok, p_id = find_name_qid(s_item.label_en, 'property')
    if not is_ok:
        return (False, p_id)

    is_ok, prop_id = find_name_qid(s_item.statement_property, 'property')
    if not is_ok:
        return (False, prop_id)

    prop_type = get_property_type(prop_id)
    if prop_type == 'wikibase-item':
        is_ok, value_id = find_name_qid(s_item.statement_value, 'item')
        if not is_ok:
            return (False, value_id)

    if prop_type == 'wikibase-property':
        is_ok, value_id = find_name_qid(s_item.statement_value, 'property')
        if not is_ok:
            return (False, value_id)

    if has_statement(p_id, prop_id):
        return (False, f"SKIP: property: '{p_id}' already has a statement: '{prop_id}'.")

    st_data = create_statement_data(s_item.statement_property, s_item.statement_value, 
                                    s_item.set_reference_property, s_item.reference_value)
    if st_data:
        try:
            data =[st_data]
            wd_statement = wbi_core.ItemEngine(item_id=p_id, data=data, debug=False)
            wd_statement.write(login_instance, entity_type='property')
            add_result = (True, f'STATEMENT ADDED, {p_id}: {prop_id} -> {s_item.statement_value}')
        except (MWApiError, KeyError, ValueError):
            add_result = (False, f'ERROR, {p_id}: {prop_id} -> {s_item.statement_value}')
    else:
        add_result = (False, f'INVALID DATA, {p_id}: {prop_id} -> {s_item.statement_value}')

    return add_result


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


def has_statement(pid_to_check: str, claim_to_check: str):
    """
    Funkcja weryfikuje czy właściwość (property) lub element (item) ma już
    taką deklarację (statement)
    """
    has_claim = False
    wb_prop = wbi_core.ItemEngine(item_id=pid_to_check)
    data_prop = wb_prop.get_json_representation()
    claims = data_prop['claims']
    if claim_to_check in claims:
        has_claim = True

    return has_claim


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

    plik_xlsx = WDHSpreadsheet(filename)
    plik_xlsx.open()

    # właściwośći
    dane = plik_xlsx.get_property_list()
    for wb_property in dane:
        result, info = add_property(wb_property)
        if result:
            print(f'Property {info}')

    # dodatkowe deklaracje
    dane = plik_xlsx.get_statement_list()
    for stm in dane:
        result, info = add_property_statement(stm)
        print(f'{info}')

    # elementy 'strukruralne' ('definicyjne')
    dane_elementy = plik_xlsx.get_item_list()
