""" skrypt generujący quickstatements dla postaci z PSB na podstawie
    indeksu biogramów postaci z PSB (tzw. indeksu Bożeny Bigaj)
"""

import sys
import pickle
import os
import re
from pathlib import Path
from time import sleep
from urllib.parse import quote
from wikibaseintegrator.wbi_config import config as wbi_config
import requests
from postacietools import DateBDF, FigureName, ustal_etykiete_biogramu, load_wyjatki
from postacietools import diff_date, get_years
from wikidariahtools import element_search, gender_detector
from wikidariahtools import get_last_nawias


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# stałe
P_INSTANCE_OF = 'P47'
Q_HUMAN = 'Q32'
P_IMIE = 'P184'
P_NAZWISKO = 'P183'
P_VIAF = 'P79'
P_REFERENCE_URL = 'S182'
P_BIRTH_NAME = 'P63'
P_DESCRIBED_BY_SOURCE = 'P17'
P_RELIGIOUS_NAME = 'P191'

VIAF_ID = {}
VIAF_BIRTH = {}
VIAF_DEATH = {}
VIAF_WYJATKI = {}
IMIONA = {}
NAZWISKA = {}
BIOGRAMY = {}
POSTACIE = {}
WERYFIKACJA_VIAF = {}
MALE_FEMALE_NAME = ['Maria', 'Anna', 'Róża', 'Magdalena', 'Zofia']
LISTA_IMION = []
LISTA_NAZWISK = []

# czy wczytywanie i zapisywanie słowników z/do pickle
LOAD_DICT = True
SAVE_DICT = True
OFFLINE = True
OFFLINE_VIAF = True


def biogram_qid(value: str, offline: bool=False) -> str:
    """ wyszukuje biogram w wikibase dla podanej etykiety biogramu

        Parametry:
            value - etykieta biogramu
            offline - jeżeli True to nie wyszukuje w Wikibase, jedynie w lokalnym
                      słowniku

        Zwraca:
            Q biogramu lub wartość '{Q:biogram} jeżeli nie znaleziono'
    """

    # sprawdzenie w słowniku
    if value in BIOGRAMY:
        return BIOGRAMY[value]

    # jeżeli brak w słowniku wyszukiwanie biogramu w Wikibase o ile paramtetr
    # offline nie jest == True
    if offline:
        return '{Q:biogram}'

    znaleziono, qid = element_search(value, 'item', 'pl')
    if not znaleziono:
        qid = '{Q:biogram}'
        print('ERROR: nie znaleziono biogramu: ', value)
    else:
        BIOGRAMY[value] = qid

    return qid


def given_name_qid(value: str, gender_first:str = '', offline: bool=False) -> str:
    """ wyszukuje Q w wikibase dla podanego imienia, najpierw sprawdzając słownik,
        jeżeli brak w słowniku szuka online w wikibase i w razie powidzenia
        uzupełnia słownik

        Parametry:
            value - poszukiwane imie
            gender_first - opcjonalnie rodzaj pierwszego imienia postaci do obsługi
                           przypadków typu Maria, Anna jako imion męskich
            offline - jeżeli True to nie wyszukuje w Wikibase, jedynie w lokalnym
                      słowniku

        Zwraca:
            identyfikator Q w wikibase (str)
    """
    gender_name = gender_detector(value)
    value_f = value
    if gender_first == 'imię męskie' and gender_name != gender_first:
        value_f = value + ':male'
        gender_name = gender_first
    if value_f in IMIONA:
        return IMIONA[value_f]

    if offline:
        #return '{Q:' + f'{value}' + '}'
        return ''

    znaleziono, qid = element_search(value, 'item', 'pl', description=gender_name)
    if not znaleziono:
        # qid = '{Q:' + f'{value}' + '}'
        qid = ''
    else:
        IMIONA[value_f] = qid

    return qid


