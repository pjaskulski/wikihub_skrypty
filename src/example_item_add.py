""" skrypt dodaje nowy element z etykietami i opisem (en, pl) """

import os
from pathlib import Path
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, wbi_datatype
from dotenv import load_dotenv


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    # nowy element
    wd_item = wbi_core.ItemEngine(new_item=True)
    wd_item.set_label('Domenico Zaviazello', lang='en')
    wd_item.set_label('Domenico Zaviazello',lang='pl')
    wd_item.set_description('wenecki mistrz szkutniczy', lang='en')
    wd_item.set_description('wenecki mistrz szkutniczy', lang='pl')

    new_id = wd_item.write(login_instance, bot_account=True, entity_type='item')
    print(new_id)

    # właściwość: given name (P184)
    moje_dane = wbi_datatype.ItemID(value='Q9578', prop_nr='P184')
    data = [moje_dane]
    wd_item = wbi_core.ItemEngine(item_id=new_id, data=data, debug=False)
    wd_item.write(login_instance, entity_type='item')
