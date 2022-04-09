""" skrypt generujący quickstatements dla postaci z PSB na podstawie
    indeksu Bożeny Bigaj
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
from postacietools import diff_date
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

VIAF_ID = {}
VIAF_BIRTH = {}
VIAF_DEATH = {}
VIAF_WYJATKI = {}
BIOGRAMY = {}
WERYFIKACJA_VIAF = {}
MALE_FEMALE_NAME = ['Maria', 'Anna']

# czy wczytywanie i zapisywanie słowników z/do pickle
LOAD_DICT = True
SAVE_DICT = True


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
        przydomek itp) oraz dodatkowo daty urodzenia i śmierci osobt jeżeli
        była wcześniej znana.
        offline - jeżeli = True to nie wyszukuje na serwerze viaf.org, korzysta
        jedynie z zapisanego wcześniej słownika z wynikami wyszukiwania
    """
    info = id_url = birthDate = deathDate = ''
    result = False

    # jeżeli osoba jest w wyjątkach to pobieramy dane ze znanego adresu
    # lub od razu NOT FOUND
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
                            if len(birthDate) == 10:
                                int_birth_date = int(birthDate[:4])
                            elif len(birthDate) == 9:
                                int_birth_date = int(birthDate[:3])
                            elif len(birthDate) == 4 and birthDate.isnumeric():
                                int_birth_date = int(birthDate)
                            elif len(birthDate) == 3 and birthDate.isnumeric():
                                int_birth_date = int(birthDate)
                            else:
                                int_birth_date = -1

                            if len(deathDate) == 10:
                                int_death_date = int(deathDate[:4])
                            elif len(deathDate) == 9:
                                int_death_date = int(deathDate[:3])
                            elif len(deathDate) == 4 and deathDate.isnumeric():
                                int_death_date = int(deathDate)
                            elif len(deathDate) == 3 and deathDate.isnumeric():
                                int_death_date = int(deathDate)
                            else:
                                int_death_date = -1

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
    output = Path('.').parent / 'out/postacie.qs'
    output_daty = Path('.').parent / 'out/postacie_daty.qs'
    postacie_pickle = Path('.').parent / 'out/postacie.pickle'
    postacie_birth_pickle = Path('.').parent / 'out/postacie_birth.pickle'
    postacie_death_pickle = Path('.').parent / 'out/postacie_death.pickle'
    biogramy_pickle = Path('.').parent / 'out/biogramy.pickle'
    postacie_viaf_html = Path('.').parent / 'out/postacie_viaf.html'

    # odmrażanie słowników
    if LOAD_DICT:
        if os.path.isfile(postacie_pickle):
            with open(postacie_pickle, 'rb') as handle:
                VIAF_ID = pickle.load(handle)

        if os.path.isfile(biogramy_pickle):
            with open(biogramy_pickle, 'rb') as handle:
                BIOGRAMY = pickle.load(handle)

        if os.path.isfile(postacie_birth_pickle):
            with open(postacie_birth_pickle, 'rb') as handle:
                VIAF_BIRTH = pickle.load(handle)

        if os.path.isfile(postacie_death_pickle):
            with open(postacie_death_pickle, 'rb') as handle:
                VIAF_DEATH = pickle.load(handle)

    with open(file_path, "r", encoding='utf-8') as f:
        indeks = f.readlines()

    if not indeks:
        print('ERROR: empty index')
        sys.exit(1)

    # identyfikatory VIAF znalezione ręcznie są pobierane z pliku xlsx
    VIAF_WYJATKI = load_wyjatki(uzup_path)

    # otwierane są dwa pliki, główny z quickstatements dla postaci, oraz uzupełniający
    # z dodatkowymi wpisami dla dat określonych jako 'somevalue', które muszą zostać
    # dodane w drugim przebiegu ze względu na błąd w QS
    with open(output, "w", encoding='utf-8') as f, open(output_daty, "w", encoding='utf-8') as fd:
        for line in indeks:
            nawias, title_stop = get_last_nawias(line)
            title = line[:title_stop].strip()

            # etykieta biogramu do wyszukania w wikibase
            etykieta = ustal_etykiete_biogramu(nawias, title)

            # czy są informacje o latach życia i aliasy?
            isYears = title.count('(') == 1 and title.count(')') == 1
            isAlias = title.count('(') == 2 and title.count(')') == 2

            # imiona i nazwiska
            start = title.find('(')
            name = title[:start].strip()
            postac = FigureName(name)

            if isAlias:
                start = title.find('(', start + 1)

            # lata życia - jeżeli we wpisie jest alias, przydomek itp. to daty
            # są w drugim nawiasie
            years = ''
            if isYears:
                stop = title.find(')', start)
                years = title[start + 1: stop].strip()
                years = years.replace('–', '-')

            # wyszukiwanie biogramu w Wikibase
            ok, q_biogram = element_search(etykieta, 'item', 'pl')
            if not ok:
                q_biogram = '{Q:biogram}'
            else:
                BIOGRAMY[name] = q_biogram

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
                                                                                   offline=True)
            else:
                viaf_ok = False

            # jeżeli VIAF ma daty to zakładam że są lepsze niż w PSB,
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

            # test czy postać nie jest już w Wikibase, wówczas wyświetla informacje
            # i pomija daną postać (na razie nie obsługujemy uaktualnień):
            ok, q_postac = element_search(postac.name_etykieta, 'item', 'en', description=years)
            if ok:
                print('ERROR:', postac.name_etykieta, 'jest już w wikibase:', q_postac)
                continue

            # zapis quickstatements
            f.write('CREATE\n')
            f.write(f'LAST\tLpl\t"{postac.name_etykieta}"\n')
            f.write(f'LAST\tLen\t"{postac.name_etykieta}"\n')
            if years:
                years = f'({years})'
                f.write(f'LAST\tDpl\t"{years}"\n')
                f.write(f'LAST\tDen\t"{years}"\n')
            if postac.imie:
                gender1 = gender_detector(postac.imie)
                ok, q_imie = element_search(postac.imie, 'item', 'pl', description=gender1)
                if not ok:
                    q_imie = '{Q:' + f'{postac.imie}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if postac.imie2:
                gender = gender_detector(postac.imie2)
                # czy to przypadek 'Maria', 'Anna'?
                if (postac.imie2 in MALE_FEMALE_NAME and gender1 == 'imię męskie'
                    and gender != gender1):
                    gender = gender1
                ok, q_imie = element_search(postac.imie2, 'item', 'pl', description=gender)
                if not ok:
                    q_imie = '{Q:' + f'{postac.imie2}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if postac.imie3:
                gender = gender_detector(postac.imie3)
                # czy to przypadek 'Maria', 'Anna' - imion zarówno meskich jak i żeńskich?
                if (postac.imie3 in MALE_FEMALE_NAME and gender1 == 'imię męskie' 
                    and gender != gender1):
                    gender = gender1
                ok, q_imie = element_search(postac.imie3, 'item', 'pl', description=gender)
                if not ok:
                    q_imie = '{Q:' + f'{postac.imie3}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if postac.imie4:
                gender = gender_detector(postac.imie4)
                # czy to przypadek 'Maria', 'Anna'?
                if (postac.imie4 in MALE_FEMALE_NAME and gender1 == 'imię męskie'
                    and gender != gender1):
                    gender = gender1
                ok, q_imie = element_search(postac.imie4, 'item', 'pl', description=gender)
                if not ok:
                    q_imie = '{Q:' + f'{postac.imie4}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if postac.nazwisko:
                ok, q_nazwisko = element_search(postac.nazwisko, 'item', 'en', description='family name')
                if not ok:
                    q_nazwisko = '{Q:' + f'{postac.nazwisko}' + '}'
                f.write(f'LAST\t{P_NAZWISKO}\t{q_nazwisko}\n')
            if postac.nazwisko2:
                ok, q_nazwisko = element_search(postac.nazwisko2, 'item', 'en', description='family name')
                if not ok:
                    q_nazwisko = '{Q:' + f'{postac.nazwisko2}' + '}'
                f.write(f'LAST\t{P_NAZWISKO}\t{q_nazwisko}\n')

            # imię i nazwisko przy urodzeniu (głównie dla zakoników/zakonnic)
            if postac.birth_name:
                f.write(f'LAST\t{P_BIRTH_NAME}\tpl:"{postac.birth_name}"')

            f.write(f'LAST\t{P_INSTANCE_OF}\t{Q_HUMAN}\n')

            # daty życia - z obsługą kwalifikatorów
            if date_of_1 and date_of_1.somevalue:
                #fd.write(date_of_1.prepare_qs('Q:'+ name_etykieta + '|' + years))
                f.write(date_of_1.prepare_qs('LAST'))
            elif date_of_1 and not date_of_1.somevalue:
                f.write(date_of_1.prepare_qs())

            if date_of_2 and date_of_2.somevalue:
                #fd.write(date_of_2.prepare_qs('Q:'+ name_etykieta + '|' + years))
                f.write(date_of_2.prepare_qs('LAST'))
            elif date_of_2 and not date_of_2.somevalue:
                f.write(date_of_2.prepare_qs())

            # opisany w źródle
            f.write(f'LAST\t{P_DESCRIBED_BY_SOURCE}\t{q_biogram}\n')
            if viaf_ok and viaf_id and viaf_url:
                # wystarczy samo id, reference url jest już zbędny
                f.write(f'LAST\t{P_VIAF}\t"{viaf_id}"\n')
                WERYFIKACJA_VIAF[name] = viaf_url

            print('Przetworzono: ', postac.name_etykieta)

    # zamrażanie słownika identyfikatów VIAF_ID
    if SAVE_DICT:
        with open(biogramy_pickle, 'wb') as handle:
            pickle.dump(BIOGRAMY, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_pickle, 'wb') as handle:
            pickle.dump(VIAF_ID, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_birth_pickle, 'wb') as handle:
            pickle.dump(VIAF_BIRTH, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(postacie_death_pickle, 'wb') as handle:
            pickle.dump(VIAF_DEATH, handle, protocol=pickle.HIGHEST_PROTOCOL)

    # zapis wyszukiwań VIAF w HTML dla łatwiejszej weryfikacji
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
