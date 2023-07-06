""" Skrypt wyszukuje informacje w Wikibase """

import pprint
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import execute_sparql_query, mediawiki_api_call_helper
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import element_exists, element_search, search_by_purl, get_claim_value, element_search_adv

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia wartości poniżej w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

if __name__ == "__main__":

    # zapytanie SPARQL o listę wszystkich elementów posiadających właściwość P47
    # (instance_of) o wartości Q32 (human), z limitem do 5 resultatów
    print('SPARQL query test.')
    query = """
        SELECT ?item
        WHERE
        {
            # ?item  instance_of human
            ?item wdt:P459 wd:Q229050.
        }
        LIMIT 5
    """

    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        print(result["item"]["value"])
