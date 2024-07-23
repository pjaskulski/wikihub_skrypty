""" korekta współrzędnych zamków """
# pylint: disable=logging-fstring-interpolation
import os
import sys
import time
import logging
import csv
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import WikibaseIntegrator, wbi_login, datatypes
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_exceptions import MWApiError
from wikibaseintegrator.wbi_helpers import execute_sparql_query
from wikibaseintegrator.wbi_enums import ActionIfExists


# adresy dla API Wikibase (instancja docelowa)
wbi_config['MEDIAWIKI_API_URL'] = 'https://wikihum.lab.dariah.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://wikihum.lab.dariah.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://wikihum.lab.dariah.pl'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env_wikihum"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

# Constants
COORDINATE_LOCATION = "P63"
POINT_IN_TIME = "P40"
P_AHP_ID = "P81"

# tworzenie obiektu loggera
file_log = Path('..') / 'log' / 'ahp_zamki.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler = logging.StreamHandler()
c_handler.setFormatter(log_format)
c_handler.setLevel(logging.DEBUG)
logger.addHandler(c_handler)
# zapis logów do pliku tylko jeżeli uruchomiono z zapisem do wiki
f_handler = logging.FileHandler(file_log)
f_handler.setFormatter(log_format)
f_handler.setLevel(logging.INFO)
logger.addHandler(f_handler)


# -------------------------- FUNKCJE -------------------------------------------
def edit_coordination(source_qid, login_instance, latitude, longitude):
    """
    funkcja modyfikuje współrzędne z kwalifikatorem point in time = 1600
    """

    save_changes = False
    year_of_interest = '+1600-00-00T00:00:00Z'
    precision = 0.001666666666667

    wbi = WikibaseIntegrator(login=login_instance)
    source_item = wbi.item.get(entity_id=source_qid)

    claims = None
    try:
        claims = source_item.claims.get(COORDINATE_LOCATION)
    except KeyError: # jeżeli element nie ma właściwości
        return

    for claim in claims:
        valid_claim = False

        try:
            qualifiers = claim.qualifiers.get(POINT_IN_TIME)
        except KeyError: # jeżeli właściwość nie ma kwalifikatora point in time
            continue

        if qualifiers:
            for qualifier in qualifiers:
                qualifier_year = qualifier.datavalue["value"]["time"]
                if qualifier_year == year_of_interest:
                    valid_claim = True
                    break

        if valid_claim:
            new_qualifiers = claim.qualifiers
            new_references = claim.references
            new_claim = datatypes.GlobeCoordinate(latitude=latitude,
                                                  longitude=longitude,
                                                  precision=precision,
                                                  prop_nr=COORDINATE_LOCATION,
                                                  references=new_references,
                                                  qualifiers=new_qualifiers)
            claim.remove()
            source_item.claims.add(new_claim, action_if_exists = ActionIfExists.APPEND_OR_REPLACE)
            save_changes = True
            break

    # zapis zmian
    if save_changes:
        # zapis zmian w docelowym elemencie
        test = 1
        while True:
            try:
                source_item.write()
                print(f'Dane poprawione w https://wikihum.lab.dariah.pl/wiki/Item:{source_qid}')
                break
            except MWApiError as wbdel_error:
                print(f'ERROR: {wbdel_error.code}, {wbdel_error.info}')
                # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                if wbdel_error.code in ['assertuserfailed', 'badtoken']:
                    if test == 1:
                        print('Generate edit credentials...')
                        login_instance.generate_edit_credentials()
                        test += 1
                        continue
                sys.exit(1)


def search_by_unique_id(prop_id: str, id_value: str) -> tuple:
    """ wyszukiwanie elementu na podstawie wartości deklaracji będącej jednoznacznym
        identyfikatorem, zwraca krotkę (True/False, qid) """
    query = f'SELECT ?item WHERE {{ ?item wdt:{prop_id} "{id_value}". }} LIMIT 5'

    results = execute_sparql_query(query)
    output = []
    for result in results["results"]["bindings"]:
        output.append(result["item"]["value"])

    # wynik to lista adresów https://wikihum.lab.dariah.pl/entity/Q77881
    if len(output) == 1:
        if 'https' in output[0].strip():
            search_result = output[0].strip().replace('https://wikihum.lab.dariah.pl/entity/', '')
        else:
            search_result = output[0].strip().replace('http://wikihum.lab.dariah.pl/entity/', '')
        return True, search_result

    return False, f'ERROR: brak lub niejednoznaczny wynik wyszukiwania (znaleziono: {len(output)}).'

# ----------------------------------- MAIN -------------------------------------

if __name__ == '__main__':
    # pomiar czasu wykonania
    start_time = time.time()

    # logowanie do instancji wikibase
    login_instance = wbi_login.OAuth1(consumer_token=WIKIDARIAH_CONSUMER_TOKEN,
                                     consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                     access_token=WIKIDARIAH_ACCESS_TOKEN,
                                     access_secret=WIKIDARIAH_ACCESS_SECRET,
                                     token_renew_period=14400)

    # plik z listą miejscowości
    file_name = Path('..') / 'data' / 'zamki_koordynaty.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)

        index = 0
        for i, row in enumerate(csv_reader):
            index += 1
            if index < 2:
                continue

            id_miejscowosci = row["id"].strip()
            latitude = float(row["szerokość (latitude)"].strip())
            longitude = float(row["długość (longitude)"].strip())

            ok, element_qid = search_by_unique_id(P_AHP_ID, id_miejscowosci)
            if not ok:
                logger.info(f'ERROR: nie znaleziono elementu dla id_ahp: {id_miejscowosci}')
                continue

            logger.info(f'Wprowadzanie poprawek do elementu: {element_qid}')
            edit_coordination(source_qid=element_qid,
                            login_instance=login_instance,
                            latitude=latitude,
                            longitude=longitude)


    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
