""" skrypt generujący quickstatements dla postaci z PSB na podstawie
    indeksu Bożeny Bigaj
"""

import sys
import re
import pickle
import os
from pathlib import Path
from time import sleep
from urllib.parse import quote
import requests
from wikibaseintegrator.wbi_config import config as wbi_config
from autorzy import VIAF_DEATH, WERYFIKACJA_VIAF
from wikidariahtools import format_date, text_clear, \
                            get_last_nawias, short_names_in_autor
from postacietools import get_name
#from wikidariahtools import element_search


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
P_DATE_OF_BIRTH = 'P7'
P_DATE_OF_DEATH = 'P8'
P_DESCRIBED_BY_SOURCE = 'P17'

BIOGRAMY = {}
VIAF_ID = {}
VIAF_BIRTH = {}
VIAF_DEATH = {}
WERYFIKACJA_VIAF = {}

# czy wczytywanie i zapisywanie słowników z/do pickle
LOAD_DICT = True
SAVE_DICT = False


def viaf_search(person_name: str, s_birth: str = '', s_death: str = '',
                offline: bool = False) -> tuple:
    """ szukanie identyfikatora VIAF """

    info = id_url = birthDate = deathDate = ''
    result = False

    # jeżeli identyfikator jest już znany to nie ma potrzeby szukania
    # przez api
    if person_name in VIAF_ID:
        info = VIAF_ID[person_name]
        match = re.search('\d{3,25}', info)
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
    sleep(0.05)

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
        print(f'Name: {name} ERROR {e_info}')

    if len(identyfikatory) == 1:
        return True, identyfikatory[0], urls[identyfikatory[0]], birthDate, deathDate

    return False, "NOT FOUND", '', '', ''


def ustal_etykiete(value: str, title_value: str) -> str:
    """ ustala etykiete biogramu """
    l_nawias = value.split(",")
    if len(l_nawias) != 4:
        print(f'ERROR: {l_nawias}')
        sys.exit(1)
    autor = text_clear(l_nawias[0])
    autor_in_title = short_names_in_autor(autor)
    tom = text_clear(l_nawias[1])
    tom = tom.replace("t.","").strip()
    strony = text_clear(l_nawias[3])

    if ";" in autor_in_title:
        autor_in_title = autor_in_title.replace(';', ',')

    return f"{autor_in_title}, {title_value}, w: PSB {tom}, {strony}"


def date_birth_death(value: str) -> tuple:
    """ dateBirthDeath """
    date_of_birth = date_of_death = ""
    if value != "":
        pattern = r'\d{4}'
        if '-' in value:
            tmp = value.split('-')
            match = re.search(pattern, tmp[0].strip())
            if match:
                date_of_birth = match.group()
            match = re.search(pattern, tmp[1].strip())
            if match:
                date_of_death = match.group()
        else:
            if 'zm.' in value or 'um.' in value:
                match = re.search(pattern, value)
                if match:
                    date_of_death = match.group()
            elif 'ur.' in value:
                match = re.search(pattern, value)
                if match:
                    date_of_birth = match.group()

    return date_of_birth, date_of_death


# def get_name(value: str) -> tuple:
#     """ get_name """
#     roman = ['I', 'II', 'III', 'IV', 'V', 'VI',
#              'VII', 'VIII', 'IX', 'X', 'XI', 'XII', 'XIII', 'XIV']
    
#     p_imie = p_imie2 = p_nazwisko = ''

#     not_forname = ['Judaeus', 'Bohemus', 'Hohenzollern', 'Wszewołodowicz',
#                    'Caucina', 'Courtenay', 'Vasseur', 'Gallo', 'Chrobry',
#                    'Mieszkowic', 'Szczodry', 'Krzywousty', 'Kędzierzawy', 'Wstydliwy',
#                    'Wysoki', 'Łysy', 'Pobożny', 'Hojny', 'Sforza', 'Radziwiłłówna', 
#                    'Rachtamowicz', 'Michajłowicz', 'Abrahamowic', 'Pesach-Libman', 
#                    'Sprawiedliwy', 'Odnowiciel', 'Oleksowicz', 'Przecławski', 
#                    'Namysłowski', 'Mniszchówna', 'Bohuszewicz', 'Aleksandrowicz', 
#                    'Aleksiejewna', 'Andegaweńska', 'Andrejewicz', 'Andrysowic']

#     if 'młodszy' in value:
#         value = value.replace("młodszy", "").strip()

#     if 'starszy' in value:
#         value = value.replace("starszy", "").strip()

#     if 'Młodszy' in value:
#         value = value.replace("Młodszy", "").strip()

#     if 'Starszy' in value:
#         value = value.replace("Starszy", "").strip()

#     tmp = value.strip().split(" ")
#     for i in range(0, len(tmp)):
#         tmp[i] = tmp[i].strip()
#         if tmp[i] in roman:
#             tmp[i] = ''

#     for item in tmp:
#         if item.strip() == '':
#             tmp.remove(item)

