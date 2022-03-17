""" skrypt dodaje deklarację (statement) do właściwości P, wraz z referencją"""

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

    # referencja, właściwość P93 (Wikidata Url) z adresem url z wikidata.org
    url = 'https://www.wikidata.org/wiki/Property:P149'
    references = [
            [
                wbi_datatype.Url(value=url, prop_nr='P93', is_reference=True)
            ]
    ]

    # dodanie deklaracji z zewnętrznym ID: P50 o wartości z wikidata.org 'P149'
    # do istniejącej w wikibase właściwości P151 (architectural style) references=references
    moje_dane = wbi_datatype.ExternalID(value='P149', prop_nr='P50', references=references)
    data = [moje_dane]
    wd_item = wbi_core.ItemEngine(item_id='P151', data=data, debug=False)
    wd_item.write(login_instance, entity_type='property')
