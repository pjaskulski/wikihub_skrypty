""" skrypt usuwa zbędne deklaracje stated as z krajów """

import os
import time
import sys
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_exceptions import MWApiError
from wikibaseintegrator.wbi_functions import remove_claims
from dotenv import load_dotenv
from wikidariahtools import find_name_qid, element_exists
from property_import import create_statement_data


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

ok, p_stated_as = find_name_qid('stated as', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated as' w instancji Wikibase")
    sys.exit(1)

ok, p_located_in = find_name_qid('located in (string)', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'located in (string)' w instancji Wikibase")
    sys.exit(1)

ok, p_reference_url = find_name_qid('reference URL', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'reference URL' w instancji Wikibase")
    sys.exit(1)

# wspólna referencja dla wszystkich deklaracji z PRNG
references = {}
references[p_reference_url] = 'https://mapy.geoportal.gov.pl/wss/service/PZGiK/PRNG/WFS/GeographicalNames'

WIKIBASE_WRITE = True


# --------------------------------- MAIN ---------------------------------------

if __name__ == "__main__":
    # pomiar czasu wykonania
    start_time = time.time()

    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'

    load_dotenv(dotenv_path=env_path)
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    lista = ['Q362423', 'Q362424', 'Q362425', 'Q362426', 'Q362427', 'Q362428', 'Q362429',
            'Q362430', 'Q362431', 'Q362432', 'Q362433', 'Q362434', 'Q362435', 'Q362436',
            'Q362437', 'Q362438', 'Q362439', 'Q362440', 'Q362441', 'Q362442', 'Q362443',
            'Q362444', 'Q362445', 'Q362446', 'Q362447', 'Q362448', 'Q362449', 'Q362450',
            'Q362451', 'Q362452', 'Q362453', 'Q362454', 'Q362455', 'Q362456', 'Q362457',
            'Q362458', 'Q362459', 'Q362460', 'Q362461', 'Q362462', 'Q362463', 'Q362464',
            'Q362465', 'Q362466', 'Q362467', 'Q362468', 'Q362469', 'Q362470', 'Q362471',
            'Q362472', 'Q362473', 'Q362474', 'Q362475', 'Q362476', 'Q362477', 'Q362478',
            'Q362479', 'Q362480', 'Q362481', 'Q362482', 'Q362483', 'Q362484', 'Q362485',
            'Q362486', 'Q362487', 'Q362488', 'Q362489', 'Q362490', 'Q362491', 'Q362492',
            'Q362493', 'Q362494', 'Q362495', 'Q362496', 'Q362497', 'Q362498', 'Q362499',
            'Q362500', 'Q362501', 'Q362502', 'Q362503', 'Q362504', 'Q362505', 'Q362506',
            'Q362507', 'Q362508', 'Q362509', 'Q362510', 'Q362511', 'Q362512', 'Q362513',
            'Q362514', 'Q362515', 'Q362516', 'Q362517', 'Q362518', 'Q362519', 'Q362520',
            'Q362521', 'Q362522', 'Q362523', 'Q362524', 'Q362525', 'Q362526', 'Q362527',
            'Q362528', 'Q362529', 'Q362530', 'Q362531', 'Q362532', 'Q362533', 'Q362534',
            'Q362535', 'Q362536', 'Q362537', 'Q362538', 'Q362539', 'Q362540', 'Q362541',
            'Q362542', 'Q362543', 'Q362544', 'Q362545', 'Q362546', 'Q362547', 'Q362548',
            'Q362549', 'Q362550', 'Q362551', 'Q362552', 'Q362553', 'Q362554', 'Q362555',
            'Q362556', 'Q362557', 'Q362558', 'Q362559', 'Q362560', 'Q362561', 'Q362562',
            'Q362563', 'Q362564', 'Q362565', 'Q362566', 'Q362567', 'Q362568', 'Q362569',
            'Q362570', 'Q362571', 'Q362572', 'Q362573', 'Q362574', 'Q362575', 'Q362576',
            'Q362577', 'Q362578', 'Q362579', 'Q362580', 'Q362581', 'Q362582', 'Q362583',
            'Q362584', 'Q362585', 'Q362586', 'Q362587', 'Q362588', 'Q362589', 'Q362590',
            'Q362591', 'Q362592', 'Q362593', 'Q362594', 'Q362595', 'Q362596', 'Q362597',
            'Q362598', 'Q362599', 'Q362600', 'Q362601', 'Q362602', 'Q362603', 'Q362604',
            'Q362605', 'Q362606', 'Q362607', 'Q362608', 'Q362609', 'Q362610', 'Q362611',
            'Q362612', 'Q362613', 'Q362614', 'Q362615', 'Q362616', 'Q362617']

    lands = ['Europa', 'Azja','Afryka','Ameryka Północna', 'Ameryka Południowa', 'Australia i Oceania']

    for item in lista:
        if not element_exists(item):
            continue

        wb_item = wbi_core.ItemEngine(item_id=item)
        label_pl = wb_item.get_label('pl')

        for statement in wb_item.statements:
            prop_nr = statement.get_prop_nr()
            if prop_nr in (p_stated_as):
                value = statement.get_value()
                value_land, value_lang = value
                if value_land in lands:
                    claim_id = statement.get_id()
                    if claim_id:
                        # przygotowanie uzupełnienia właściwości located in (string)
                        data = []
                        statement = create_statement_data(p_located_in, value_land, None, None, add_ref_dict=None)
                        if statement:
                            data.append(statement)

                        if WIKIBASE_WRITE:
                            # jeżeli znaleziono to usuwa
                            result = remove_claims(claim_id, login=login_instance)
                            if result['success'] == 1:
                                print(f'Z elementu {item} usunięto deklarację {prop_nr}, wartość: {value_land}.')
                            else:
                                print(f'ERROR: podczas usuwania deklaracji {prop_nr} z elementu {item}.')

                            # uzupełnienie właściwości located in (string)
                            if data:
                                wb_update = wbi_core.ItemEngine(item_id=item, data=data, debug=False)
                                wb_update.write(login_instance, entity_type='item')
                                print(f'Do elementu {item} dodano deklarację {p_located_in}, wartość: {value_land}.')
                        else:
                            print(f'Przygotowano usunięcie deklaracji {prop_nr} z elementu {item}, wartość: {value_land}.')
                            print(f'Przygotowano dodanie do elementu {item} deklarację {p_located_in}, wartość: {value_land}.')

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
