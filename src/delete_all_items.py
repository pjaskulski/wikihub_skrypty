""" usunięcie wszystkich elementów z wikibase"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import delete_property_or_item


# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')


# --------------------------------- MAIN ---------------------------------------
if __name__ == '__main__':
    log_path = Path("..") / "log" / "delete_all_items.log"

    # pomiar czasu wykonania
    start_time = time.time()

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                      consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                      access_token=WIKIDARIAH_ACCESS_TOKEN,
                                      access_secret=WIKIDARIAH_ACCESS_SECRET,
                                      token_renew_period=14400)
    start_item = 228087
    end_item = 229050
    for i in range(start_item, end_item):
        qid = f'Q{i}'
        item_params = {
                'action': 'delete',
                'title': f'Item:{qid}'
            }

        result = delete_property_or_item(login_instance, params=item_params)
        log_description = 'brak: '
        if result:
            log_description = 'usunięto: '

        with open(log_path, 'a', encoding='utf-8') as f:
            log_message = log_description + qid
            f.write(log_message + '\n')
            print(log_message)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
