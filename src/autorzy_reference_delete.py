""" skrypt usuwa referencję typu 'reference URL' """

import os
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


def delete_reference(my_login, par_claim_id, par_reference_hash, par_token) -> bool:
    """ usuwanie referencji """
    result = False

    p_params = {
                "action": "wbremovereferences",
                "statement": par_claim_id,
                "references": par_reference_hash,
                "token": par_token,
                "bot": True,
            }

    try:
        p_results = mediawiki_api_call_helper(
            data=p_params,
            login=my_login,
            mediawiki_api_url=None,
            user_agent=None,
            allow_anonymous=False,
        )

        if p_results["success"] == 1:
            result = True

    except MWApiError as wbdelreference_error:
        print("Error: problem z usuwaniem referencji, ", wbdelreference_error)

    return result


if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_data = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    g_ref_qid = 'P399'

    items = []
    for i in range(232325, 233533):
        items.append(f"Q{i}")

    for item in items:
        print(f"Item: {item}")
        if not element_exists(item):
            continue

        wd_item = wbi_core.ItemEngine(item_id=item)

        for statement in wd_item.statements:
            claim_id = statement.get_id()
            statement_value = statement.get_value()
            statement_prop = statement.get_prop_nr()
            if statement_prop not in ('P517', 'P484'):
                continue
            tmp_references = statement.get_references()
            for t_ref_blok in tmp_references:
                stat_ref_qid = t_ref_blok[0].get_prop_nr()
                stat_ref_value = t_ref_blok[0].get_value()
                if (stat_ref_qid == g_ref_qid):
                    reference_hash = t_ref_blok[0].get_hash()

                    # token
                    token = get_token(login_data)
                    is_deleted = delete_reference(login_data, claim_id, reference_hash, token)

                    if is_deleted:
                        print(f'Item {item} - usunięto referencję: {g_ref_qid} z deklaracji {statement_prop} ({statement_value})')

    print("Skrypt wykonany")