#     if len(tmp) == 1:
#         # czy to imię czy nazwisko? Słownik typowych imion a jeżeli spoza to nazwisko?
#         p_imie = tmp[0].strip()
#     elif len(tmp) == 2:
#         if tmp[0][0].isupper() and tmp[1][0].isupper():
#             if tmp[1].strip() in not_forname:
#                 p_nazwisko = tmp[1].strip()
#                 p_imie = tmp[0].strip()
#             else:
#                 p_nazwisko = tmp[0].strip()
#                 p_imie = tmp[1].strip()
#     elif len(tmp) == 3:
#         if tmp[0][0].isupper() and tmp[1][0].isupper() and tmp[2][0].isupper():
#             if tmp[2].strip() in not_forname:
#                 p_nazwisko = tmp[2].strip()
#                 p_imie = tmp[0].strip()
#                 if tmp[1].strip() not in not_forname:
#                     p_imie2 = tmp[1].strip()
#             else:
#                 p_nazwisko = tmp[0].strip()
#                 p_imie = tmp[1].strip()
#                 p_imie2 = tmp[2].strip()
#         else:
#             if ' z ' in value:
#                 p_imie = tmp[0].strip()
#     else:
#         if ' de ' in value:
#             p_imie = tmp[-1].strip()
#             p_nazwisko = ' '.join(tmp[:-1])

#     return p_nazwisko, p_imie, p_imie2


if __name__ == "__main__":
    file_path = Path('.').parent / 'data/lista_hasel_PSB_2020.txt'
    output = Path('.').parent / 'out/postacie.qs'
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

    with open(output, "w", encoding='utf-8') as f:
        licznik = 0
        for line in indeks:
            licznik += 1
            nawias, title_stop = get_last_nawias(line)
            title = line[:title_stop].strip()
            # etykieta biogramu do wyszukania w wikibase
            etykieta = ustal_etykiete(nawias, title)

            isYears = title.count('(') == 1 and title.count(')') == 1
            isAlias = title.count('(') == 2 and title.count(')') == 2

            name = years = author = psb = dateOfBirth = dateOfDeath = ''
            imie = imie2 = imie3 = imie4 = nazwisko = nazwisko2 = ''
            stop = 0

            # lata życia
            # jeżeli we wpisie jest alias, przydomek itp. to daty są w drugim nawiasie
            start = title.find('(')
            name = title[:start].strip()
            print(name)
            nazwisko, imie, imie2, nazwisko2, imie3, imie4 = get_name(name)

            if isAlias:
                print("ALIAS: ", title)
                start = title.find('(', start + 1)

            if isYears:
                stop = title.find(')', start)
                years = title[start + 1: stop].strip()
                years = years.replace('–', '-')

            #ok, q_biogram = element_search(etykieta, 'item', 'pl')
            ok = False # na razie nie szukamy
            if not ok:
                q_biogram = '{Q:biogram}'
            else:
                BIOGRAMY[name] = q_biogram

            dateB, dateD = date_birth_death(years)

            # jeżeli znamy tylko imię postaci odpytywanie VIAF nie ma sensu (?)
            viaf_ok = False
            viaf_id = viaf_url = viaf_date_b = viaf_date_d = ''
            if ' ' in name:
                viaf_ok, viaf_id, viaf_url, viaf_date_b, viaf_date_d = viaf_search(name,
                                                                                   s_birth=dateB,
                                                                                   s_death=dateD,
                                                                                   offline=True)

            if viaf_ok and viaf_date_b and viaf_date_b != dateB:
                dateB = viaf_date_b
            if viaf_ok and viaf_date_d and viaf_date_d != dateD:
                dateD = viaf_date_d

            dateB = format_date(dateB)
            dateD = format_date(dateD)

            # zapis quickstatements
            f.write('CREATE\n')
            f.write(f'LAST\tLpl\t"{name}"\n')
            f.write(f'LAST\tLen\t"{name}"\n')
            if years:
                f.write(f'LAST\tDpl\t"({years})"\n')
                f.write(f'LAST\tDen\t"({years})"\n')
            if imie:
                # ok, q_imie = element_search(imie, 'item', 'en', description='given name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_imie = '{Q:' + f'{imie}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if imie2:
                # ok, q_imie = element_search(imie2, 'item', 'en', description='given name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_imie = '{Q:' + f'{imie2}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if imie3:
                # ok, q_imie = element_search(imie3, 'item', 'en', description='given name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_imie = '{Q:' + f'{imie3}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if imie4:
                # ok, q_imie = element_search(imie4, 'item', 'en', description='given name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_imie = '{Q:' + f'{imie4}' + '}'
                f.write(f'LAST\t{P_IMIE}\t{q_imie}\n')
            if nazwisko:
                # ok, q_nazwisko = element_search(nazwisko, 'item', 'en', description='family name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_nazwisko = '{Q:' + f'{nazwisko}' + '}'
                f.write(f'LAST\t{P_NAZWISKO}\t{q_nazwisko}\n')
            if nazwisko2:
                # ok, q_nazwisko = element_search(nazwisko2, 'item', 'en', description='family name')
                ok = False # na razie nie szukamy
                if not ok:
                    q_nazwisko = '{Q:' + f'{nazwisko2}' + '}'
                f.write(f'LAST\t{P_NAZWISKO}\t{q_nazwisko}\n')

            f.write(f'LAST\t{P_INSTANCE_OF}\t{Q_HUMAN}\n')
            if dateB:
                f.write(f'LAST\t{P_DATE_OF_BIRTH}\t{dateB}\n')
            if dateD:
                f.write(f'LAST\t{P_DATE_OF_DEATH}\t{dateD}\n')
            f.write(f'LAST\t{P_DESCRIBED_BY_SOURCE}\t{q_biogram}\n')
            if viaf_ok and viaf_id and viaf_url:
                f.write(f'LAST\t{P_VIAF}\t"{viaf_id}"\t{P_REFERENCE_URL}\t"{viaf_url}"\n')
                WERYFIKACJA_VIAF[name] = viaf_url

            #if licznik >= 100:
            #    break

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
