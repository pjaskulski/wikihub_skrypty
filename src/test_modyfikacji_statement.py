import os
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator import wbi_login, wbi_datatype
from dotenv import load_dotenv
from pathlib import Path

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

# login i hasło ze zmiennych środowiskowych 
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)
BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

# Zmiana właściwości P4 (nazwisko) typu łańcuch dla elementu Q413
moje_dane = wbi_datatype.String(value='Aders-Kettler-Starszy II', prop_nr='P4')
data = [moje_dane]
wd_item = wbi_core.ItemEngine(item_id='Q413', data=data, debug=False)
wd_item.write(login_instance)
