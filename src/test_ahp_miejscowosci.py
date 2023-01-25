""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import os
import sys
import time
import re
import copy
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from langdetect import detect
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import element_search_adv, get_properties, get_elements
from wikidariahtools import search_by_unique_id, write_or_exit
from property_import import create_statement_data, has_statement


# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
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

WIKIBASE_WRITE = True


def get_palatinate(value: str):
    """ zwraca QID województwa """
    result = ''

    if value.startswith('ziemia'):
        label = value.replace('ziemia', 'land')
        palatinate_parameters = [(properties['instance of'], elements['land (The Polish-Lithuanian Commonwealth (1569-1795))'])]

    else:
        label = f"palatinate {value}"
        palatinate_parameters = [(properties['instance of'], elements['palatinate (The Polish-Lithuanian Commonwealth (1569-1795))'])]

    ok, qid = element_search_adv(label, 'en', palatinate_parameters)
    if ok:
        result = qid
    else:
        logger.info(f'ERROR: nie znaleziono QID dla {value}')

    return result

 # tworzenie obiektu loggera
file_log = Path('..') / 'log' / 'ahp_zbiorcza_pkt_prng.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(file_log)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler.setFormatter(log_format)
f_handler.setFormatter(log_format)
c_handler.setLevel(logging.DEBUG)
f_handler.setLevel(logging.INFO)
logger.addHandler(c_handler)
logger.addHandler(f_handler)

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
print('Przygotowanie słownika właściwości...')
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'settlement type', 'settlement ownership type', 'prng id',
                             'contains an object type', 'type of location',
                             'central state functions', 'central church functions',
                             'SIMC place ID', 'Wikidata ID', 'AHP id',
                             'located in the administrative territorial entity',
                             'count', 'ID SHG'
                            ])

print('Przygotowanie słownika elementów definicyjnych...')
elements = get_elements(['human settlement', 'demesne settlement',
                         'manor', 'demesne', 'castle', 'glassworks', 'mining settlement',
                         'city/town', 'abbey', 'inn', 'ironworks',
                         'mill settlement', 'tar pitch', 'ostrov', 'suburb', 'suburb or village',
                         'haven', 'unsettled area', 'village', 'royal property', 'church property',
                         'town property', 'noble property',
                         'brewery', 'fulling mill', 'demesne', 'tavern', 'rental tavern',
                         'hereditary tavern', 'cauldron sauce', 'smithy',
                         'ironwork', 'mill', 'rental mill', 'hereditary mill',
                         'mill with overshot water wheel', 'mill with undershot water wheel',
                         'furnace', 'saw', 'ore', 'groats mortar', 'sawmill',
                         'windmill', 'rental windmill', 'hereditary windmill', 'wyszynk',
                         'location unknown', 'approximate location',
                         'the capital of an archdeaconry', 'the capital of a deanery',
                         'the seat of a parish', 'the capital of a diocese',
                         'the seat of an abbey/ monastery',
                         "castellan's residence", 'capital of the duchy',
                         'seat of the town starost', 'the place where the knighthood was held',
                         'the capital of a county', 'venue of the general assembly',
                         'place of meeting of the local assembly', 'the seat of the crown tribunal',
                         'seat of the non-garden starost (tenutarius)', 'capital of the state',
                         'the capital of the province', 'general starosty of Małopolska',
                         'the capital of the land',
                         'district (The Polish-Lithuanian Commonwealth (1569-1795))',
                         'palatinate (The Polish-Lithuanian Commonwealth (1569-1795))',
                         'parish (Roman Catholic Church)',
                         'land (The Polish-Lithuanian Commonwealth (1569-1795))'
                         ])

# settlement type map
s_type_map = {}
s_type_map['dworzec'] = 'manor'
s_type_map['folwark'] = 'demesne'
s_type_map['zamek'] = 'castle'
s_type_map['huta szkła'] = 'glassworks'
s_type_map['kopalnia'] = 'mining settlement'
s_type_map['miasto'] = 'city/town'
s_type_map['opactwo'] = 'abbey'
s_type_map['osada folwarczna'] = 'demesne settlement'
s_type_map['osada karczemna'] = 'inn'
s_type_map['osada kuźnicza'] = 'ironworks'
s_type_map['osada młyńska'] = 'mill settlement'
s_type_map['osada smolna'] = 'tar pitch'
s_type_map['ostrów'] = 'ostrov'
s_type_map['przedmieście'] = 'suburb'
s_type_map['przedmieście lub wieś'] = 'suburb or village'
s_type_map['przewóz'] = 'haven'
s_type_map['pustka'] = 'unsettled area'
s_type_map['wieś'] = 'village'

