""" skrypt dodaje referencję typu 'reference URL' do właściwości
    'part of' dla elementów będących typami jednostek administracyjnych
"""

import os
import json
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from dotenv import load_dotenv
from wikidariahtools import element_exists

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

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

    snak_type = "value"
    snak = {
        prop_nr: [
            {
                "snaktype": snak_type,
                "property": prop_nr,
                "datavalue": {"type": "string", "value": prop_value},
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
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_data = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    g_ref_qid = 'P182'
    g_ref_value = 'https://ontohgis.pl'
    properties = ['P212', 'P213', 'P203', 'P204', 'P47']

    systems_items = ['Q79708', 'Q79709', 'Q79710', 'Q79711', 'Q79712', 'Q79713',
                     'Q79714', 'Q79715', 'Q79716', 'Q79717', 'Q79718', 'Q79719',
                     'Q79720', 'Q79721', 'Q79722', 'Q79723', 'Q79724', 'Q79725',
                     'Q79726', 'Q79727', 'Q79728', 'Q79729', 'Q79730', 'Q79731',
                     'Q79732', 'Q79733', 'Q79734', 'Q79735', 'Q79736', 'Q79737',
                     'Q79738', 'Q79739', 'Q79740', 'Q79741', 'Q79742', 'Q79743',
                     'Q79744', 'Q79745', 'Q79746', 'Q79747', 'Q79748', 'Q79749',
                     'Q79750', 'Q79751', 'Q79752', 'Q79753', 'Q79754', 'Q79755']

    for item in systems_items:
        if not element_exists(item):
            continue

        wd_item = wbi_core.ItemEngine(item_id=item)
        print(f"\nItem: {item} - {wd_item.get_label('pl')}")

        for statement in wd_item.statements:
            reference_exists = False
            claim_id = statement.get_id()
            statement_value = statement.get_value()
            statement_prop = statement.get_prop_nr()

            if statement_prop in properties:
                print(f'Weryfikacja deklaracji: {statement_prop}')

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
                        token = get_token(login_data)

                        # dołączanie referencji
                        is_ok = add_reference(login_data, token, claim_id, g_ref_qid, g_ref_value)

                        if is_ok:
                            print(f'Dodano referencję: {g_ref_qid} ({g_ref_value}) do deklaracji {statement_prop}')
                    else:
                        print(f'Przygotowano referencję: {g_ref_qid} ({g_ref_value}) do deklaracji {statement_prop}')
                else:
                    print(f'Referencja  {g_ref_qid} do deklaracji {statement_prop} ({statement_value}) już istnieje')

    print("Skrypt wykonany")