def family_name_qid(value: str, offline: bool=False) -> str:
    """ wyszukuje Q w wkibase dla podanego nazwiska, najpierw sprawdzając słownik,
        jeżeli brak w słowniku szuka online w wikibase i w razie powidzenia
        uzupełnia słownik

        Parametry:
            value - poszukiwane nazwisko
            offline - jeżeli True to nie wyszukuje w Wikibase, jedynie w lokalnym
                      słowniku


        Zwraca:
            identyfikator Q w wikibase (str)
    """
    if value in NAZWISKA:
        return NAZWISKA[value]

    if offline:
        return ''

    znaleziono, qid = element_search(value, 'item', 'en', description='family name')
    if not znaleziono:
        qid = ''
    else:
        NAZWISKA[value] = qid

    return qid


def postac_qid(value: str, description: str='', offline=False) -> str:
    """ wyszukuje Q dla postaci w Wikibase/słowniku

        Parametry:
            value - etykieta postaci
            description - opis dla postaci
            offline - jeżeli True to nie wyszukuje w Wikibase, jedynie w lokalnym
                      słowniku

        Zwraca:
            identyfikator Q w wikibase (str) lub 'LAST' (dla nowych elementów)
    """
    postac_key = f'{value}|{description}'
    if postac_key in POSTACIE:
        return POSTACIE[postac_key]

    if offline:
        return 'LAST'

    znaleziono, qid = element_search(value, 'item', 'pl', description=description)
    if znaleziono:
        print('INFO:', value, 'jest już w wikibase:', qid)
        POSTACIE[postac_key] = qid
        return qid

    return 'LAST'


def get_viaf_data(v_url: str) -> tuple:
    """ get_viaf_data  - pobiera dane ze znanego adresu identyfikatora
        viaf dla osoby
        v_url - adres VIAF id dla osoby
    """
    v_id = v_birth = v_death = ''
    if not v_url.endswith('/'):
        v_url += '/'
    response = requests.get(v_url + 'viaf.json')
    result = response.json()
    if 'viafID' in result:
        v_id = result['viafID']
    if 'birthDate' in result:
        v_birth = result['birthDate']
    if 'deathDate' in result:
        v_death = result['deathDate']

    return v_id, v_birth, v_death


