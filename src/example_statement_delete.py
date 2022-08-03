""" skrypt modyfikuje usuwa deklarację (statement) w elemencie Q """

import os
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_functions import remove_claims
from dotenv import load_dotenv
from wikidariahtools import get_claim_id


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

    # Usunięcie deklaracji dla elementu (o okreslonej wartości)
    element = 'Q79211'
    prop_nr = 'P180'
    prop_value = 'Testowy Autor'

    clm_id = get_claim_id(element, prop_nr, prop_value)
    if clm_id:
        # jeżeli znaleziono to usuwa pierwszą (może być wiele o tej samej wartości)
        result = remove_claims(clm_id[0], login=login_instance)

        # przykład zwracanej wartości (result):
        # {'pageinfo': {'lastrevid': 211631}, 'success': 1,
        # 'claims': ['Q79211$FCEEDC83-8089-4810-BE90-4D4EF2892996']}
        if result['success'] == 1:
            print(f'Z elementu {element} usunięto deklarację {prop_nr} o wartości {prop_value}.')
    else:
        print(f'Nie znaleziono dla elementu {element} deklaracji z właściwością {prop_nr} o wartości: {prop_value}.')
