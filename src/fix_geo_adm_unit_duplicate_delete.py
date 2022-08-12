""" skrypt usuwa niepoprawne elementy geo """

import os
from pathlib import Path
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from dotenv import load_dotenv
from wikidariahtools import statement_value_fix, get_property_type


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    items = []
    del_items = []
    for i in range(80340, 86452):
        test_item = f"Q{i}"
        wb_item = wbi_core.ItemEngine(item_id=test_item)
        label = wb_item.get_label('pl')
        print(i, '/', 81892, label)
        for statement in wb_item.statements:
            statement_property = statement.get_prop_nr()
            if statement_property == 'P253':
                statement_value = statement.get_value()
                statement_type = get_property_type(statement_property)
                statement_value = statement_value_fix(statement_value, statement_type)
                tmp = (f'{label}={statement_value}')
                if tmp in items:
                    del_items.append(tmp)
                else:
                    items.append(tmp)

    for item in del_items:
        print(item)