def viaf_search(person_name: str, s_birth: str = '', s_death: str = '',
                offline: bool = False) -> tuple:
    """ szukanie identyfikatora VIAF na podstawie nazwy osoby (imię nazwisko
        przydomek itp) oraz dodatkowo daty urodzenia i śmierci osoby jeżeli
        była wcześniej znana.
        offline - jeżeli = True to nie wyszukuje na serwerze viaf.org, korzysta
        jedynie z zapisanego wcześniej słownika z wynikami wyszukiwania
    """
    info = id_url = birthDate = deathDate = ''
    result = False

    # jeżeli osoba jest w wyjątkach to pobiera dane ze znanego adresu
    # lub gdy w wyjątkach mamy wpis BRAK to od razu zwraca NOT FOUND
    if person_name in VIAF_WYJATKI:
        if VIAF_WYJATKI[person_name].strip() == 'BRAK':
            return False, "NOT_FOUND", '', '', ''

        info, birthDate, deathDate = get_viaf_data(VIAF_WYJATKI[person_name])
        id_url = VIAF_WYJATKI[person_name]
        VIAF_ID[person_name] = info
        if birthDate:
            VIAF_BIRTH[person_name] = birthDate
        if deathDate:
            VIAF_DEATH[person_name] = deathDate

        return True, info, id_url, birthDate, deathDate

    # jeżeli identyfikator jest już znany to nie ma potrzeby szukania
    # przez api
    if person_name in VIAF_ID:
        info = VIAF_ID[person_name]
        if 'http' in info:
            match = re.search(r'\d{3,25}', info)
            if match:
                info = match.group()
        id_url = f"http://viaf.org/viaf/{info}/"

        if person_name in VIAF_BIRTH:
            birthDate = VIAF_BIRTH[person_name]

        if person_name in VIAF_DEATH:
            deathDate = VIAF_DEATH[person_name]

        return True, info, id_url, birthDate, deathDate

    # jeżeli nie chcemy wyszukiwać online w viaf.org
    if offline:
        return False, "NOT FOUND", '', '', ''

    identyfikatory = []
    urls = {}
    base = 'https://viaf.org/viaf/search'
    format_type = 'application/json'
    search_person = quote(f'"{person_name}"')
    adres = f'{base}?query=local.personalNames+=+{search_person}'
    adres+= f'&local.sources+=+"plwabn"&sortKeys=holdingscount&httpAccept={format_type}'

    # mały odstęp między poszukiwaniami
    sleep(0.03)

    try:
        response = requests.get(adres)
        result = response.json()
        if 'records' in result['searchRetrieveResponse']:
            rekordy = result['searchRetrieveResponse']['records']

            for rekord in rekordy:
                v_id = rekord['record']['recordData']['viafID']
                if v_id:
                    url = rekord['record']['recordData']['Document']['@about']
                    if isinstance(rekord['record']['recordData']['mainHeadings']['data'], list):
                        label = rekord['record']['recordData']['mainHeadings']['data'][0]['text']
                    elif isinstance(rekord['record']['recordData']['mainHeadings']['data'], dict):
                        label = rekord['record']['recordData']['mainHeadings']['data']['text']

                    if label:
                        label = label.replace(",", "")
                        l_name = person_name.split(" ")
                        find_items = True

                        for item_name in l_name:
                            if len(item_name) > 2 and not item_name in label:
                                find_items = False
                                break

                        if find_items:
                            if 'birthDate' in rekord['record']['recordData']:
                                birthDate = rekord['record']['recordData']['birthDate']

                            if 'deathDate' in rekord['record']['recordData']:
                                deathDate = rekord['record']['recordData']['deathDate']

                            # jeżeli mamy podane daty w viaf i w indeksie to mogą się różnić
                            # o maksymalnie 3 lata
                            int_birth_date = -1
                            if '-' in birthDate:
                                t_tmp = birthDate.split('-')
                                if t_tmp[0].isnumeric():
                                    int_birth_date = int(t_tmp[0])
                            elif birthDate.isnumeric():
                                int_birth_date = int(birthDate)

                            int_death_date = -1
                            if '-' in deathDate:
                                t_tmp = deathDate.split('-')
                                if t_tmp[0].isnumeric():
                                    int_death_date = int(t_tmp[0])
                            elif deathDate.isnumeric():
                                int_death_date = int(deathDate)

                            if s_birth and int_birth_date > 0:
                                y_diff = abs(int(s_birth) - int_birth_date)
                                if not birthDate.startswith(s_birth) and y_diff > 3:
                                    continue

                            if s_death and int_death_date > 0:
                                y_diff = abs(int(s_death) - int_death_date)
                                if not deathDate.startswith(s_death) and y_diff > 3:
                                    continue

                            identyfikatory.append(v_id)
                            urls[v_id] = url

                            VIAF_ID[person_name] = v_id  # zapis identyfikatora w słowniku

                            if birthDate:
                                VIAF_BIRTH[person_name] = birthDate
                            if deathDate:
                                VIAF_DEATH[person_name] = deathDate

                            break

    except requests.exceptions.RequestException as e_info:
        print(f'Name: {person_name} ERROR {e_info}')

    if len(identyfikatory) == 1:
        return True, identyfikatory[0], urls[identyfikatory[0]], birthDate, deathDate

    return False, "NOT FOUND", '', '', ''


