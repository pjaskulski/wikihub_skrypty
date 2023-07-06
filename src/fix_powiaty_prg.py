""" skrypt dodaje brakujące dekaracje do województw """

import os
import time
from pathlib import Path
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_core
from dotenv import load_dotenv
from wikidariahtools import element_exists
from property_import import create_inverse_statement
from wikidariahtools import get_properties


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

    properties = get_properties(['part of', 'has part or parts', 'stated in', 'retrieved', 'reference URL'])

    # wspólna referencja dla wszystkich deklaracji
    references = {}
    references[properties['reference URL']] = 'https://mapy.geoportal.gov.pl/wss/service/PZGIK/PRG/WFS/AdministrativeBoundaries'
    references[properties['retrieved']] = '2022-09-05'

    powiaty = [
        'Q234277', 'Q234278', 'Q234279', 'Q234280', 'Q234281', 'Q234282', 'Q234283',
        'Q234284', 'Q234285', 'Q234286', 'Q234287', 'Q234288', 'Q234289', 'Q234290',
        'Q234291', 'Q234292', 'Q234293', 'Q234294', 'Q234295', 'Q234296', 'Q234297',
        'Q234298', 'Q234299', 'Q234300', 'Q234301', 'Q234302', 'Q234303', 'Q234304',
        'Q234305', 'Q234306', 'Q234307', 'Q234308', 'Q234309', 'Q234310', 'Q234311',
        'Q234312', 'Q234313', 'Q234314', 'Q234315', 'Q234316', 'Q234317', 'Q234318',
        'Q234319', 'Q234320', 'Q234321', 'Q234322', 'Q234323', 'Q234324', 'Q234325',
        'Q234326', 'Q234327', 'Q234328', 'Q234329', 'Q234330', 'Q234331', 'Q234332',
        'Q234333', 'Q234334', 'Q234335', 'Q234336', 'Q234337', 'Q234338', 'Q234339',
        'Q234340', 'Q234341', 'Q234342', 'Q234343', 'Q234344', 'Q234345', 'Q234346',
        'Q234347', 'Q234348', 'Q234349', 'Q234350', 'Q234351', 'Q234352', 'Q234353',
        'Q234354', 'Q234355', 'Q234356', 'Q234357', 'Q234358', 'Q234359', 'Q234360',
        'Q234361', 'Q234362', 'Q234363', 'Q234364', 'Q234365', 'Q234366', 'Q234367',
        'Q234368', 'Q234369', 'Q234370', 'Q234371', 'Q234372', 'Q234373', 'Q234374',
        'Q234375', 'Q234376', 'Q234377', 'Q234378', 'Q234379', 'Q234380', 'Q234381',
        'Q234382', 'Q234383', 'Q234384', 'Q234385', 'Q234386', 'Q234387', 'Q234388',
        'Q234389', 'Q234390', 'Q234391', 'Q234392', 'Q234393', 'Q234394', 'Q234395',
        'Q234396', 'Q234397', 'Q234398', 'Q234399', 'Q234400', 'Q234401', 'Q234402',
        'Q234403', 'Q234404', 'Q234405', 'Q234406', 'Q234407', 'Q234408', 'Q234409',
        'Q234410', 'Q234411', 'Q234412', 'Q234413', 'Q234414', 'Q234415', 'Q234416',
        'Q234417', 'Q234418', 'Q234419', 'Q234420', 'Q234421', 'Q234422', 'Q234423',
        'Q234424', 'Q234425', 'Q234426', 'Q234427', 'Q234428', 'Q234429', 'Q234430',
        'Q234431', 'Q234432', 'Q234433', 'Q234434', 'Q234435', 'Q234436', 'Q234437',
        'Q234438', 'Q234439', 'Q234440', 'Q234441', 'Q234442', 'Q234443', 'Q234444',
        'Q234445', 'Q234446', 'Q234447', 'Q234448', 'Q234449', 'Q234450', 'Q234451',
        'Q234452', 'Q234453', 'Q234454', 'Q234455', 'Q234456', 'Q234457', 'Q234458',
        'Q234459', 'Q234460', 'Q234461', 'Q234462', 'Q234463', 'Q234464', 'Q234465',
        'Q234466', 'Q234467', 'Q234468', 'Q234469', 'Q234470', 'Q234471', 'Q234472',
        'Q234473', 'Q234474', 'Q234475', 'Q234476', 'Q234477', 'Q234478', 'Q234479',
        'Q234480', 'Q234481', 'Q234482', 'Q234483', 'Q234484', 'Q234485', 'Q234486',
        'Q234487', 'Q234488', 'Q234489', 'Q234490', 'Q234491', 'Q234492', 'Q234493',
        'Q234494', 'Q234495', 'Q234496', 'Q234497', 'Q234498', 'Q234499', 'Q234500',
        'Q234501', 'Q234502', 'Q234503', 'Q234504', 'Q234505', 'Q234506', 'Q234507',
        'Q234508', 'Q234509', 'Q234510', 'Q234511', 'Q234512', 'Q234513', 'Q234514',
        'Q234515', 'Q234516', 'Q234517', 'Q234518', 'Q234519', 'Q234520', 'Q234521',
        'Q234522', 'Q234523', 'Q234524', 'Q234525', 'Q234526', 'Q234527', 'Q234528',
        'Q234529', 'Q234530', 'Q234531', 'Q234532', 'Q234533', 'Q234534', 'Q234535',
        'Q234536', 'Q234537', 'Q234538', 'Q234539', 'Q234540', 'Q234541', 'Q234542',
        'Q234543', 'Q234544', 'Q234545', 'Q234546', 'Q234547', 'Q234548', 'Q234549',
        'Q234550', 'Q234551', 'Q234552', 'Q234553', 'Q234554', 'Q234555', 'Q234556',
        'Q234557', 'Q234558', 'Q234559', 'Q234560', 'Q234561', 'Q234562', 'Q234563',
        'Q234564', 'Q234565', 'Q234566', 'Q234567', 'Q234568', 'Q234569', 'Q234570',
        'Q234571', 'Q234572', 'Q234573', 'Q234574', 'Q234575', 'Q234576', 'Q234577',
        'Q234578', 'Q234579', 'Q234580', 'Q234581', 'Q234582', 'Q234583', 'Q234584',
        'Q234585', 'Q234586', 'Q234587', 'Q234588', 'Q234589', 'Q234590', 'Q234591',
        'Q234592', 'Q234593', 'Q234594', 'Q234595', 'Q234596', 'Q234597', 'Q234598',
        'Q234599', 'Q234600', 'Q234601', 'Q234602', 'Q234603', 'Q234604', 'Q234605',
        'Q234606', 'Q234607', 'Q234608', 'Q234609', 'Q234610', 'Q234611', 'Q234612',
        'Q234613', 'Q234614', 'Q234615', 'Q234616', 'Q234617', 'Q234618', 'Q234619',
        'Q234620', 'Q234621', 'Q234622', 'Q234623', 'Q234624', 'Q234625', 'Q234626',
        'Q234627', 'Q234628', 'Q234629', 'Q234630', 'Q234631', 'Q234632', 'Q234633',
        'Q234634', 'Q234635', 'Q234636', 'Q234637', 'Q234638', 'Q234639', 'Q234640',
        'Q234641', 'Q234642', 'Q234643', 'Q234644', 'Q234645', 'Q234646', 'Q234647',
        'Q234648', 'Q234649', 'Q234650', 'Q234651', 'Q234652', 'Q234653', 'Q234654',
        'Q234655', 'Q234656'
    ]

    print("\nUzupełnianie powiatów w województwach:\n")
    for item in powiaty:
        if not element_exists(item):
            continue

        wb_update = wbi_core.ItemEngine(item_id=item)
        print(f"Przetwarzanie: {item} ({wb_update.get_label('pl')})")

        if WIKIBASE_WRITE:
            create_inverse_statement(login_instance,
                                     item,
                                     properties['part of'],
                                     properties['has part or parts'],
                                     references)

    print("Skrypt wykonany")
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
