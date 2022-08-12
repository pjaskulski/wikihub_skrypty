""" skrypt usuwa niepoprawne elementy geo """

import os
import sys
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from dotenv import load_dotenv
from wikidariahtools import element_search_adv


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

WIKIBASE_WRITE = True

if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    with open('../log/duplikaty_jednostek.txt', 'r', encoding='utf-8') as f:
        items = f.readlines()

    p_ontohgis_database_id = 'P253'

    for item in items:
        item = item.strip()
        tmp = item.split('=')
        label = tmp[0]
        ontohgis_id = tmp[1]
        parameters = [(p_ontohgis_database_id, ontohgis_id)]
        ok, item_id = element_search_adv(label, 'en', parameters=parameters)
        if ok:
            if WIKIBASE_WRITE:
                params = {
                    'action': 'delete',
                    'title': f'Item:{item_id}'
                }

                try:
                    delete_results = mediawiki_api_call_helper(data=params, login=login_instance,
                                                    mediawiki_api_url=None)
                    print(delete_results)

                except MWApiError as e:
                    print('Error:', e)
                    sys.exit(1)
            else:
                print(f'Przygotowanio usunięcie: {item_id} {label}')
        else:
            print(f'ERROR: nie znaleziono: {label} {ontohgis_id}')
