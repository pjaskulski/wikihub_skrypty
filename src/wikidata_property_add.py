""" skrypt dodaje deklarację (statement) do właściwości P, wraz z referencją"""

import os
from pathlib import Path
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, wbi_datatype
from wikibaseintegrator.wbi_functions import remove_claims
from dotenv import load_dotenv
from wikidariahtools import element_exists, statement_value_fix, get_property_type, get_claim_id


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'


if __name__ == "__main__":
    # login i hasło ze zmiennych środowiskowych
    env_path = Path(".") / ".env"
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

    start_id = 407
    end_id = 530

    for item in range(start_id, end_id):
        item_id = f'P{item}'
        if element_exists(item_id):
            print(item_id)
            wb_item_read = wbi_core.ItemEngine(item_id=item_id)
            for statement in wb_item_read.statements:
                statement_property = statement.get_prop_nr()
                if statement_property == 'P398':
                    statement_value = statement.get_value()
                    statement_type = get_property_type(statement_property)
                    statement_value = statement_value_fix(statement_value, statement_type)
                    print(f'Znaleziono {statement_property} o wartości {statement_value}')

                    moje_dane = wbi_datatype.ExternalID(value=statement_value, prop_nr='P530')
                    data = [moje_dane]
                    wb_item_write = wbi_core.ItemEngine(item_id=item_id, data=data, debug=False)
                    print(f'Przygotowano dodanie P530 o wartości {statement_value}')
                    wb_item_write.write(login_instance, entity_type='property')

                    clm_id = get_claim_id(item_id, 'P398', statement_value)
                    if clm_id:
                        print('Przygotowano usunięcie P398')
                        result = remove_claims(clm_id[0], login=login_instance)
                        if result['success'] == 1:
                            print(f'Z właściwości {item_id} usunięto deklarację P398 o wartości {statement_value}.')