# rodzaj własności
wlasnosc = {}
wlasnosc['k'] = elements['royal property']
wlasnosc['d'] = elements['church property']
wlasnosc['m'] = elements['town property']
wlasnosc['s'] = elements['noble property']

# obiekty gospodarcze
obiekty = {}
obiekty['browar'] = elements['brewery']
obiekty['folusz'] = elements['fulling mill']
obiekty['folwark'] = elements['demesne']
obiekty['forwark'] = elements['demesne']
obiekty['karczma'] = elements['tavern']
obiekty['krm'] = elements['tavern']
obiekty['karczma doroczna'] = elements['rental tavern']
obiekty['karczma dziedziczna'] = elements['hereditary tavern']
obiekty['kotły gorzałczane'] = elements['cauldron sauce']
obiekty['kocioł gorzałczany'] = elements['cauldron sauce']
obiekty['garniec gorzałczany'] = elements['cauldron sauce']
obiekty['kuźnia'] = elements['smithy']
obiekty['kuźnica'] = elements['ironwork']
obiekty['młyn'] = elements['mill']
obiekty['młyn doroczny'] = elements['rental mill']
obiekty['młyn dziedziczny'] = elements['hereditary mill']
obiekty['młyn korzeczny'] = elements['mill with overshot water wheel']
obiekty['młyn korzecznik'] = elements['mill with overshot water wheel']
obiekty['korzeczny'] = elements['mill with overshot water wheel']
obiekty['młyn walny'] = elements['mill with undershot water wheel']
obiekty['włyn walny'] = elements['mill with undershot water wheel']
obiekty['piec'] = elements['furnace']
obiekty['piła'] = elements['saw']
obiekty['ruda'] = elements['ore']
obiekty['stępa'] = elements['groats mortar']
obiekty['tartak'] = elements['sawmill']
obiekty['wiatrak'] = elements['windmill']
obiekty['wtr'] = elements['windmill']
obiekty['wiatrak doroczny'] = elements['rental windmill']
obiekty['wiatrak dziedziczny'] = elements['hereditary windmill']
obiekty['wyszynk'] = elements['wyszynk']
obiekty['wyszynk gorzałki'] = elements['wyszynk']

gospodarcze_wiele = {
                    'młyny doroczne':'młyn doroczny',
                    'karczmy':'karczma',
                    'młyny':'młyn',
                    "młynów":"młyn",
                    'młyny walne':'młyn walny',
                    'młyny dziedziczne':'młyn dziedziczny',
                    'młyny dziedzine':'młyn dziedziczny',
                    'młyny korzeczne':'młyn korzeczny',
                    'młyny doroczny':'młyn doroczny',
                    'młynów korzecznych':'młyn korzeczny',
                    'karczmy doroczne':'karczma doroczna',
                    'garnce gorzałczane':'kotły gorzałczane',
                    'kotły gorzałczane':'kotły gorzałczane',
                    'wyszynki':'wyszynk',
                    'folusze':'folusz',
                    'wiatraki':'wiatrak',
                    'wiatraki dziedziczne':'wiatrak dziedziczny'
                }

fun_centaralne_panstw = {}
fun_centaralne_panstw['kasztelania'] = elements["castellan's residence"]
fun_centaralne_panstw['księstwo'] = elements['capital of the duchy']
fun_centaralne_panstw['starostwo grodowe'] = elements['seat of the town starost']
fun_centaralne_panstw['starostwo grodowo'] = elements['seat of the town starost']
fun_centaralne_panstw['miejsce popisu rycerstwa'] = elements['the place where the knighthood was held']
fun_centaralne_panstw['okazowanie rycerstwa'] = elements['the place where the knighthood was held']
fun_centaralne_panstw['powiat'] = elements['the capital of a county']
fun_centaralne_panstw['sejmik generalny'] = elements['venue of the general assembly']
fun_centaralne_panstw['sejmik partykularny'] = elements['place of meeting of the local assembly']
fun_centaralne_panstw['trybunał koronny'] = elements['the seat of the crown tribunal']
fun_centaralne_panstw['starostwo niegrodowe'] = elements['seat of the non-garden starost (tenutarius)']
fun_centaralne_panstw['stolica państwa'] = elements['capital of the state']
fun_centaralne_panstw['województwo'] = elements['the capital of the province']
fun_centaralne_panstw['starostwo generalne Małopolski'] = elements['general starosty of Małopolska']
fun_centaralne_panstw['ziemia'] = elements['the capital of the land']