if __name__ == "__main__":
    file_path = Path('.').parent / 'data/lista_hasel_PSB_2020.txt'
    uzup_path = Path('.').parent / 'data/postacie_viaf_uzup.xlsx'
    lista_imion_path = Path('.').parent / 'data/imiona_all.txt'
    lista_nazwisk_path = Path('.').parent / 'data/nazwiska_all.txt'
    output = Path('.').parent / 'out/postacie.qs'
    output_daty = Path('.').parent / 'out/postacie_daty.qs'
    output_aktualizacje = Path('.').parent / 'out/postacie_aktualizacje.qs'

    postacie_pickle = Path('.').parent / 'out/postacie.pickle'
    postacie_qid_pickle = Path('.').parent / 'out/postacie_qid.pickle'
    postacie_birth_pickle = Path('.').parent / 'out/postacie_birth.pickle'
    postacie_death_pickle = Path('.').parent / 'out/postacie_death.pickle'
    biogramy_pickle = Path('.').parent / 'out/biogramy.pickle'
    postacie_viaf_html = Path('.').parent / 'out/postacie_viaf.html'
    imiona_pickle = Path('.').parent / 'out/postacie_imiona.pickle'
    nazwiska_pickle = Path('.').parent / 'out/postacie_nazwiska.pickle'

    # odmrażanie słowników
    if LOAD_DICT:
        if os.path.isfile(postacie_pickle):
            with open(postacie_pickle, 'rb') as handle:
                VIAF_ID = pickle.load(handle)

        if os.path.isfile(postacie_qid_pickle):
            with open(postacie_qid_pickle, 'rb') as handle:
                POSTACIE = pickle.load(handle)

        if os.path.isfile(biogramy_pickle):
            with open(biogramy_pickle, 'rb') as handle:
                BIOGRAMY = pickle.load(handle)

        if os.path.isfile(postacie_birth_pickle):
            with open(postacie_birth_pickle, 'rb') as handle:
                VIAF_BIRTH = pickle.load(handle)

        if os.path.isfile(postacie_death_pickle):
            with open(postacie_death_pickle, 'rb') as handle:
                VIAF_DEATH = pickle.load(handle)

        if os.path.isfile(imiona_pickle):
            with open(imiona_pickle, 'rb') as handle:
                IMIONA = pickle.load(handle)

        if os.path.isfile(nazwiska_pickle):
            with open(nazwiska_pickle, 'rb') as handle:
                NAZWISKA = pickle.load(handle)

    # wczytywanie zawartości indeksu biogramów PSB
    with open(file_path, "r", encoding='utf-8') as f:
        indeks = f.readlines()

    if not indeks:
        print('ERROR: empty index')
        sys.exit(1)

    # identyfikatory VIAF znalezione ręcznie są pobierane z pliku xlsx
    VIAF_WYJATKI = load_wyjatki(uzup_path)

    # wczytywanie list 'legalnych' (zweryfikowanych) imion i nazwisk
    with open(lista_imion_path, "r", encoding='utf-8') as f:
        lines = f.readlines()
        LISTA_IMION = [imie.strip() for imie in lines]

    with open(lista_nazwisk_path, "r", encoding='utf-8') as f:
        lines = f.readlines()
        LISTA_NAZWISK = [nazwisko.strip() for nazwisko in lines]

    # otwierane są trzy pliki, główny z quickstatements dla nowych postaci, uzupełniający
    # z dodatkowymi wpisami dla dat określonych jako 'somevalue', które muszą zostać
    # dodane w drugim przebiegu ze względu na błąd w QS, trzeci z danymi aktualizacyjnymi
    # dla postaci już wprowadzonych do Wikibase
    with open(output, "w", encoding='utf-8') as f, open(output_daty, "w", encoding='utf-8') as fd, open(output_aktualizacje, "w", encoding='utf-8') as fa:
        for line in indeks:
            nawias, title_stop = get_last_nawias(line)
            title = line[:title_stop].strip()

            # etykieta biogramu do wyszukania w wikibase
            etykieta = ustal_etykiete_biogramu(nawias, title)

            # informacja o latach życia postaci, dacie urodzin, śmierci, okresie
            # aktywności
            years = get_years(title)

            # imiona i nazwiska
            name = title.replace(years, '').replace('()','').strip()
            postac = FigureName(name)

            # wyszukiwanie biogramu w słowniku lub Wikibase
            q_biogram = biogram_qid(etykieta, offline=OFFLINE)

            # daty urodzenia i śmierci
            separator = ',' if ',' in years else '-'
            date_of_1 = date_of_2 = None
            # jeżeli zakres dat
            if separator in years:
                tmp = years.split(separator)
                date_of_1 = DateBDF(tmp[0].strip(), 'B')
                date_of_2 = DateBDF(tmp[1].strip(), 'D')
            # jeżeli tylko jedna z dat lub ogólny opis np. XVII wiek
            else:
                if years:
                    date_of_1 = DateBDF(years, '')

            p_birth = p_death = ''
            if date_of_1 and date_of_1.type == 'B':
                p_birth = date_of_1.date
            if date_of_1 and date_of_1.type == 'D':
                p_death = date_of_1.date
            if date_of_2 and date_of_2.type == 'D':
                p_death = date_of_2.date

            # jeżeli znamy tylko imię postaci odpytywanie VIAF nie ma sensu (?)
            if ' ' in name:
                viaf_ok, viaf_id, viaf_url, viaf_date_b, viaf_date_d = viaf_search(name,
                                                                        s_birth=p_birth,
                                                                        s_death=p_death,
                                                                        offline=OFFLINE_VIAF)
            else:
                viaf_ok = False

            # jeżeli rekord VIAF ma podane daty to zakładam, że są lepsze niż w PSB,
            # tylko jeżeli dat nie ma w VIAF lub są identyczne jak w PSB
            # to obsługa dat z PSB, z niepewnościami włącznie typu:
            # 'before', 'after' , 'about', 'or', 'between', 'roman', 'turn'
            # wyjątkiem jest sytuacja gdy mamy daty roczne z PSB i viaf, ale
            # różnią się o ponad 3 lata, co może wskazywać na nieprawidłową
            # identyfikację w viaf.org
            if viaf_ok and viaf_date_b and date_of_1:
                if (date_of_1.type == 'B' and date_of_1.date != viaf_date_b
                    and diff_date(date_of_1.date, viaf_date_b)):
                    date_of_1.date = viaf_date_b
            if viaf_ok and viaf_date_d and date_of_1:
                if (date_of_1.type == 'D' and date_of_1.date != viaf_date_d
                    and diff_date(date_of_1.date, viaf_date_d)):
                    date_of_1.date = viaf_date_d
            if viaf_ok and viaf_date_d and date_of_2:
                if (date_of_2.type == 'D' and date_of_2.date != viaf_date_d
                    and diff_date(date_of_2.date, viaf_date_d)):
                    date_of_2.date = viaf_date_d

            # test czy postać nie jest już w Wikibase, wówczas aktualizacja danych
            p_qid = postac_qid(postac.name_etykieta, description='('+years+')', offline=OFFLINE)

            # zapis do osobnego pliku dla aktualizacji
            if p_qid == 'LAST':
                w = f
            else:
                w = fa

            # zapis quickstatements
            if p_qid == 'LAST':
                w.write('CREATE\n')
            w.write(f'{p_qid}\tLpl\t"{postac.name_etykieta}"\n')
            w.write(f'{p_qid}\tLen\t"{postac.name_etykieta}"\n')
            if years:
                years = f'({years})'
                w.write(f'{p_qid}\tDpl\t"{years}"\n')
                w.write(f'{p_qid}\tDen\t"{years}"\n')
            if postac.imie and postac.imie in LISTA_IMION:
                # ustalenie rodzaju imienia (m/ż)
                gender1 = gender_detector(postac.imie)
                # poszukiwanie imienia w Wikibase lub w słowniku
                q_imie = given_name_qid(postac.imie, gender_first='', offline=OFFLINE)
                if q_imie:
                    w.write(f'{p_qid}\t{P_IMIE}\t{q_imie}\n')
            if postac.imie2 and postac.imie2 in LISTA_IMION:
                q_imie = given_name_qid(postac.imie2, gender_first=gender1, offline=OFFLINE)
                if q_imie:
                    w.write(f'{p_qid}\t{P_IMIE}\t{q_imie}\n')
            if postac.imie3 and postac.imie3 in LISTA_IMION:
                q_imie = given_name_qid(postac.imie3, gender_first=gender1, offline=OFFLINE)
                if q_imie:
                    w.write(f'{p_qid}\t{P_IMIE}\t{q_imie}\n')
            if postac.imie4 and postac.imie4 in LISTA_IMION:
                q_imie = given_name_qid(postac.imie4, gender_first=gender1, offline=OFFLINE)
                if q_imie:
                    w.write(f'{p_qid}\t{P_IMIE}\t{q_imie}\n')
            if postac.nazwisko and postac.nazwisko in LISTA_NAZWISK:
                # poszukiwanie nazwiska w Wikibase lub w słowniku
                q_nazwisko = family_name_qid(postac.nazwisko, offline=OFFLINE)
                if q_nazwisko:
                    w.write(f'{p_qid}\t{P_NAZWISKO}\t{q_nazwisko}\n')
            if postac.nazwisko2 and postac.nazwisko2 in LISTA_NAZWISK:
                q_nazwisko = family_name_qid(postac.nazwisko2, offline=OFFLINE)
                if q_nazwisko:
                    w.write(f'{p_qid}\t{P_NAZWISKO}\t{q_nazwisko}\n')

            # imię i nazwisko przy urodzeniu (głównie dla zakoników/zakonnic)
            if postac.birth_name:
                w.write(f'{p_qid}\t{P_BIRTH_NAME}\tpl:"{postac.birth_name}"\n')
            # imiona we wspólnocie religijniej
            if postac.zakon_names:
                for z_name in postac.zakon_names:
                    w.write(f'{p_qid}\t{P_RELIGIOUS_NAME}\tpl:"{z_name}"\n')

            w.write(f'{p_qid}\t{P_INSTANCE_OF}\t{Q_HUMAN}\n')

            # daty życia - z obsługą kwalifikatorów, daty nieprecyzyjne zapisywane w osobnym
            # pliku ze względu na błąd w QS, muszą być importowane po wprowadzeniu postaci
            # do wikibase
            if date_of_1 and date_of_1.somevalue:
                fd.write(date_of_1.prepare_qs('Q:'+ postac.name_etykieta + '|' + years))
            elif date_of_1 and not date_of_1.somevalue:
                w.write(date_of_1.prepare_qs(p_qid))

            if date_of_2 and date_of_2.somevalue:
                fd.write(date_of_2.prepare_qs('Q:'+ postac.name_etykieta + '|' + years))
            elif date_of_2 and not date_of_2.somevalue:
                w.write(date_of_2.prepare_qs(p_qid))

            # opisany w źródle
            w.write(f'{p_qid}\t{P_DESCRIBED_BY_SOURCE}\t{q_biogram}\n')
            # zapis VIAF, adres url obecnie jest pomijany, właściwość w wikibase
            # tworzy adres url dynamicznie
            if viaf_ok and viaf_id and viaf_url:
                w.write(f'{p_qid}\t{P_VIAF}\t"{viaf_id}"\n')
                WERYFIKACJA_VIAF[name] = viaf_url

            print('Przetworzono: ', postac.name_etykieta)

    # zamrażanie słownika identyfikatów VIAF_ID
    if SAVE_DICT:
        with open(biogramy_pickle, 'wb') as handle:
            pickle.dump(BIOGRAMY, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_pickle, 'wb') as handle:
            pickle.dump(VIAF_ID, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_qid_pickle, 'wb') as handle:
            pickle.dump(POSTACIE, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_birth_pickle, 'wb') as handle:
            pickle.dump(VIAF_BIRTH, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_death_pickle, 'wb') as handle:
            pickle.dump(VIAF_DEATH, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(imiona_pickle, 'wb') as handle:
            pickle.dump(IMIONA, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(nazwiska_pickle, 'wb') as handle:
            pickle.dump(NAZWISKA, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # zapis wyszukiwań VIAF w HTML dla łatwiejszej weryfikacji poprawności id
    with open(postacie_viaf_html, "w", encoding='utf-8') as h:
        h.write('<html>\n')
        h.write('<head>\n')
        h.write('<meta charset="utf-8">\n')
        h.write('<title>Weryfikacja VIAF dla postaci PSB</title>\n')
        h.write('</head>\n')
        h.write('<body>\n')
        h.write('<h2>Weryfikacja VIAF dla postaci PSB</h2>\n')
        h.write('<table>\n')
        for key, val in WERYFIKACJA_VIAF.items():
            h.write(f'<tr><td>{key}</td><td><a href="{val}">{val}</td></tr>\n')
        h.write('</table>\n')
        h.write('</body>\n')
        h.write('</html>\n')
