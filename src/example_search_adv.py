""" Uzupełnianie danych miejscowosci z pliku miejscowosciU.xlsx (dane z PRG) """
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import element_search_adv

# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

# ----------------------------------- MAIN -------------------------------------

if __name__ == '__main__':
    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD, token_renew_period=3600)

    label_en = 'Łazy'
    description_en = 'przysiółek wsi: Grzechynia (gmina: Maków Podhalański, powiat: suski, wojewódzwo: małopolskie)'
    description_en = 'przysiółek wsi (gmina: Maków Podhalański, powiat: suski, wojewódzwo: małopolskie)'
    ok, item_id = element_search_adv(label_en, 'en', None, description_en, max_results_to_verify=500)
    print(ok, item_id)
