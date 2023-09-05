""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import os
import sys
import time
import re
import copy
import logging
import warnings
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
    elif value == 'księstwo siewierskie':
        label = 'The Duchy of Siewierz'
        palatinate_parameters = [(properties['instance of'], elements['county (The Duchy of Siewierz (1443-1790))'])]
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
file_log = Path('..') / 'log' / 'ahp_miejscowosci.log'
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_format = logging.Formatter('%(asctime)s - %(message)s')
c_handler = logging.StreamHandler()
c_handler.setFormatter(log_format)
c_handler.setLevel(logging.DEBUG)
logger.addHandler(c_handler)
# zapis logów do pliku tylko jeżeli uruchomiono z zapisem do wiki
if WIKIBASE_WRITE or 1:
    f_handler = logging.FileHandler(file_log)
    f_handler.setFormatter(log_format)
    f_handler.setLevel(logging.INFO)
    logger.addHandler(f_handler)

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
print('Przygotowanie słownika właściwości...')
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'settlement type', 'settlement ownership type', 'prng id',
                             'has facility', 'type of location',
                             'central state function', 'central church function',
                             'SIMC place ID', 'Wikidata item identifier', 'AHP ID',
                             'located in the administrative territorial entity',
                             'count', 'refine date', 'stated in'
                            ])

