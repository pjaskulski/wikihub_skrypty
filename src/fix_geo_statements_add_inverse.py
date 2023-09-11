""" skrypt dodaje brakujące dekaracje do elementów geograficznych """

import os
import sys
import time
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_functions import execute_sparql_query
from dotenv import load_dotenv
from wikidariahtools import element_exists, find_name_qid
from property_import import create_inverse_statement


# adresy dla API Wikibase (instancja docelowa)
wbi_config['MEDIAWIKI_API_URL'] = 'https://wikihum.lab.dariah.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://wikihum.lab.dariah.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://wikihum.lab.dariah.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

WIKIBASE_WRITE = False

# --------------------------------- MAIN ---------------------------------------

if __name__ == "__main__":
    # pomiar czasu wykonania
    start_time = time.time()

    # login i hasło ze zmiennych środowiskowych - instancja docelowa
    env_path = Path(".") / ".env_wikihum"

    load_dotenv(dotenv_path=env_path)

    # OAuth
    WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
    WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
    WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
    WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

    ok, p_part_of = find_name_qid('part of', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'part of' w instancji Wikibase")
        sys.exit(1)
    ok, p_has_part_or_parts = find_name_qid('has part or parts', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'has part or parts' w instancji Wikibase")
        sys.exit(1)
    ok, p_subclass_of = find_name_qid('subclass of', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'subclass of' w instancji Wikibase")
        sys.exit(1)
    ok, p_superclass_of = find_name_qid('superclass of', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'superclass of' w instancji Wikibase")
        sys.exit(1)
    ok, p_contains_adm_type = find_name_qid('contains administrative unit type', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'contains administrative unit type' w instancji Wikibase")
        sys.exit(1)
    ok, p_belongs_to_adm_sys = find_name_qid('belongs to administrative system', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'belongs to administrative system' w instancji Wikibase")
        sys.exit(1)
    ok, p_stated_in = find_name_qid('stated in', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'stated in' w instancji Wikibase")
        sys.exit(1)

    # wspólna referencja do OntoHGIS dla wszystkich deklaracji
    references = {}
    references[p_stated_in] = 'Q364' # OntoHGIS

    # # lista systemów administracyjnych
    systems_items = []
    query = 'SELECT ?item WHERE { ?item wdt:P27 wd:Q4 . }'
    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        tmp = str(result["item"]["value"]).strip()
        pos = tmp.rfind(r'/')
        search_result = tmp[pos+1:]
        systems_items.append(search_result)


    # lista typów jednostek administracyjnych
    administrative_types = []
    query = 'SELECT ?item WHERE {{ ?item wdt:P27 wd:Q36 . }}'
    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        tmp = str(result["item"]["value"]).strip()
        pos = tmp.rfind(r'/')
        search_result = tmp[pos+1:]
        administrative_types.append(search_result)

    print("\nUzupełnianie: administrative systems\n")
    for item in systems_items:
        if not element_exists(item):
            continue
        wb_update = wbi_core.ItemEngine(item_id=item)
        print(f"Przetwarzanie: {item} ({wb_update.get_label('pl')})")

        create_inverse_statement(login_instance, item, p_part_of, p_has_part_or_parts, references)
        create_inverse_statement(login_instance, item, p_has_part_or_parts, p_part_of, references)

        create_inverse_statement(login_instance, item, p_subclass_of, p_superclass_of, references)
        create_inverse_statement(login_instance, item, p_superclass_of, p_subclass_of, references)

    print("\nUzupełnianie: administrative types\n")
    for item in administrative_types:
        if not element_exists(item):
            continue

        wb_update = wbi_core.ItemEngine(item_id=item)
        print(f"Przetwarzanie: {item} ({wb_update.get_label('pl')})")

        create_inverse_statement(login_instance, item, p_part_of, p_has_part_or_parts, references)
        create_inverse_statement(login_instance, item, p_has_part_or_parts, p_part_of, references)

        create_inverse_statement(login_instance, item, p_subclass_of, p_superclass_of, references)
        create_inverse_statement(login_instance, item, p_superclass_of, p_subclass_of, references)

        create_inverse_statement(login_instance, item, p_belongs_to_adm_sys, p_contains_adm_type, references)

    print("Skrypt wykonany")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
