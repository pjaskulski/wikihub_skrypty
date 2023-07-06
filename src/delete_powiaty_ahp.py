""" usunięcie błędie dodanych powiatów a AHP """

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper

# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

# pomiar czasu wykonania
start_time = time.time()

dane =  [
    'Q224215', 'Q224216', 'Q224217', 'Q224218', 'Q224219', 'Q224220', 'Q224221',
    'Q224222', 'Q224223', 'Q224224', 'Q224225', 'Q224226', 'Q224227', 'Q224228',
    'Q224229', 'Q224230', 'Q224231', 'Q224232', 'Q224233', 'Q224234', 'Q224235',
    'Q224236', 'Q224237', 'Q224238', 'Q224239', 'Q224240', 'Q224241', 'Q224242',
    'Q224243', 'Q224244', 'Q224245', 'Q224246', 'Q224247', 'Q224248', 'Q224249',
    'Q224250', 'Q224251', 'Q224252', 'Q224253', 'Q224254', 'Q224255', 'Q224256',
    'Q224257', 'Q224258', 'Q224259', 'Q224260', 'Q224261', 'Q224262', 'Q224263',
    'Q224264', 'Q224265', 'Q224266', 'Q224267', 'Q224268', 'Q224269', 'Q224270',
    'Q224271', 'Q224272', 'Q224273', 'Q224274', 'Q224275', 'Q224276', 'Q224277',
    'Q224278', 'Q224279', 'Q224280', 'Q224281', 'Q224282', 'Q224283', 'Q224284',
    'Q224285', 'Q224286', 'Q224287', 'Q224288', 'Q224289', 'Q224290', 'Q224291',
    'Q224292', 'Q224293', 'Q224294', 'Q224295', 'Q224296', 'Q224297', 'Q224298',
    'Q224299', 'Q224300', 'Q224301', 'Q224302', 'Q224303', 'Q224304', 'Q224305',
    'Q224306', 'Q224307', 'Q224308', 'Q224309', 'Q224310', 'Q224311', 'Q224312',
    'Q224313', 'Q224314', 'Q224315'
]

# --------------------------------- MAIN ---------------------------------------
if __name__ == '__main__':
    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                      consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                      access_token=WIKIDARIAH_ACCESS_TOKEN,
                                      access_secret=WIKIDARIAH_ACCESS_SECRET,
                                      token_renew_period=14400)

    for delete_item in dane:
        # usuwanie z obsługą błędów tokena
        test = 1

        while True:
            params = {
                'action': 'delete',
                'title': f'Item:{delete_item}'
            }

            try:
                delete_results = mediawiki_api_call_helper(data=params, login=login_instance,
                                                      mediawiki_api_url=None)
                print(delete_results)
                break
            except MWApiError as wb_error:
                err_code = wb_error.error_msg['error']['code']
                message = wb_error.error_msg['error']['info']
                print(f'ERROR: {err_code}, {message}')
                # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                if err_code in ['assertuserfailed', 'badtoken']:
                    if test == 1:
                        print('Generate edit credentials...')
                        login_instance.generate_edit_credentials()
                        test += 1
                        continue
                sys.exit(1)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
