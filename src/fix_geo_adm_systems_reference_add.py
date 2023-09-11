""" skrypt dodaje referencję typu 'reference URL' do właściwości
    'part of', subclass of itp. dla systemów administracyjnych
"""

import os
import json
import sys
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikibaseintegrator.wbi_functions import execute_sparql_query
from dotenv import load_dotenv
from wikidariahtools import element_exists, find_name_qid


# adresy dla API Wikibase (instancja docelowa)
wbi_config['MEDIAWIKI_API_URL'] = 'https://wikihum.lab.dariah.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://wikihum.lab.dariah.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://wikihum.lab.dariah.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

ok, p_stated_in = find_name_qid('stated in', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated in' w instancji Wikibase")
    sys.exit(1)
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
ok, p_starts_at = find_name_qid('starts at', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'starts at' w instancji Wikibase")
    sys.exit(1)
ok, p_ends_at = find_name_qid('ends at', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'ends at' w instancji Wikibase")
    sys.exit(1)
ok, p_instance_of = find_name_qid('instance of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'instance of' w instancji Wikibase")
    sys.exit(1)

WIKIBASE_WRITE = True


def get_token(my_login) -> str:
    """ zwraca token lub pusty string """
    result = ''

    token_params = {"action": "query",
                    "meta": "tokens"}

    try:
        token_results = mediawiki_api_call_helper(
            data=token_params,
            login=my_login,
            mediawiki_api_url=None,
            user_agent=None,
            allow_anonymous=False,
        )

        result = token_results["query"]["tokens"]["csrftoken"]

    except MWApiError as wb_get_token_error:
        print("Error (remove reference - token):", wb_get_token_error)

    return result


def add_reference(my_login, p_token: str, p_claim_id: str, prop_nr: str, prop_value: str) -> bool:
    """dodaje odnośnik do deklaracji"""
    add_result = False
    prop_value_numeric = int(prop_value[1:])

    snak_type = "value"
    snak = {
        prop_nr: [
            {
                "snaktype": snak_type,
                "property": prop_nr,
                "datavalue": {"type": "wikibase-entityid",
                              "value": {"entity-type": "item", "numeric-id": prop_value_numeric, "id": prop_value}
                              },
            }
        ]
    }
    snak_encoded = json.dumps(snak)

    params = {
        "action": "wbsetreference",
        "statement": p_claim_id,
        "snaks": snak_encoded,
        "token": p_token,
        "bot": True,
    }

    try:
        results = mediawiki_api_call_helper(
            data=params,
            login=my_login,
            mediawiki_api_url=None,
            user_agent=None,
            allow_anonymous=False,
        )
        if results["success"] == 1:
            add_result = True
    except MWApiError as wbsetreference_error:
        print(f"Error - dodawanie referencji - snak: \n{snak_encoded}\n", wbsetreference_error)

    return add_result


if __name__ == "__main__":
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

    # wspólna referencja do OntoHGIS dla wszystkich deklaracji
    g_ref_qid = p_stated_in
    g_ref_value = 'Q364'

    properties = [p_part_of, p_has_part_or_parts, p_subclass_of, p_superclass_of,
                  p_starts_at, p_ends_at, p_instance_of]

    # # lista systemów administracyjnych
    systems_items = []
    query = 'SELECT ?item WHERE { ?item wdt:P27 wd:Q4 . }'
    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        tmp = str(result["item"]["value"]).strip()
        pos = tmp.rfind(r'/')
        search_result = tmp[pos+1:]
        systems_items.append(search_result)

    for item in systems_items:
        print(f"Item: {item}")
        if not element_exists(item):
            continue

        wd_item = wbi_core.ItemEngine(item_id=item)

        for statement in wd_item.statements:
            reference_exists = False
            claim_id = statement.get_id()
            statement_value = statement.get_value()
            statement_prop = statement.get_prop_nr()

            if statement_prop in properties:
                print(f'Weryfikacja deklaracji: {statement_prop} o wartości = {statement_value}')

                # weryfikacja czy referencja istnieje
                tmp_references = statement.get_references()
                for t_ref_blok in tmp_references:
                    stat_ref_qid = t_ref_blok[0].get_prop_nr()
                    stat_ref_value = t_ref_blok[0].get_value()
                    if stat_ref_qid == g_ref_qid:
                        reference_exists = True

                # jeżeli nie istnieje to dodaje
                if not reference_exists:
                    if WIKIBASE_WRITE:
                        # token
                        token = get_token(login_instance)

                        # dołączanie referencji
                        is_ok = add_reference(login_instance, token, claim_id, g_ref_qid, g_ref_value)

                        if is_ok:
                            print(f'Dodano referencję: {g_ref_qid} ({g_ref_value}) do deklaracji {statement_prop} ({statement_value})')
                    else:
                        print(f'Przygotowano referencję: {g_ref_qid} ({g_ref_value}) do deklaracji {statement_prop} ({statement_value})')
                else:
                    print(f'Referencja  {g_ref_qid} do deklaracji {statement_prop} ({statement_value}) już istnieje')

    print("Skrypt wykonany")
