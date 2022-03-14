import os 
import openpyxl
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator import wbi_login, wbi_datatype
from wikidariahtools import element_exists, element_search
from dotenv import load_dotenv
from pathlib import Path


TEST_ONLY = True

# adresy dla API Wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'


def add_property(login_instance: wbi_login.Login, data: dict) -> tuple:
    """
    funkcja dodaje nową właściwość
    zwraca tuple: (True/False, ID/ERROR) 
    """

    # test czy właściwość już nie istnieje
    result, id = element_search(data['label_en'], 'property', 'en')
    if result:
        print(f"Property: '{data['label_en']}' already exists: {id}")
        return False, f"[{data['label_en']}] exists - > {id}" 
    else:
        if TEST_ONLY:
            print(f"Property: '{data['label_en']}' is new.")
            return True, "ID" 

        wd_item = wbi_core.ItemEngine(new_item=True)
        wd_item.set_label(data['label_en'], lang='en')
        wd_item.set_description(data['description_en'], lang='en')

        if data['label_pl']:
            wd_item.set_label(data['label_pl'],lang='pl')
        if data['description_pl']:
            wd_item.set_description(data['description_pl'], lang='pl')

        # typy danych dla property: 'string', 'wikibase-item', 'wikibase-property', 
        # 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 
        # 'globe-coordinate'
        options = {'property_datatype':data['datatype']}
        
        try:
            id = wd_item.write(login_instance, bot_account=True, entity_type='property', **options)
            result = (True, id)
        except:
            result = (False, 'ERROR')
        finally:
            return result
    

if __name__ == "__main__":

    # login i hasło ze zmiennych środowiskowych 
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')
    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD) 

    # dane z arkusza XLSX
    filename = Path('.') / 'data/arkusz_import.xlsx'
    wb = openpyxl.load_workbook(filename)
    ws = wb['P_list']

    # kolumny w arkuszu
    col_names = {}
    nr_col = 0
    for column in ws.iter_cols(1, ws.max_column):
        col_names[column[0].value] = nr_col
        nr_col += 1

    max = ws.max_row

    for row in ws.iter_rows(2, max):
        dane = {}
        
        dane['label_en'] = row[col_names['Label_en']].value
        dane['description_en'] = row[col_names['Description_en']].value
        datatype = row[col_names['datatype']].value
        if datatype != None:
            if datatype == 'item':
                datatype = 'wikibase-item'
            elif datatype == 'property':
                datatype = 'wikibase-property'
        dane['datatype'] = datatype

        # tylko jeżeli etykieta i opis w języku angielskim oraz typ danych są wypełnione
        if dane['label_en'] and dane['description_en'] and dane['datatype']:
            dane['label_pl'] = row[col_names['Label_pl']].value
            dane['description_pl'] = row[col_names['Description_pl']].value
            dane['wiki_id'] = row[col_names['Wiki_id']].value
            dane['wiki_url'] = row[col_names['Wiki_url']].value
            dane['inverse_property'] = row[col_names['inverse_property']].value
            
            result, info = add_property(login_instance, dane)