fun_centralne_koscielne = {}
fun_centralne_koscielne['archidiakonat'] = elements['the capital of an archdeaconry']
fun_centralne_koscielne['dekanat'] = elements['the capital of a deanery']
fun_centralne_koscielne['parafia'] = elements['the seat of a parish']
fun_centralne_koscielne['diecezja'] = elements['the capital of a diocese']
fun_centralne_koscielne['opactwo'] = elements['the seat of an abbey/ monastery']

# wojewodztwa
palatinates = {}
palatinates['brzeskie'] = get_palatinate('brzeskie')
palatinates['chełmińskie'] = get_palatinate('chełmińskie')
palatinates['inowrocławskie'] = get_palatinate('inowrocławskie')
palatinates['kaliskie'] = get_palatinate('kaliskie')
palatinates['krakowskie'] = get_palatinate('krakowskie')
palatinates['łęczyckie'] = get_palatinate('łęczyckie')
palatinates['lubelskie'] = get_palatinate('lubelskie')
palatinates['malborskie'] = get_palatinate('malborskie')
palatinates['mazowieckie'] = get_palatinate('mazowieckie')
palatinates['płockie'] = get_palatinate('płockie')
palatinates['podlaskie'] = get_palatinate('podlaskie')
palatinates['pomorskie'] = get_palatinate('pomorskie')
palatinates['poznańskie'] = get_palatinate('poznańskie')
palatinates['rawskie'] = get_palatinate('rawskie')
palatinates['ruskie'] = get_palatinate('ruskie')
palatinates['sandomierskie'] = get_palatinate('sandomierskie')
palatinates['sieradzkie'] = get_palatinate('sieradzkie')
palatinates['trockie'] = get_palatinate('trockie')
palatinates['ziemia dobrzyńska'] = get_palatinate('ziemia dobrzyńska')