print('Przygotowanie słownika elementów definicyjnych...')
elements = get_elements(['human settlement',
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
                         'capital of an archdeaconry', 'capital of a deanery',
                         'seat of a parish', 'capital of a diocese',
                         'seat of an abbey/ monastery',
                         "castellan's residence", 'capital of the duchy',
                         'seat of the town starost', 'place where the knighthood was held',
                         'capital of a county', 'venue of the general assembly',
                         'place of meeting of the local assembly', 'seat of the crown tribunal',
                         'seat of the non-garden starost (tenutarius)', 'capital of the state',
                         'capital of the province', 'general starosty of Małopolska',
                         'capital of the land',
                         'district (The Polish-Lithuanian Commonwealth (1569-1795))',
                         'palatinate (The Polish-Lithuanian Commonwealth (1569-1795))',
                         'parish (Latin Church)',
                         'land (The Polish-Lithuanian Commonwealth (1569-1795))',
                         'county (The Duchy of Siewierz (1443-1790))',
                         'second half', 'parish (Orthodox Church)'
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
s_type_map['osada folwarczna'] = 'demesne'
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
obiekty['wiatrak dziedziny'] = elements['hereditary windmill']
obiekty['wyszynk'] = elements['wyszynk']
obiekty['wyszynk gorzałki'] = elements['wyszynk']

# obiekty gospodarcze l. mnoga -> l. pojedyncza
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

# słownik mapujący funkcje państwowe na identyfikatory QID
fun_centaralne_panstw = {}
fun_centaralne_panstw['kasztelania'] = elements["castellan's residence"]
fun_centaralne_panstw['księstwo'] = elements['capital of the duchy']
fun_centaralne_panstw['starostwo grodowe'] = elements['seat of the town starost']
fun_centaralne_panstw['starostwo grodowo'] = elements['seat of the town starost']
fun_centaralne_panstw['miejsce popisu rycerstwa'] = elements['place where the knighthood was held']
fun_centaralne_panstw['okazowanie rycerstwa'] = elements['place where the knighthood was held']
fun_centaralne_panstw['powiat'] = elements['capital of a county']
fun_centaralne_panstw['sejmik generalny'] = elements['venue of the general assembly']
fun_centaralne_panstw['sejmik partykularny'] = elements['place of meeting of the local assembly']
fun_centaralne_panstw['trybunał koronny'] = elements['seat of the crown tribunal']
fun_centaralne_panstw['starostwo niegrodowe'] = elements['seat of the non-garden starost (tenutarius)']
fun_centaralne_panstw['stolica państwa'] = elements['capital of the state']
fun_centaralne_panstw['województwo'] = elements['capital of the province']
fun_centaralne_panstw['starostwo generalne Małopolski'] = elements['general starosty of Małopolska']
fun_centaralne_panstw['ziemia'] = elements['capital of the land']

# słownik mapujący funkcje kościelne na identyfikatory QID
fun_centralne_koscielne = {}
fun_centralne_koscielne['archidiakonat'] = elements['capital of an archdeaconry']
fun_centralne_koscielne['dekanat'] = elements['capital of a deanery']
fun_centralne_koscielne['parafia'] = elements['seat of a parish']
fun_centralne_koscielne['diecezja'] = elements['capital of a diocese']
fun_centralne_koscielne['opactwo'] = elements['seat of an abbey/ monastery']

# województwa - słownik identyfikatorów QID dla województw, ziemi i księstw
palatinates = {}
palatinates['brzeskie kujawskie'] = get_palatinate('brzeskie kujawskie')
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
palatinates['sandomierskie'] = get_palatinate('sandomierskie')
palatinates['sieradzkie'] = get_palatinate('sieradzkie')
palatinates['ziemia dobrzyńska'] = get_palatinate('ziemia dobrzyńska')
palatinates['księstwo siewierskie'] = get_palatinate('księstwo siewierskie')

# mapowanie skrótowych nazw parafii na nazwy pełne
wyjatki_parafie = {}
wyjatki_parafie['Sandomierz - Paweł Ap'] = 'Sandomierz - under the invocation of St. Paul the Apostle'
wyjatki_parafie['Ostrów - NMP'] = 'Ostrów - under invocation of the Blessed Virgin Mary'
wyjatki_parafie['Łęgonice - Jan Ch'] = 'Łęgonice - under the invocation of John the Baptist'
wyjatki_parafie['Rokitno - Wojciech Bp'] = 'Rokitno - under the invocation of St. Adalbert the Bishop'
wyjatki_parafie['Kraków - Szczepan M'] = 'Kraków - under the invocation of St. Stephen the Martyr'
wyjatki_parafie['Łowicz - NMP'] = 'Łowicz - under the invocation of the Blessed Virgin Mary'
wyjatki_parafie['Czemierniki - town'] = 'Czemierniki'
wyjatki_parafie['Kazimierz - Stanisław Bp, Michał A'] = 'Kazimierz - under the invocation of St. Stanislaus the Bishop and St. Michael the Archangel'
wyjatki_parafie['Gniezno - Piotr Ap'] = 'Gniezno - under the invocation of St. Peter the Apostle'
wyjatki_parafie['Kazimierz - Jakub W Ap'] = 'Kazimierz - under the invocation of St. James the Greater Apostle'
wyjatki_parafie['Sandomierz - Piotr Ap'] = 'Sandomierz - under the invocation of Peter the Apostle'
wyjatki_parafie['Łowicz - Św. Duch'] = 'Łowicz - under the invocation of the Holy Spirit'
wyjatki_parafie['Kraków - NMP'] = 'Krakow - under the invocation of the Blessed Virgin Mary'
wyjatki_parafie['Poznań - Mikołaj Bp'] = 'Poznań - under the invocation of St. Nicolas the Bishop'
wyjatki_parafie['Rokitno - Jakub W Ap'] = 'Rokitno - under the invocation of St James the Greater Apostle'
wyjatki_parafie['Kalisz - Mikołaj Bp'] = 'Kalisz - under the invocation of St. Nicolas the Bishop'
wyjatki_parafie['Gniezno - Michał A'] = 'Gniezno - under the invocation of St. Michael the Archangel'
wyjatki_parafie['Kraków - Mikołaj Bp'] = 'Krakow - under the invocation of St. Nicolas the Bishop'
wyjatki_parafie['Gniezno - Św. Trójca'] = 'Gniezno - under the invocation of St. Trinity'
wyjatki_parafie['Kalisz - NMP'] = 'Kalisz - under the invocation of the Blessed Virgin Mary'
wyjatki_parafie['Gniezno - Wawrzyniec M'] = 'Gniezno -under the invocation of St. Laurence the Martyr'
wyjatki_parafie['Ostrów - Jan Ch'] = 'Ostrów - under the invocation of St. John the Baptist'
wyjatki_parafie['Żerków - Stanisław Bp'] = 'Żerków - under the invocation of St. Stanislaus the Bishop'
wyjatki_parafie['Żerków - Mikołaj Bp'] = 'Żerków - under the invocation of Mikołaj Biskupa'
wyjatki_parafie['Poznań - Jan Ch'] = 'Poznań - under the invocation of Saint John the Baptist'
wyjatki_parafie['Poznań - Marcin Bp'] = 'Poznań - under the invocation of Martin the Bishop'
wyjatki_parafie['Poznań - Wojciech Bp'] = 'Poznań - under the invocation of St. Adalbert the Bishop'
wyjatki_parafie['Kraków - Wszyscy Św'] = 'Kraków - under the invocation of All Saints'
wyjatki_parafie['Poznań - Maria Magdalena'] = 'Poznań - under the invocation of Mary Magdalene'
wyjatki_parafie['Kraków - Św. Krzyż'] = 'Kraków - under the invocation of St. Cross'
wyjatki_parafie['Kraków - Anna'] = 'Krakow - under the invocation of St. Anne'
wyjatki_parafie['Łęgonice - Maria Magdalena'] = 'Łęgonice - under the invocation of Mary Magdalene'
wyjatki_parafie['Kazimierz - Boże Ciało'] = 'Kazimierz - under the invocation of Corpus Christi'


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

    # plik pomocniczy z indeksem nr lini -> QID
    file_index = Path('..') / 'data' / 'ahp_miejscowosci_line_qid.csv'

    logger.info('POCZĄTEK IMPORTU')

    # wczytanie słownika z mapowaniem prng -> qid  - ten plik trzeba przygotować dla docelowej wiki
    # gdyż tam będą inne symbole QID
    file_map = Path('..') / 'data' / 'prng_qid.csv'
    with open(file_map, 'r', encoding='utf-8') as fm:
        map_lines = fm.readlines()
    map_lines = [map_line.strip() for map_line in map_lines]
    for map_line in map_lines:
        t_line = map_line.split(',')
        prng_qid_map[t_line[0].strip()] = t_line[1].strip()

    # wczytanie głównych danych
    file_name = Path('..') / 'data' / 'ahp_miejscowosci.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    references = {}
    references[properties['stated in']] = 'Q234031' # referencja do elementu AHP w instancji testowej!
    references[properties['retrieved']] = '2023-06-15'

    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/7' # XVI wiek
    qualifiers[properties['refine date']] = elements['second half']     # druga połowa

    # czy to pierwsze ładowanie danych? - wówczas bez dodatkowej weryfikacji
    first_load = True

    line_number = 0
    for line in lines:
        line_number +=1

        t_line = line.split('@')
        id_miejscowosci = t_line[0].strip()

        nazwa_slownikowa = t_line[1].strip()
        nazwa_wspolczesna = t_line[2].strip()
        nazwa_odmianki = t_line[3].strip()
        nazwa_16w = t_line[4].strip()
        charakter_osady = t_line[5].strip()
        rodzaj_wlasnosci = t_line[6].strip()
        parafia = t_line[7].strip()
        obiekty_gospodarcze = t_line[8].strip()
        rodzaj_lokalizacji = t_line[9].strip()
        komentarz_do_lokalizacji = t_line[10].strip()
        funkcje_centralne_panstwowe = t_line[11].strip()
        funkcje_centralne_koscielne = t_line[12].strip()
        m_nadrz = t_line[13].strip()
        powiat_p = t_line[14].strip()
        woj_p = t_line[15].strip()
        wielkosc_karto = t_line[16].strip()
        klasa_obiektow = t_line[17].strip()
        zbiorcza_prng = t_line[18].strip()
        simc = t_line[19].strip()
        wikidata = t_line[20].strip()
        latitude = t_line[21].strip()
        longitude = t_line[22].strip()


        # modyfikacja niektórych wartości
        if rodzaj_lokalizacji == 'przybliżona':
            rodzaj_lokalizacji = 'approximate location'
        elif rodzaj_lokalizacji == 'nieznana':
            rodzaj_lokalizacji = 'location unknown'

        # szukanie w wiki po identyfikatorze prng
        element_qid = ''
        instance_of = ''

        if zbiorcza_prng:
            if zbiorcza_prng in prng_qid_map:
                ok_prng = True
                element_qid = prng_qid_map[zbiorcza_prng]
            else:
                ok_prng, element_qid = search_by_unique_id(properties['prng id'], zbiorcza_prng)

            # rekordy z prng którego nie udało się znaleźć w wikibase są na razie pomijane
            if not ok_prng:
                logger.error(f'ERROR: ({id_miejscowosci}) Nie znaleziono elementu dla PRNG {zbiorcza_prng}, {element_qid}')
                continue
        # nie ma prng, należy dodać nowy element z miejscowością historyczną, o ile już nie istnieje
        else:
            # szukanie czy aby nie istnieje
            if not nazwa_16w:
                # nie ma nazwy z 16 wieku - obecnie pomijamy
                continue
            else:
                # jest nazwa z 16 wieku
                parameters = [(properties['instance of'], elements['human settlement']),
                              (properties['stated as'], f'pl:"{nazwa_16w}"')]
                ok, element_qid = element_search_adv(f"{nazwa_16w}", 'en', parameters,
                                    description=f"historical settlement from the Historical Atlas of Poland (parish {parafia}, district {powiat_p}, palatinate {woj_p})")

            # jeżeli nie ma w wikibase to przygotowanie etykiet i description do dodania
            # w szczególnych przypadkach dodać własność do description?
            if not ok:
                element_qid = '' # czyszczenie, może zawierać zapis 'NOT FOUND' z funkcji wyszukującej

                # utworzenie przynależności administracyjnej dla description
                desc_add_pl = []
                desc_add_en = []
                if parafia:
                    desc_add_pl.append(f"parafia {parafia}")
                    desc_add_en.append(f"parish {parafia}")
                if powiat_p:
                    desc_add_pl.append(f"powiat {powiat_p}")
                    desc_add_en.append(f"district {powiat_p}")
                if woj_p:
                    if woj_p.startswith('ziemia') or woj_p.startswith('Ziemia'):
                        desc_add_pl.append(f"{woj_p}")
                        desc_add_en.append(f"{woj_p.replace('ziemia', 'land')}")
                    else:
                        desc_add_pl.append(f"województwo {woj_p}")
                        desc_add_en.append(f"palatinate {woj_p}")

                label_pl = label_en = nazwa_16w
                description_pl = f"osada historyczna z Atlasu Historycznego Polski ({', '.join(desc_add_pl)})"
                description_en = f"historical settlement from the Historical Atlas of Poland ({', '.join(desc_add_en)})"

                # testowanie unikalności pary label-description
                identyfikator = label_en + ' : ' + description_en
                if identyfikator not in unikalne:
                    unikalne.append(identyfikator)
                else:
                    logger.error(f'ERROR: ({id_miejscowosci}) Brak unikalności pary label-description, {identyfikator}')

                instance_of = elements['human settlement']

        # przygotowanie struktur wikibase
        data = []
        aliasy = {}

        # ===== instance of =====
        if instance_of:
            statement = create_statement_data(properties['instance of'],
                                              instance_of,
                                              None, None, add_ref_dict=None)
            if statement:
                data.append(statement)

        # ===== stated as - nazwa 16w =====
        if nazwa_16w:
            if not element_qid or first_load or not has_statement(element_qid, properties['stated as'], f'pl:"{nazwa_16w}"'):
                # rozpoznawanie języka
                lang = detect(nazwa_16w)
                if lang != 'de':
                    lang = 'pl'
                if 'neu' in nazwa_16w.lower() and lang != 'de':
                    lang = 'de'

                if element_qid:
                    if lang in aliasy:
                        aliasy[lang].append(nazwa_16w)
                    else:
                        aliasy[lang] = [nazwa_16w]

                statement = create_statement_data(properties['stated as'],
                                                  f'{lang}:"{nazwa_16w}"',
                                                  None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== stated as - nazwa słownikowa =====
        if nazwa_slownikowa:
            if not element_qid or first_load or not has_statement(element_qid, properties['stated as'], f'pl:"{nazwa_slownikowa}"'):
                if 'pl' in aliasy:
                    aliasy['pl'].append(nazwa_slownikowa)
                else:
                    aliasy['pl'] = [nazwa_slownikowa]
                #shg_references = {}
                #if zbiorcza_sgh_id:
                #    shg_references[properties['reference URL']] = f'http://www.slownik.ihpan.edu.pl/search.php?id={zbiorcza_sgh_id}'
                #else:
                #    shg_references[properties['reference URL']] = 'http://www.slownik.ihpan.edu.pl/'
                #statement = create_statement_data(properties['stated as'],
                #                                  f'pl:"{nazwa_slownikowa}"',
                #                                  shg_references, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== stated as - nazwa odmianki =====
        if nazwa_odmianki:
            t_odmianki = nazwa_odmianki.split(",")
            for t_odm in t_odmianki:
                t_odm = t_odm.strip()
                if not t_odm: # pomijanie pustych
                    continue
                if not element_qid or first_load or not has_statement(element_qid, properties['stated as'], f'pl:"{t_odm}"'):
                    if 'pl' in aliasy:
                        aliasy['pl'].append(t_odm)
                    else:
                        aliasy['pl'] = [t_odm]
                    statement = create_statement_data(properties['stated as'],
                                                  f'pl:"{t_odm}"',
                                                  None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== settlement type =====
        if charakter_osady:
            t_charakter_osady = charakter_osady.split(' i ')
            for t_char in t_charakter_osady:
                t_char = t_char.strip()

                # wyjąteczki
                if t_char == 'młyńska':
                    t_char = 'osada młyńska'
                if t_char == 'staw':
                    continue

                if t_char not in s_type_map:
                    print(f'ERROR: ({id_miejscowosci}) nieznany charakter osady:', charakter_osady)
                    sys.exit(1)

                settlement_type = s_type_map[t_char]
                if not element_qid or first_load or not has_statement(element_qid, properties['settlement type'], elements[settlement_type]):
                    statement = create_statement_data(properties['settlement type'],
                                                 elements[settlement_type],
                                                  None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== settlement ownership type =====
        if rodzaj_wlasnosci:
            for ch in rodzaj_wlasnosci:
                if ch in wlasnosc:
                    if not element_qid or first_load or not has_statement(element_qid, properties['settlement ownership type'], wlasnosc[ch]):
                        statement = create_statement_data(properties['settlement ownership type'],
                                                  wlasnosc[ch],
                                                  None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)

        # ===== has facility =====
        if obiekty_gospodarcze:
            if ',' in obiekty_gospodarcze:
                obiekty_gospodarcze = obiekty_gospodarcze.replace(',',';')

            # najpierw wyjątki
            if obiekty_gospodarcze == '6 młynów (w tym folusz)':
                t_obiekty = ['6 młynów', 'folusz']
            else:
                t_obiekty = obiekty_gospodarcze.split(';')

            for t_ob in t_obiekty:
                t_ob = t_ob.strip()
                liczba = '1'
                pattern = r'\d{1,3}'
                match = re.search(pattern=pattern, string=t_ob)
                if match:
                    liczba = match.group()
                    t_ob = t_ob.replace(liczba, '').strip()
                    # jeżeli nazwa w liczbie mnogiej to zamiana na pojedynczną
                    if t_ob in gospodarcze_wiele:
                        t_ob = gospodarcze_wiele[t_ob]

                # wyjątek
                if t_ob == 'dwa wiatraki':
                    t_ob = 'wiatrak'
                    liczba = '2'

                # jeżeli liczba mnoga bez podanej konkretnej liczby
                if t_ob in gospodarcze_wiele:
                    if liczba == '1':
                        liczba = 'somevalue'
                    # przekształcenie na liczbę pojedynczną (zwykle)
                    t_ob = gospodarcze_wiele[t_ob]

                # dodanie kwalifikatora 'count'
                ob_qualifiers = copy.deepcopy(qualifiers)
                ob_qualifiers[properties['count']] = liczba
                if not element_qid or first_load or not has_statement(element_qid, properties['has facility'], obiekty[t_ob]):
                    statement = create_statement_data(properties['has facility'],
                                                obiekty[t_ob],
                                                None, qualifier_dict=ob_qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== rodzaj lokalizacji =====
        if rodzaj_lokalizacji and rodzaj_lokalizacji in ['location unknown', 'approximate location']:
            if not element_qid or first_load or not has_statement(element_qid, properties['type of location'], elements[rodzaj_lokalizacji]):
                statement = create_statement_data(properties['type of location'],
                                                elements[rodzaj_lokalizacji],
                                                None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== funkcje centralne państwowe =====
        if funkcje_centralne_panstwowe:
            if ';' in funkcje_centralne_panstwowe:
                funkcje_centralne_panstwowe = funkcje_centralne_panstwowe.replace(';', ',')
            t_funkcje = funkcje_centralne_panstwowe.split(',')
            for t_fun in t_funkcje:
                t_fun = t_fun.strip()
                if t_fun in fun_centaralne_panstw:
                    funkcja_panstwowa = fun_centaralne_panstw[t_fun]
                    if not element_qid or first_load or not has_statement(element_qid, properties['central state function'], funkcja_panstwowa):
                        statement = create_statement_data(properties['central state function'],
                                                funkcja_panstwowa,
                                                None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.info(f'ERROR: ({id_miejscowosci}) nieznana funkcja państwowa {t_fun}')

        # ===== funkcje centralne kościelne (central church functions) =====
        if funkcje_centralne_koscielne:
            if ';' in funkcje_centralne_koscielne:
                funkcje_centralne_koscielne = funkcje_centralne_koscielne.replace(';', ',')
            t_funkcje = funkcje_centralne_koscielne.split(',')
            for t_fun in t_funkcje:
                t_fun = t_fun.strip()
                if t_fun in fun_centralne_koscielne:
                    funkcja_koscielna = fun_centralne_koscielne[t_fun]
                    if not element_qid or first_load or not has_statement(element_qid, properties['central church function'], funkcja_koscielna):
                        statement = create_statement_data(properties['central church function'],
                                                funkcja_koscielna,
                                                None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.info(f'ERROR: ({id_miejscowosci}) nieznana funkcja kościelna {t_fun}')

        # ===== współrzędne miejscowości =====
        # np. Point (23.29833332 52.68194448)
        if latitude and longitude:
            coordinate = f'{latitude},{longitude}'
            if not element_qid or first_load or not has_statement(element_qid, properties['coordinate location'], coordinate):
                statement = create_statement_data(properties['coordinate location'],
                                                  coordinate, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)


        # ===== SIMC place ID ======
        if simc:
            if not element_qid or first_load or not has_statement(element_qid, properties['SIMC place ID'], simc):
                statement = create_statement_data(properties['SIMC place ID'],
                                                  simc, None, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== wikidata =====
        # np. http://www.wikidata.org/entity/Q7848867
        if wikidata:
            q_wikidata = wikidata.replace('http://www.wikidata.org/entity/','').strip()
            if not element_qid or first_load or not has_statement(element_qid, properties['Wikidata item identifier'], q_wikidata):
                statement = create_statement_data(properties['Wikidata item identifier'],
                                                  q_wikidata, None, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== AHP id =====
        if id_miejscowosci:
            if not element_qid or first_load or not has_statement(element_qid, properties['AHP ID'], id_miejscowosci):
                statement = create_statement_data(properties['AHP ID'],
                                                  id_miejscowosci, None, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== shg_id =====
        # if zbiorcza_sgh_id:
        #     if not element_qid or first_load or not has_statement(element_qid, properties['ID SHG'], zbiorcza_sgh_id):
        #         statement = create_statement_data(properties['ID SHG'],
        #                                           zbiorcza_sgh_id, None, None, add_ref_dict=references, if_exists='APPEND')
        #         if statement:
        #             data.append(statement)

        # ===== located in the administrative territorial entity =====
        if powiat_p and powiat_p != 'księstwo siewierskie':
            if ' i ' in powiat_p:
                t_powiaty = powiat_p.split(' i ')
            elif powiat_p == 'brzeski kujawski lub przedecki':
                t_powiaty = ['brzeski kujawski', 'przedecki']
            else:
                t_powiaty = [powiat_p]

            for t_powiat in t_powiaty:
                t_powiat = t_powiat.strip()

                parameters = [(properties['instance of'], elements['district (The Polish-Lithuanian Commonwealth (1569-1795))'])]
                if woj_p:
                    # specjalna obsługa dla dziwnych przypadków
                    if woj_p == 'rawskie i brzeskie kujawskie':
                        if t_powiat == 'kowalski':
                            woj_powiat = 'brzeskie kujawskie'
                        elif t_powiat == 'gostyniński':
                            woj_powiat = 'rawskie'
                    elif woj_p == 'brzeskie kujawskie i inowrocławskie':
                        if t_powiat == 'kruszwicki':
                            woj_powiat = 'brzeskie kujawskie'
                        elif t_powiat == 'inowrocławski':
                            woj_powiat = 'inowrocławskie'
                    else:
                        woj_powiat = woj_p

                    parameters.append((properties['part of'], palatinates[woj_powiat]))
                ok, powiat_qid = element_search_adv(f"district {t_powiat}", 'en', parameters)
                if ok:
                    if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], powiat_qid):
                        statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                    powiat_qid, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.error(f'ERROR: ({id_miejscowosci}) nie znaleziono powiatu: {t_powiat}')

        # jeżeli nie ma powiatu to jednostką jest województwo
        if not powiat_p and woj_p:
            woj_qid = palatinates[woj_p]
            if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], woj_qid):
                statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                  woj_qid, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== located in the administrative territorial entity =====
        if parafia and parafia != '[nieznana]':
            if ';' in parafia:
                t_parafie = parafia.split(';')
            elif ' i ' in parafia:
                t_parafie = parafia.split(' i ')
            elif ' lub ' in parafia:
                t_parafie = parafia.split(' lub ')
            else:
                t_parafie = [parafia]

            for t_parafia in t_parafie:
                t_parafia = t_parafia.strip()
                if t_parafia in wyjatki_parafie:
                    t_parafia = wyjatki_parafie[t_parafia]

                qualifiers_parafia = copy.deepcopy(qualifiers)
                if t_parafia.endswith('?'):
                    qualifiers_parafia['information status'] = 'uncertain'
                    t_parafia = t_parafia[:-1]
                elif ' lub ' in parafia:
                    qualifiers_parafia['information status'] = 'uncertain'

                if 'prawosławna' in t_parafia:
                    parameters = [(properties['instance of'], elements['parish (Orthodox Church)'])]
                    label_to_search = f"orthodox parish {t_parafia}"
                    label_to_search = label_to_search.replace('(prawosławna)','').strip()
                else:
                    parameters = [(properties['instance of'], elements['parish (Latin Church)'])]
                    label_to_search = f"parish {t_parafia}"

                ok, parafia_qid = element_search_adv(label_to_search, 'en', parameters)
                if ok:
                    if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], parafia_qid):

                        statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                    parafia_qid, None, qualifier_dict=qualifiers_parafia, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.error(f'ERROR: ({id_miejscowosci}) nie znaleziono parafii: {t_parafia}')

        # ===== etykiety, description =====
        if not zbiorcza_prng:
            # nowy element - osada historyczna
            new_element = True
            wb_item = wbi_core.ItemEngine(new_item=True, data=data)
            wb_item.set_label(label_en, lang='en')
            wb_item.set_label(label_pl,lang='pl')

            wb_item.set_description(description_en, 'en')
            wb_item.set_description(description_pl, 'pl')
        else:
            # istniejący już element
            new_element = False
            wb_item = wbi_core.ItemEngine(item_id=element_qid, data=data)
            label_pl = wb_item.get_label('pl')
            label_en = wb_item.get_label('en')
            description_pl = wb_item.get_description('pl')
            description_en = wb_item.get_description('en')

        # ===== aliasy =====
        if aliasy:
            for alias_lang, alias_value in aliasy.items():
                for alias_item in alias_value:
                    wb_item.set_aliases(alias_item, alias_lang)

        if WIKIBASE_WRITE:
            element_qid = write_or_exit(login_instance, wb_item, logger)

            if new_element:
                message = f'({line_number}, {id_miejscowosci}) Dodano: # [https://prunus-208.man.poznan.pl/wiki/Item:{element_qid} {label_pl}]'
            else:
                message = f'({line_number}, {id_miejscowosci}) Zaktualizowano: # [https://prunus-208.man.poznan.pl/wiki/Item:{element_qid} {label_pl}]'

            logger.info(message)

            # zapis pomocniczego indeksu który posłuży do uzupełniania właściwości 'okolic'
            if element_qid:
                with open(file_index, 'a', encoding='utf-8') as fi:
                    fi.write(f'{line_number},{element_qid}\n')

        else:
            if not element_qid:
                element_qid = 'TEST'
            logger.info(f"({line_number}, {id_miejscowosci}) Przygotowano dodanie/uzupełnienie: # [https://prunus-208.man.poznan.pl/wiki/Item:{element_qid} {label_pl}]")

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
