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
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

    administrative_types = ['Q79902', 'Q79903', 'Q79904', 'Q79905', 'Q79906', 'Q79907',
                     'Q79896', 'Q79897', 'Q79908', 'Q79909', 'Q79910', 'Q79911',
                     'Q79912', 'Q79913', 'Q79914', 'Q79915', 'Q79916', 'Q79917',
                     'Q79918', 'Q79919', 'Q79920', 'Q79921', 'Q79922', 'Q79923',
                     'Q79924', 'Q79925', 'Q79926', 'Q79927', 'Q79928', 'Q79929',
                     'Q79930', 'Q79931', 'Q79932', 'Q79933', 'Q79934', 'Q79935',
                     'Q79936', 'Q79937', 'Q79938', 'Q79939', 'Q79940', 'Q79941',
                     'Q79942', 'Q79943', 'Q79944', 'Q79945', 'Q79946', 'Q79947',
                     'Q79948', 'Q79949', 'Q79950', 'Q79951', 'Q79952', 'Q79953',
                     'Q79954', 'Q79955', 'Q79956', 'Q79957', 'Q79958', 'Q79959',
                     'Q79960', 'Q79961', 'Q79962', 'Q79963', 'Q79964', 'Q79965',
                     'Q79966', 'Q79967', 'Q79968', 'Q79969', 'Q79970', 'Q79971',
                     'Q79972', 'Q79973', 'Q79974', 'Q79975', 'Q79976', 'Q79977',
                     'Q79978', 'Q79979', 'Q79980', 'Q79981', 'Q79982', 'Q79983',
                     'Q79984', 'Q79985', 'Q79986', 'Q79987', 'Q79988', 'Q79989',
                     'Q79990', 'Q79991', 'Q79992', 'Q79993', 'Q79994', 'Q79995',
                     'Q79996', 'Q79997', 'Q79998', 'Q79999', 'Q80000', 'Q80001',
                     'Q80002', 'Q80003', 'Q80004', 'Q80005', 'Q80006', 'Q80007',
                     'Q80008', 'Q80009', 'Q80010', 'Q80011', 'Q80012', 'Q80013',
                     'Q80014', 'Q80015', 'Q80016', 'Q80017', 'Q80018', 'Q80019',
                     'Q80020', 'Q80021', 'Q80022', 'Q80023', 'Q80024', 'Q80025',
                     'Q80026', 'Q80027', 'Q80028', 'Q80029', 'Q80030', 'Q80031',
                     'Q80032', 'Q80033', 'Q80034', 'Q80035', 'Q80036', 'Q80037',
                     'Q80038', 'Q80039', 'Q80040', 'Q80041', 'Q80042', 'Q80043',
                     'Q80044', 'Q80045', 'Q80046', 'Q80047', 'Q80048', 'Q80049',
                     'Q80050', 'Q80051', 'Q80052', 'Q80053', 'Q80054', 'Q80055',
                     'Q80056', 'Q80057', 'Q80058', 'Q80059', 'Q80060', 'Q80061',
                     'Q80062', 'Q80063', 'Q80064', 'Q80065', 'Q80066', 'Q80067',
                     'Q80068', 'Q80069', 'Q80070', 'Q80071', 'Q80072', 'Q80073',
                     'Q80074', 'Q80075', 'Q80076', 'Q80077', 'Q80078', 'Q80079',
                     'Q80080', 'Q80081', 'Q80082', 'Q80083', 'Q80084', 'Q80085',
                     'Q80086', 'Q80087', 'Q80088', 'Q80089', 'Q80090', 'Q80091',
                     'Q80092', 'Q80093', 'Q80094', 'Q80095', 'Q80096', 'Q80097',
                     'Q80098', 'Q80099', 'Q80100', 'Q80101', 'Q80102', 'Q80103',
                     'Q80104', 'Q80105', 'Q80106', 'Q80107', 'Q80108', 'Q80109',
                     'Q80110', 'Q80111', 'Q80112', 'Q80113', 'Q80114', 'Q80115',
                     'Q80116', 'Q80117', 'Q80118', 'Q80119', 'Q80120', 'Q80121',
                     'Q80122', 'Q80123', 'Q80124', 'Q80125', 'Q80126', 'Q80127',
                     'Q80128', 'Q80129', 'Q80130', 'Q80131', 'Q80132', 'Q80133',
                     'Q80134', 'Q80135', 'Q80153', 'Q80154', 'Q80155', 'Q80156',
                     'Q80157', 'Q80158', 'Q80159', 'Q80160', 'Q80161', 'Q80162',
                     'Q80163', 'Q80164', 'Q80165', 'Q80166', 'Q80167', 'Q80168',
                     'Q80169', 'Q80170', 'Q80171', 'Q80172', 'Q80173', 'Q80174',
                     'Q80175', 'Q80176', 'Q80177', 'Q80178', 'Q80179', 'Q80180',
                     'Q80181', 'Q80182', 'Q80183', 'Q80184', 'Q80185', 'Q80186',
                     'Q80187', 'Q80188', 'Q80189', 'Q80190', 'Q80191', 'Q80192',
                     'Q80193', 'Q80194', 'Q80195', 'Q80196', 'Q80197', 'Q80198',
                     'Q80199', 'Q80200']

    with open('../log/adm_types_wiki.txt', 'w', encoding='utf-8') as f:
        for item in administrative_types:
            if not element_exists(item):
                continue

            wb_item = wbi_core.ItemEngine(item_id=item)
            label_pl = wb_item.get_label('pl')
            label_en = wb_item.get_label('en')
            adres = f'https://prunus-208.man.poznan.pl/wiki/Item:{item}'
            f.write(f'# [{adres} {label_en}/{label_pl} ({item})]\n')

    print("Skrypt wykonany")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
