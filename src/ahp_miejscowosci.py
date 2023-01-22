""" import miejscowości z AHP (XVI wiek) """
# pylint: disable=logging-fstring-interpolation

import os
import sys
import time
import re
import copy
import logging
from pathlib import Path
from dotenv import load_dotenv
from langdetect import detect
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import element_search_adv, get_properties, get_elements, search_by_unique_id
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

# standardowe właściwości i elementy (P i Q wyszukiwane w wikibase raz i trzymane w słownikach)
print('Przygotowanie słownika właściwości...')
properties = get_properties(['instance of', 'stated as', 'reference URL', 'retrieved',
                             'point in time', 'part of', 'has part or parts', 'coordinate location',
                             'settlement type', 'settlement ownership type', 'prng id',
                             'economic object', 'type of location',
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
                         'parish (Roman Catholic Church)'
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

unikalne = []
prng_qid_map = {}


# ------------------------------------MAIN -------------------------------------

if __name__ == '__main__':

    # logowanie do instancji wikibase
    if WIKIBASE_WRITE:
        login_instance = wbi_login.Login(consumer_key=WIKIDARIAH_CONSUMER_TOKEN,
                                         consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                         access_token=WIKIDARIAH_ACCESS_TOKEN,
                                         access_secret=WIKIDARIAH_ACCESS_SECRET,
                                         token_renew_period=14400)

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

    # plik pomocniczy z indeksem nr lini -> QID
    file_index = Path('..') / 'data' / 'ahp_line_qid.csv'

    logger.info('POCZĄTEK IMPORTU')

    # wczytanie słownika z mapowaniem prng -> qid
    file_map = Path('..') / 'data' / 'prng_qid.csv'
    with open(file_map, 'r', encoding='utf-8') as fm:
        map_lines = fm.readlines()
    map_lines = [map_line.strip() for map_line in map_lines]
    for map_line in map_lines:
        t_line = map_line.split(',')
        prng_qid_map[t_line[0].strip()] = t_line[1].strip()

    file_name = Path('..') / 'data' / 'ahp_zbiorcza_pkt_prng.csv'
    with open(file_name, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    lines = [line.strip() for line in lines]

    references = {}
    references[properties['reference URL']] = 'https://atlasfontium.pl/ziemie-polskie-korony/'
    qualifiers = {}
    qualifiers[properties['point in time']] = '+1600-00-00T00:00:00Z/9'

    # czy to pierwsze ładowanie danych? - wówczas bez dodatkowej weryfikacji
    first_load = True

    line_number = 0
    for line in lines:
        line_number +=1
        # if line_number < 22310:
        #     continue

        t_line = line.split('@')
        id_miejscowosci = t_line[0].strip()

        # tylko testowe
        #test_rec = ['Nowa_Karczma_prz_gdn_pmr', 'Ogony_rpn_dbr', 'Augustow_blk_pdl']
        test_rec = ['Babimost_ksc_pzn']
        if id_miejscowosci not in test_rec:
            continue

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
        simc = t_line[18].strip()
        wikidata = t_line[19].strip()
        ahp_pkt_WGS84 = t_line[20].strip()
        zbiorcza_sgh_id = t_line[21].strip()
        zbiorcza_prng = t_line[22].strip()

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
                logger.error(f'ERROR: Nie znaleziono elementu dla PRNG {zbiorcza_prng}, {element_qid}')
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
                        desc_add_en.append(f"{woj_p}")
                    else:
                        desc_add_pl.append(f"województwo {woj_p}")
                        desc_add_en.append(f"palatinate {woj_p}")

                if not nazwa_16w:
                    label_pl = 'bez nazwy'
                    label_en = 'name missing'
                    description_pl = f"osada historyczna z Atlasu Historycznego Polski [id: {id_miejscowosci}] ({', '.join(desc_add_pl)})"
                    description_en = f"historical settlement from the Historical Atlas of Poland [id: {id_miejscowosci}] ({', '.join(desc_add_en)})"
                else:
                    label_pl = label_en = nazwa_16w
                    description_pl = f"osada historyczna z Atlasu Historycznego Polski ({', '.join(desc_add_pl)})"
                    description_en = f"historical settlement from the Historical Atlas of Poland ({', '.join(desc_add_en)})"

                # testowanie unikalności pary label-description
                identyfikator = label_en + ' : ' + description_en
                if identyfikator not in unikalne:
                    unikalne.append(identyfikator)
                else:
                    logger.error(f'ERROR: Brak unikalności pary label-description, {identyfikator}')

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
                shg_references = {}
                if zbiorcza_sgh_id:
                    shg_references[properties['reference URL']] = f'http://www.slownik.ihpan.edu.pl/search.php?id={zbiorcza_sgh_id}'
                else:
                    shg_references[properties['reference URL']] = 'http://www.slownik.ihpan.edu.pl/'
                statement = create_statement_data(properties['stated as'],
                                                  f'pl:"{nazwa_slownikowa}"',
                                                  shg_references, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # # ===== stated as - nazwa wspolczesna =====
        # if nazwa_wspolczesna:
        #     if not element_qid or not has_statement(element_qid, properties['stated as'], f'pl:"{nazwa_wspolczesna}"'):
        #         if 'pl' in aliasy:
        #             aliasy['pl'].append(nazwa_wspolczesna)
        #         else:
        #             aliasy['pl'] = [nazwa_wspolczesna]
        #         statement = create_statement_data(properties['stated as'],
        #                                           f'pl:"{nazwa_wspolczesna}"',
        #                                           None, None, add_ref_dict=references, if_exists='APPEND')
        #         if statement:
        #             data.append(statement)

        # ===== stated as - nazwa odmianki =====
        if nazwa_odmianki:
            t_odmianki = nazwa_odmianki.split(",")
            for t_odm in t_odmianki:
                t_odm = t_odm.strip()
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
                    print('ERROR: nieznany charakter osady:', charakter_osady)
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

        # ===== economic object =====
        if obiekty_gospodarcze:
            if ',' in obiekty_gospodarcze:
                obiekty_gospodarcze = obiekty_gospodarcze.replace(',',';')

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
                if not element_qid or first_load or not has_statement(element_qid, properties['economic object'], obiekty[t_ob]):
                    statement = create_statement_data(properties['economic object'],
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
                    if not element_qid or first_load or not has_statement(element_qid, properties['central state functions'], funkcja_panstwowa):
                        statement = create_statement_data(properties['central state functions'],
                                                funkcja_panstwowa,
                                                None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.info(f'ERROR: nieznana funkcja państwowa {t_fun}')

        # ===== funkcje centralne kościelne (central church functions) =====
        if funkcje_centralne_koscielne:
            if ';' in funkcje_centralne_koscielne:
                funkcje_centralne_koscielne = funkcje_centralne_koscielne.replace(';', ',')
            t_funkcje = funkcje_centralne_koscielne.split(',')
            for t_fun in t_funkcje:
                t_fun = t_fun.strip()
                if t_fun in fun_centralne_koscielne:
                    funkcja_koscielna = fun_centralne_koscielne[t_fun]
                    if not element_qid or first_load or not has_statement(element_qid, properties['central church functions'], funkcja_koscielna):
                        statement = create_statement_data(properties['central church functions'],
                                                funkcja_koscielna,
                                                None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                        if statement:
                            data.append(statement)
                else:
                    logger.info(f'ERROR: nieznana funkcja kościelna {t_fun}')

        # ===== współrzędne miejscowości =====
        # np. Point (23.29833332 52.68194448)
        if ahp_pkt_WGS84:
            wgs84 = ahp_pkt_WGS84.replace('Point', '').replace('(', '').replace(')','').strip()
            tmp = wgs84.split(' ')
            longitude = tmp[0]
            latitude = tmp[1]
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
            if not element_qid or first_load or not has_statement(element_qid, properties['Wikidata ID'], q_wikidata):
                wiki_ref = {}
                wiki_ref[properties['reference URL']] = wikidata
                statement = create_statement_data(properties['Wikidata ID'],
                                                  q_wikidata, wiki_ref, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== AHP id =====
        if id_miejscowosci:
            if not element_qid or first_load or not has_statement(element_qid, properties['AHP id'], id_miejscowosci):
                statement = create_statement_data(properties['AHP id'],
                                                  id_miejscowosci, None, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== shg_id =====
        if zbiorcza_sgh_id:
            if not element_qid or first_load or not has_statement(element_qid, properties['ID SHG'], zbiorcza_sgh_id):
                statement = create_statement_data(properties['ID SHG'],
                                                  zbiorcza_sgh_id, None, None, add_ref_dict=references, if_exists='APPEND')
                if statement:
                    data.append(statement)

        # ===== located in the administrative territorial entity =====
        if powiat_p:
            parameters = [(properties['instance of'], elements['district (The Polish-Lithuanian Commonwealth (1569-1795))'])]
            ok, powiat_qid = element_search_adv(f"district {powiat_p}", 'en', parameters)
            if ok:
                if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], powiat_qid):
                    statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                  powiat_qid, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== located in the administrative territorial entity =====
        if woj_p:
            parameters = [(properties['instance of'], elements['palatinate (The Polish-Lithuanian Commonwealth (1569-1795))'])]
            ok, woj_qid = element_search_adv(f"palatinate {woj_p}", 'en', parameters)
            if ok:
                if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], woj_qid):
                    statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                  woj_qid, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== located in the administrative territorial entity =====
        if parafia:
            parameters = [(properties['instance of'], elements['parish (Roman Catholic Church)'])]
            ok, parafia_qid = element_search_adv(f"parish {parafia}", 'en', parameters)
            if ok:
                if not element_qid or first_load or not has_statement(element_qid, properties['located in the administrative territorial entity'], parafia_qid):
                    statement = create_statement_data(properties['located in the administrative territorial entity'],
                                                  parafia_qid, None, qualifier_dict=qualifiers, add_ref_dict=references, if_exists='APPEND')
                    if statement:
                        data.append(statement)

        # ===== etykiety, description =====
        if not zbiorcza_prng:
            # nowy element - osada historyczna
            wb_item = wbi_core.ItemEngine(new_item=True, data=data)
            wb_item.set_label(label_en, lang='en')
            wb_item.set_label(label_pl,lang='pl')

            wb_item.set_description(description_en, 'en')
            wb_item.set_description(description_pl, 'pl')
        else:
            # istniejący już element
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
            test = 1
            while True:
                try:
                    if not element_qid:
                        element_qid = wb_item.write(login_instance, bot_account=True, entity_type='item')
                        logger.info(f'Dodano nowy element: {label_en} / {label_pl} = {element_qid}')
                    else:
                        # tylko jak jest coś do uzupełnienia
                        if data:
                            wb_item.write(login_instance, bot_account=True, entity_type='item')
                            logger.info(f'Zaktualizowano element: {label_en} / {label_pl} = {element_qid}')

                    # zapis pomocniczego indeksu który posłuży do uzupełniania właściwości part of
                    if element_qid:
                        with open(file_index, 'a', encoding='utf-8') as fi:
                            fi.write(f'{line_number},{element_qid}')

                    break
                except MWApiError as wb_error:
                    err_code = wb_error.error_msg['error']['code']
                    message = wb_error.error_msg['error']['info']
                    logger.info(f'ERROR: {err_code}, {message}')
                    # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                    # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                    if err_code in ['assertuserfailed', 'badtoken']:
                        if test == 1:
                            logger.info('Generate edit credentials...')
                            login_instance.generate_edit_credentials()
                            test += 1
                            continue
                    sys.exit(1)
        else:
            if not element_qid:
                element_qid = 'TEST'
            logger.info(f"({line_number}) Przygotowano dodanie/uzupełnienie danych miejscowości - {label_en} / {label_pl}  = {element_qid}")
