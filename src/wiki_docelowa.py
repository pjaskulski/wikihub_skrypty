""" test czy działa api wikibase """

import os
import time
import sys
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_functions import execute_sparql_query


# https://wikihum.lab.dariah.pl/wiki/Main_Page
# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://wikihum.lab.dariah.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://wikihum.lab.dariah.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://wikihum.lab.dariah.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env_wikihum"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

print(WIKIDARIAH_CONSUMER_TOKEN)
print(WIKIDARIAH_CONSUMER_SECRET)
print(WIKIDARIAH_ACCESS_TOKEN)
print(WIKIDARIAH_ACCESS_SECRET)

# pomiar czasu wykonania
start_time = time.time()

WIKIBASE_WRITE = False


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    try:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)
        if login_instance:
            print('Zalogowano: ', login_instance.session, login_instance.user_agent)

    except Exception as es:
        print(es)


    print('SPARQL query test.')
    query = """
        SELECT ?item
         WHERE
        {
            ?item wdt:P47 wd:Q32.
        }
        LIMIT 5
    """
    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        print(result["item"]["value"])
