""" skrypt dodaje brakujące dekaracje do elementów geograficznych """

import os
import sys
import time
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from dotenv import load_dotenv
from wikidariahtools import element_exists, find_name_qid
from property_import import create_inverse_statement


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'

WIKIBASE_WRITE = False

# --------------------------------- MAIN ---------------------------------------

if __name__ == "__main__":
    # pomiar czasu wykonania
    start_time = time.time()

    # login i hasło ze zmiennych środowiskowych (plik .env w folderze ze źródłami)
    env_path = Path('.') / '.env'
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

    ok, p_stated_in = find_name_qid('stated in', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'stated in' w instancji Wikibase")
        sys.exit(1)
    ok, p_subclass_of = find_name_qid('subclass of', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'subclass of' w instancji Wikibase")
        sys.exit(1)
    ok, p_superclass_of = find_name_qid('superclass of', 'property', strict=True)
    if not ok:
        print("ERROR: brak właściwości 'superclass of' w instancji Wikibase")
        sys.exit(1)

    # wspólna referencja dla wszystkich deklaracji
    references = {}
    references[p_stated_in] = 'Q233549'

    administrative_types = ['Q234035', 'Q234036', 'Q234037', 'Q234038', 'Q234039', 'Q234040', 'Q234041', 'Q234042', 'Q234043',
'Q234044', 'Q234045', 'Q234046', 'Q234047', 'Q234048', 'Q234049', 'Q234050', 'Q234051', 'Q234052',
'Q234053', 'Q234054', 'Q234055', 'Q234056', 'Q234057', 'Q234058', 'Q234059', 'Q234060', 'Q234061',
'Q234062', 'Q234063', 'Q234064', 'Q234065', 'Q234066', 'Q234067', 'Q234068', 'Q234069', 'Q234070',
'Q234071', 'Q234072', 'Q234073', 'Q234074', 'Q234075', 'Q234076', 'Q234077', 'Q234078', 'Q234079',
'Q234080', 'Q234081', 'Q234082', 'Q234083', 'Q234084', 'Q234085', 'Q234086', 'Q234087', 'Q234088',
'Q234089', 'Q234090', 'Q234091', 'Q234092', 'Q234093', 'Q234094', 'Q234095', 'Q234096', 'Q234097',
'Q234098', 'Q234099', 'Q234100', 'Q234101', 'Q234102', 'Q234103', 'Q234104', 'Q234105', 'Q234106',
'Q234107', 'Q234108', 'Q234109', 'Q234110', 'Q234111', 'Q234112', 'Q234113', 'Q234114', 'Q234115',
'Q234116', 'Q234117', 'Q234118', 'Q234119', 'Q234120', 'Q234121', 'Q234122', 'Q234123', 'Q234124',
'Q234125', 'Q234126', 'Q234127', 'Q234128', 'Q234129', 'Q234130', 'Q234131', 'Q234132', 'Q234133',
'Q234134', 'Q234135', 'Q234136', 'Q234137', 'Q234138', 'Q234139', 'Q234140', 'Q234141', 'Q234142',
'Q234143', 'Q234144', 'Q234145', 'Q234146', 'Q234147', 'Q234148', 'Q234149', 'Q234150', 'Q234151',
'Q234152', 'Q234153', 'Q234154', 'Q234155', 'Q234156', 'Q234157', 'Q234158', 'Q234159', 'Q234160',
'Q234161', 'Q234162', 'Q234163', 'Q234164', 'Q234165', 'Q234166', 'Q234167', 'Q234168', 'Q234169',
'Q234170', 'Q234171', 'Q234172', 'Q234173', 'Q234174', 'Q234175', 'Q234176', 'Q234177', 'Q234178',
'Q234179', 'Q234180', 'Q234181', 'Q234182', 'Q234183', 'Q234184', 'Q234185', 'Q234186', 'Q234187',
'Q234188', 'Q234189', 'Q234190', 'Q234191', 'Q234192', 'Q234193', 'Q234194', 'Q234195', 'Q234196',
'Q234197', 'Q234198', 'Q234199', 'Q234200', 'Q234201', 'Q234202', 'Q234203', 'Q234204', 'Q234205',
'Q234206', 'Q234207', 'Q234208', 'Q234209', 'Q234210', 'Q234211', 'Q234212', 'Q234213', 'Q234214',
'Q234215', 'Q234216', 'Q234217', 'Q234218', 'Q234219', 'Q234220', 'Q234221', 'Q234222', 'Q234223',
'Q234224', 'Q234225', 'Q234226', 'Q234227', 'Q234228', 'Q234229', 'Q234230', 'Q234231', 'Q234232',
'Q234233', 'Q234234', 'Q234235', 'Q234236', 'Q234237', 'Q234238', 'Q234239', 'Q234240', 'Q234241',
'Q234242', 'Q234243', 'Q234244', 'Q234245', 'Q234246', 'Q234247', 'Q234248', 'Q234249', 'Q234250',
'Q234251', 'Q234252', 'Q234253', 'Q234254', 'Q234255', 'Q234256', 'Q234257', 'Q234258', 'Q234259',
'Q234260'
    ]

    print("\nUzupełnianie: administrative types\n")
    for item in administrative_types:
        if not element_exists(item):
            continue

        wb_update = wbi_core.ItemEngine(item_id=item)
        print(f"Przetwarzanie: {item} ({wb_update.get_label('pl')})")

        create_inverse_statement(login_instance, item, p_subclass_of, p_superclass_of, references)
        create_inverse_statement(login_instance, item, p_superclass_of, p_subclass_of, references)


    print("Skrypt wykonany")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
