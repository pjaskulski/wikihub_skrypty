import os
import openpyxl
import sys
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator import wbi_login, wbi_datatype
from wikidariahtools import element_exists, element_search
from dotenv import load_dotenv
from pathlib import Path


TEST_ONLY = True     # jeżeli True to nie dodaje danych tylko informuje, czy jest to nowa właściwość
PROP_WIKI_ID = ''
PROP_WIKI_URL = ''
PROP_INVERSE = ''

# adresy dla API Wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'


def add_property(login_instance: wbi_login.Login, dane: dict) -> tuple:
    """
    funkcja dodaje nową właściwość
    zwraca tuple: (True/False, ID/ERROR) 
    """

    # test czy właściwość już nie istnieje
    result, id = element_search(dane['label_en'], 'property', 'en')
    if result:
        print(f"Property: '{dane['label_en']}' already exists: {id}")
        return False, f"[{dane['label_en']}] exists - > {id}" 
    else:
        if TEST_ONLY:
            print(f"Property: '{dane['label_en']}' is new.")
            return True, "ID" 

        wd_item = wbi_core.ItemEngine(new_item=True)
        
        # etykiety i opisy
        wd_item.set_label(dane['label_en'], lang='en')
        wd_item.set_description(dane['description_en'], lang='en')
        if dane['label_pl']:
            wd_item.set_label(dane['label_pl'],lang='pl')
        if dane['description_pl']:
            wd_item.set_description(dane['description_pl'], lang='pl')

        # Wikidata ID i Wikidata URL
        if dane['wiki_id']:
            if PROP_WIKI_ID == '' or PROP_WIKI_URL == '':
                get_wiki_properties()

            wiki_id = dane['wiki_id'].strip()
            url = f"https://www.wikidata.org/wiki/Property:{wiki_id}"
            references = [
                [
                    wbi_datatype.Url(value=url, prop_nr=PROP_WIKI_URL, is_reference=True)
                ]
            ]
            wiki_dane = wbi_datatype.ExternalID(value=wiki_id, prop_nr=PROP_WIKI_ID, references=references)
        else:
            wiki_dane = None

        # odwrotność właściwości 
        inverse_dane = None
        if dane['inverse_property']:
            if PROP_INVERSE == '':
                get_wiki_properties()
            property_name = dane['inverse_property'].strip()
            result, pid = element_search(property_name, 'property', 'en')
            if result and PROP_INVERSE != '':
                inverse_dane = wbi_datatype.Property(value=pid, prop_nr=PROP_INVERSE)
            
        # typy danych dla property: 'string', 'wikibase-item', 'wikibase-property', 
        # 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 
        # 'globe-coordinate'
        options = {'property_datatype':dane['datatype']}
        
        try:
            id = wd_item.write(login_instance, bot_account=True, entity_type='property', **options)
            
            # deklaracje dla właściwości 
            data = []
            if wiki_dane: data.append(wiki_dane)
            if inverse_dane: data.append(inverse_dane)
            if len(data) > 0: 
                wd_statement = wbi_core.ItemEngine(item_id=id, data=data, debug=False)
                wd_statement.write(login_instance, entity_type='property')

            result = (True, id)

        except:
            result = (False, 'ERROR')
        
        finally:
            return result


def test_xlsx_columns(col_names: dict) -> bool:
    """
    funkcja weryfikuje czy XLSX zawiera oczekiwane kolumny
    """
    expected = ['Label_en', 'Description_en', 'datatype', 'Label_pl']
    is_ok = True
    for item in expected:
        if not item in col_names:
            is_ok = False
            break

    return is_ok 


def correct_type(datatype: str) -> str:
    """
    Funkcja ewentualnie koryguje typ właściwości na właściwy, zgodny z oczekiwanym
    przez Wikibase
    """
    if datatype != None:
        if datatype == 'item':
            datatype = 'wikibase-item'
        elif datatype == 'property':
            datatype = 'wikibase-property'
        elif datatype == 'external identifier':
            datatype = 'external-id'
    
    return datatype


def get_wiki_properties():
    """
    funkcja ustala nr podstawowych property związanych z wikidata.org
    """   
    global PROP_WIKI_ID
    global PROP_WIKI_URL
    global PROP_INVERSE

    if PROP_WIKI_ID == '':
        result, pid = element_search('Wikidata ID', 'property', 'en')
        if result: PROP_WIKI_ID = pid
    if PROP_WIKI_URL == '':
        result, pid = element_search('Wikidata URL', 'property', 'en')
        if result: PROP_WIKI_URL = pid
    if PROP_INVERSE == '':
        result, pid = element_search('inverse property', 'property', 'en')
        if result: PROP_INVERSE = pid


if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych 
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')
    
    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD) 

    # ustalenie nr podstawowych property (jeżeli są, jeżeli będą dodawane podczas
    # pracy skryptu, wartości zostaną podczytane pred pierwszym użyciem)
    get_wiki_properties()    
    
    # dane z arkusza XLSX, wg ścieżki przekazanej argumentem z linii komend
    # jeżeli nie przekazano, skrypt szuka pliku 'data/arkusz_import.xlsx'
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = Path('.') / 'data/arkusz_import.xlsx'
    
    try:
        wb = openpyxl.load_workbook(filename)
    except:
        print(f"ERROR. Can't open and process file: {filename}")
        exit(1)

    # czy to jest właściwy plik? cz. 1
    sheet = 'P_list'
    if not sheet in wb.sheetnames:
        print(f"ERROR. Expected worksheet '{sheet}' is missing in the file.")
        exit(1)

    ws = wb[sheet]

    # słownik kolumn w arkuszu
    col_names = {}
    nr_col = 0
    for column in ws.iter_cols(1, ws.max_column):
        col_names[column[0].value] = nr_col
        nr_col += 1

    # czy to właściwy plik?, cz.2    
    if not test_xlsx_columns(col_names):
        print(f'ERROR. There are no expected columns in the worksheet.')
        exit(1)

    max = ws.max_row

    for row in ws.iter_rows(2, max):
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
