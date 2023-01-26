""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import os
import time
import logging
import warnings
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import element_search_adv, get_properties, get_elements
from wikidariahtools import search_by_unique_id
from property_import import has_statement

warnings.filterwarnings("ignore")

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
logger.info('Przygotowanie słownika właściwości...')
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'settlement type', 'settlement ownership type', 'prng id',
                             'contains an object type', 'type of location',
                             'central state functions', 'central church functions',
                             'SIMC place ID', 'Wikidata ID', 'AHP id',
                             'located in the administrative territorial entity',
                             'count', 'ID SHG'
                            ])

logger.info('Przygotowanie słownika elementów definicyjnych...')
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

    # dane pomocnicze
    parameters = [(properties['instance of'], elements['district (The Polish-Lithuanian Commonwealth (1569-1795))'])]
    parameters.append((properties['part of'], palatinates['podlaskie']))
    ok, powiat_qid = element_search_adv("district bielski", 'en', parameters)
    if not ok:
        logger.error('ERROR: brak powiatu bielskiego w województwie podlaskim')

    parafia = fun_centralne_koscielne['parafia']
    powiat = fun_centaralne_panstw['powiat']
    wojewodztwo = fun_centaralne_panstw['województwo']
    starostwo_niegrodowe = fun_centaralne_panstw['starostwo niegrodowe']
    kasztelania = fun_centaralne_panstw['kasztelania']
    archidiakonat = fun_centralne_koscielne['archidiakonat']
    dekanat = fun_centralne_koscielne['dekanat']
    wiatrak = obiekty['wiatrak']

    # przypadki testowe na razie jak lista krotek,
    # każda krotka zawiera:
    #   - identyfikator elementu, obecnie poprzez statement z unikalnym identyfikatorem
    #   - rodzaj informacji do sprawdzenia, obecnie: STATEMENT, ALIAS, DESCRIPTION
    #   - nazwa właściwości w przypadku STATEMENT, lub kod języka w przypadku ALIAS lub DESCRIPTION
    #   - wartość, w przypadku STATEMENT może to być tekst dla właściwości typu string ('example'),
    #     lub item jeżeli jest w obsługiwanych elementach, wówczas przed etykietą identyfikującą element
    #     powinno znaleźć się słowo ITEM: np. 'ITEM:fulling mill'
    #     w przypadku ALIAS powinien to być pełny tekst aliasu, w przypadku DESCRIPTION
    #     może to być fragment opisu elementu.

    test_rec = [
                ('STATEMENT:AHP id|VALUE:Nowa_Karczma_prz_gdn_pmr', 'STATEMENT','stated as','de:"Neukrug"'),
                ('STATEMENT:AHP id|VALUE:Nowa_Karczma_prz_gdn_pmr', 'ALIAS','de','Neukrug'),
                ('STATEMENT:AHP id|VALUE:Ogony_rpn_dbr', 'DESCRIPTION','pl','osada historyczna'),
                ('STATEMENT:AHP id|VALUE:Augustow_blk_pdl', 'STATEMENT', 'contains an object type', 'ITEM:fulling mill'),
                ('STATEMENT:AHP id|VALUE:Augustow_blk_pdl', 'STATEMENT', 'contains an object type', 'ITEM:tavern'),
                ('STATEMENT:AHP id|VALUE:Augustow_blk_pdl', 'STATEMENT', 'contains an object type', 'ITEM:mill'),
                ('STATEMENT:AHP id|VALUE:Augustow_blk_pdl', 'STATEMENT', 'located in the administrative territorial entity', powiat_qid),
                ('STATEMENT:AHP id|VALUE:Babimost_ksc_pzn', 'STATEMENT', 'settlement ownership type', 'ITEM:royal property'),
                ('STATEMENT:AHP id|VALUE:Babimost_ksc_pzn', 'STATEMENT', 'central church functions', parafia),
                ('STATEMENT:AHP id|VALUE:Babimost_ksc_pzn', 'STATEMENT', 'ID SHG', '15704'),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central state functions', powiat),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central state functions', wojewodztwo),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central state functions', starostwo_niegrodowe),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central state functions', kasztelania),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central church functions', parafia),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central church functions', archidiakonat),
                ('STATEMENT:AHP id|VALUE:Dobrzyn_dbr_dbr','STATEMENT','central church functions', dekanat),
                ('STATEMENT:AHP id|VALUE:Szpetal_Dolny_dbr_dbr','STATEMENT','stated as', 'pl:"Spital"'),
                ('STATEMENT:AHP id|VALUE:Szpetal_Dolny_dbr_dbr','STATEMENT','stated as', 'pl:"Szpital"'),
                ('STATEMENT:AHP id|VALUE:Szpetal_Dolny_dbr_dbr','STATEMENT','settlement ownership type','ITEM:church property'),
                ('STATEMENT:AHP id|VALUE:Szpetal_Dolny_dbr_dbr','STATEMENT','settlement ownership type','ITEM:noble property'),
                ('STATEMENT:AHP id|VALUE:Czaple_Jarki_drh_pdl','DESCRIPTION', 'pl', 'osada historyczna'),
                ('STATEMENT:AHP id|VALUE:Czaple_Jarki_drh_pdl','STATEMENT','type of location', 'ITEM:approximate location'),
                ('STATEMENT:AHP id|VALUE:Bielony_Borysy_drh_pdl','STATEMENT','settlement ownership type','ITEM:noble property'),
                ('STATEMENT:AHP id|VALUE:Czechowo_gzn_kls', 'STATEMENT', 'contains an object type', wiatrak)

                ]

    logger.info('Uruchomienie testów...')

    for identyfikator, cmd_type, cmd_prop, cmd_value in test_rec:
        # obecnie obsługa tylko identyfikatorów w formie jednoznacznie
        # identyfikującej deklaracji np. 'AHP id' = 'Czechowo_gzn_kls'

        property_id = value_id = ''
        t_identyfikator = identyfikator.split('|')
        typ_id = t_identyfikator[0].strip()
        if typ_id.split(':')[0].strip() == 'STATEMENT':
            property_id = typ_id.split(':')[1].strip()
        value_id = t_identyfikator[1].strip()
        if value_id.split(':')[0].strip() == 'VALUE':
            value_id = value_id.split(':')[1].strip()

        if not property_id or not value_id:
            logger.error(f'ERROR: nieprawidłowa definicja danych testowych {identyfikator}')
            continue

        ok, element_qid = search_by_unique_id(properties[property_id], value_id)
        if not ok:
            logger.error(f'ERROR: nie znaleziono elementu dla identyfikatora: {identyfikator}')
            continue

        wb_item = wbi_core.ItemEngine(item_id=element_qid)

        if cmd_type == 'STATEMENT':
            if cmd_value.startswith('ITEM:'):
                cmd_value_text = f"('{cmd_value[5:]}')"
                cmd_value = elements[cmd_value[5:]]
            else:
                cmd_value_text = ''

            if not has_statement(element_qid, properties[cmd_prop], cmd_value):
                logger.error(f"ERROR: brak właściwości '{cmd_prop}' = {cmd_value} {cmd_value_text}")
            else:
                logger.info(f"OK: [{value_id}] - poprawna właściwość '{cmd_prop}' = {cmd_value} {cmd_value_text}")
        elif cmd_type == 'ALIAS':
            aliasy = wb_item.get_aliases(cmd_prop)
            if cmd_value not in aliasy:
                logger.error(f"ERROR: [{value_id}] - brak aliasu '{cmd_value}'")
            else:
                logger.info(f"OK: [{value_id}] - poprawny alias '{cmd_value}'")
        elif cmd_type == 'DESCRIPTION':
            description = wb_item.get_description(cmd_prop)
            if cmd_value not in description:
                logger.error(f"ERROR: [{value_id}] - brak opisu '{cmd_value}'")
            else:
                logger.info(f"OK: [{value_id}] - poprawny opis, zawiera tekst '{cmd_value}'")
