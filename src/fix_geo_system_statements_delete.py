""" skrypt usuwa dekaracje z systemów administracyjnych """

import os
import sys
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_functions import remove_claims
from dotenv import load_dotenv
from wikidariahtools import element_exists, find_name_qid


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

WIKIBASE_WRITE = True

# --------------------------------- MAIN ---------------------------------------

if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    ok, p_has_part_or_parts = find_name_qid('has part or parts', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'has part or parts' w instancji Wikibase")
        sys.exit(1)

    systems_items = ['Q79708', 'Q79709', 'Q79710', 'Q79711', 'Q79712', 'Q79713',
                     'Q79714', 'Q79715', 'Q79716', 'Q79717', 'Q79718', 'Q79719',
                     'Q79720', 'Q79721', 'Q79722', 'Q79723', 'Q79724', 'Q79725',
                     'Q79726', 'Q79727', 'Q79728', 'Q79729', 'Q79730', 'Q79731',
                     'Q79732', 'Q79733', 'Q79734', 'Q79735', 'Q79736', 'Q79737',
                     'Q79738', 'Q79739', 'Q79740', 'Q79741', 'Q79742', 'Q79743',
                     'Q79744', 'Q79745', 'Q79746', 'Q79747', 'Q79748', 'Q79749',
                     'Q79750', 'Q79751', 'Q79752', 'Q79753', 'Q79754', 'Q79755']

    print("\nUsuwanie właściwości: administrative system\n")
    for item in systems_items:
        if not element_exists(item):
            continue

        wb_update = wbi_core.ItemEngine(item_id=item)
        print(f"Przetwarzanie: {item} ({wb_update.get_label('pl')})")

        for statement in wb_update.statements:
            prop_nr = statement.get_prop_nr()
            if prop_nr in (p_has_part_or_parts):
                claim_id = statement.get_id()
                if claim_id:
                    if WIKIBASE_WRITE:
                        # jeżeli znaleziono to usuwa
                        result = remove_claims(claim_id, login=login_instance)
                        if result['success'] == 1:
                            print(f'Z elementu {item} usunięto deklarację {prop_nr}.')
                        else:
                            print(f'ERROR: podczas usuwania deklaracji {prop_nr} z elementu {item}.')
                    else:
                        print(f'Przygotowano usunięcie deklaracji {prop_nr} z elementu {item}.')

    print("Skrypt wykonany")
