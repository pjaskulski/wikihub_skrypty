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

# nowa wlasciwość
wd_item = wbi_core.ItemEngine(new_item=True)
wd_item.set_label('architectural style', lang='en')
wd_item.set_label('styl architektoniczny',lang='pl')
wd_item.set_description('architectural style of a structure', lang='en')
wd_item.set_description('styl architektoniczny konstrukcji', lang='pl')

# typy danych dla property: 'string', 'wikibase-item', 'monolingualtext', 'external-id'
# 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate'
options = {'property_datatype':'wikibase-item'}
id = wd_item.write(login_instance, bot_account=True, entity_type='property', **options)
print(id)