unikalne = []
prng_qid_map = {}


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                        consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                        access_token=WIKIDARIAH_ACCESS_TOKEN,
                                        access_secret=WIKIDARIAH_ACCESS_SECRET,
                                        token_renew_period=14400)

    # tylko testowe
    test_rec = [
                'Nowa_Karczma_prz_gdn_pmr',
                'Ogony_rpn_dbr',
                'Augustow_blk_pdl',
                'Babimost_ksc_pzn',
                'Dobrzyn_dbr_dbr',
                'Szpetal_Dolny_dbr_dbr',
                'Czaple_Jarki_drh_pdl',
                'Bielony_Borysy_drh_pdl',
                'Czechowo_gzn_kls'
                ]

    for id_miejscowosci in test_rec:

        ok, element_qid = search_by_unique_id(properties['AHP id'], id_miejscowosci)
        if not ok:
            logger.error(f'ERROR: nie znaleziono elementu dla identyfikatora: {id_miejscowosci}')
            continue
        else:
            logger.info(f'INFO: weryfikacja miejscowości: {id_miejscowosci} ({element_qid})')

        wb_item = wbi_core.ItemEngine(item_id=element_qid)

        if id_miejscowosci == 'Nowa_Karczma_prz_gdn_pmr':
            # alias i stated as w j. niemieckim
            if not has_statement(element_qid, properties['stated as'], 'de:"Neukrug"'):
                logger.error("ERROR: brak właściwości 'stated as' = 'Neukrug' (dla języka niemieckiego)")
            aliasy = wb_item.get_aliases('de')
            if not 'Neukrug' in aliasy:
                logger.error(f"ERROR: {id_miejscowosci} - brak aliasu 'Neukrug' (dla języka niemieckiego)")

        if id_miejscowosci == 'Ogony_rpn_dbr':
            # przykład osady historycznej, bez prng
            description = wb_item.get_description('pl')
            if not 'osada historyczna' in description:
                logger.error(f"ERROR: {id_miejscowosci} - brak opisu 'osada historyczna'")

        if id_miejscowosci == 'Augustow_blk_pdl':
            # przykład miejscowości z obiektami gospodarczymi, w powiecie bielskim (woj. podlaskie)
            parameters = [(properties['instance of'], elements['district (The Polish-Lithuanian Commonwealth (1569-1795))'])]
            parameters.append((properties['part of'], palatinates['podlaskie']))
            ok, powiat_qid = element_search_adv("district bielski", 'en', parameters)
            if not ok:
                logger.error('ERROR: brak powiatu bielskiego w województwie podlaskim')
            else:
                if not has_statement(element_qid, properties['located in the administrative territorial entity'], powiat_qid):
                    logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'located in the administrative territorial entity' = {powiat_qid} (powiat bielski)")
            if not has_statement(element_qid, properties['contains an object type'], elements['fulling mill']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'contains an object type' = {elements['fulling mill']} (folusz, fulling mill)")
            if not has_statement(element_qid, properties['contains an object type'], elements['tavern']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'contains an object type' = {elements['tavern']} (karczma, tavern)")
            if not has_statement(element_qid, properties['contains an object type'], elements['mill']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'contains an object type' = {elements['mill']} (młyn, mill)")

        if id_miejscowosci == 'Babimost_ksc_pzn':
            # własność królewska, funkcja centralna kościelna - siedziba parafii, ma identyfikator SHG i 'stated as' z nazwą z SHG
            if not has_statement(element_qid, properties['settlement ownership type'], elements['royal property']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'settlement ownership type' = {elements['royal property']} (własność królewska)")

            if not has_statement(element_qid, properties['central church functions'], fun_centralne_koscielne['parafia']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central church functions' = {fun_centralne_koscielne['parafia']} (parafia)")

            if not has_statement(element_qid, properties['ID SHG'], '15704'):
                logger.error(f"ERROR: {id_miejscowosci} - brak identyfikatora 'ID SHG' = 15704")

        if id_miejscowosci == 'Dobrzyn_dbr_dbr':
            # Dobrzyn_dbr_dbr - nietypowe woj.: funkcje państowe:województwo, powiat, starostwo niegrodowe, kasztelania,
            # funkcje kościelne: archidiakonat, dekanat, parafia
            if not has_statement(element_qid, properties['central state functions'], fun_centaralne_panstw['powiat']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central state functions' = {fun_centaralne_panstw['powiat']} (powiat)")
            if not has_statement(element_qid, properties['central state functions'], fun_centaralne_panstw['województwo']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central state functions' = {fun_centaralne_panstw['województwo']} (województwo)")
            if not has_statement(element_qid, properties['central state functions'], fun_centaralne_panstw['starostwo niegrodowe']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central state functions' = {fun_centaralne_panstw['starostwo niegrodowe']} (starostwo niegrodowe)")
            if not has_statement(element_qid, properties['central state functions'], fun_centaralne_panstw['kasztelania']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central state functions' = {fun_centaralne_panstw['kasztelania']} (kasztelania)")

            if not has_statement(element_qid, properties['central church functions'], fun_centralne_koscielne['parafia']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central church functions' = {fun_centralne_koscielne['parafia']} (parafia)")
            if not has_statement(element_qid, properties['central church functions'], fun_centralne_koscielne['archidiakonat']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central church functions' = {fun_centralne_koscielne['archidiakonat']} (archidiakonat)")
            if not has_statement(element_qid, properties['central church functions'], fun_centralne_koscielne['dekanat']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'central church functions' = {fun_centralne_koscielne['dekanat']} (dekanat)")

        if id_miejscowosci == 'Szpetal_Dolny_dbr_dbr':
            # Szpetal_Dolny_dbr_dbr - dwie odmianki nazw, dwa rodzaje własności: duchowna, szlachecka
            if not has_statement(element_qid, properties['stated as'], 'pl:"Spital"'):
                logger.error("ERROR: brak właściwości 'stated as' = 'Spital' (dla języka polskiego)")
            if not has_statement(element_qid, properties['stated as'], 'pl:"Szpital"'):
                logger.error("ERROR: brak właściwości 'stated as' = 'Szpital' (dla języka polskiego)")

            if not has_statement(element_qid, properties['settlement ownership type'], elements['church property']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'settlement ownership type' = {elements['church property']} (własność duchowna)")
            if not has_statement(element_qid, properties['settlement ownership type'], elements['noble property']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'settlement ownership type' = {elements['noble property']} (własność szlachecka)")

        if id_miejscowosci == 'Czaple_Jarki_drh_pdl':
            # Czaple_Jarki_drh_pdl - osada historyczna, rodzaj lokalizacji: przybliżona
            description = wb_item.get_description('pl')
            if 'osada historyczna' not in description:
                logger.error(f"ERROR: {id_miejscowosci} - brak opisu 'osada historyczna'")
            if not has_statement(element_qid, properties['type of location'], elements['approximate location']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'type of location' = {elements['approximate location']} (przybliżona)")

        if id_miejscowosci == 'Bielony_Borysy_drh_pdl':
            # Bielony_Borysy_drh_pdl - własność szlachecka
            if not has_statement(element_qid, properties['settlement ownership type'], elements['noble property']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'settlement ownership type' = {elements['noble property']} (własność szlachecka)")

        if id_miejscowosci == 'Czechowo_gzn_kls':
            # Czechowo_gzn_kls - obiekty gospodarcze z liczbą: 2 wiatraki, link do wikidata
            if not has_statement(element_qid, properties['contains an object type'], obiekty['wiatrak']):
                logger.error(f"ERROR: {id_miejscowosci} - brak właściwości 'contains an object type' = {obiekty['wiatrak']} (wiatraki)")
