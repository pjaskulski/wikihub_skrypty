""" funkcje pomocniczne do obsługi skryptów wikibase """

import re
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikibaseintegrator.wbi_functions import search_entities
from wikibaseintegrator.wbi_functions import execute_sparql_query


def element_exists(element_id: str) -> bool:
    """
    Funkcja sprawdza czy podany element (item lub property) istnieje w wikibase
    wywołanie:
        element_exist('Q30')
        element_exist('P4')
    zwraca: True/False
    """
    try:
        my_first_wikidata_item = wbi_core.ItemEngine(item_id=element_id)
        data = my_first_wikidata_item.get_json_representation()
    except (MWApiError, KeyError):
        data = None

    return bool(data)


def element_search(search_string: str, element_type: str, lang: str, **kwargs) -> tuple:
    """
    Funkcja poszukuje kodu item lub property na podstawie podanego tekstu.

    Wywołanie:
        element_search('subclass of', 'property', 'en')
        lub
        element_search('Maria Bielińska', 'item', 'en', description='historyk')
        jeżeli podano argument strict=True to zwróci NOT FOUND także gdy znaleziona
        zostanie częściowo dopasowana właściwość lub element

    Zwraca tuple np.: (True, 'P133') lub (False, 'NOT FOUND')
    """
    description = ''
    aliases = strict = purl_id = False
    if kwargs:
        if 'description' in kwargs:
            description = kwargs['description']
        if 'aliases' in kwargs:
            aliases = kwargs['aliases']
        if 'strict' in kwargs:
            strict = kwargs['strict']
        if 'purl_id' in kwargs:
            purl_id = kwargs['purl_id']

    # jeżeli search_string jest zbyt długi to tylko 243 pierwsze znaki
    if len(search_string) > 240:
        search_string = search_string[:241]

    results = search_entities(search_string, language=lang,
                              search_type=element_type, max_results=50)

    if len(results) == 0:
        return False, "NOT FOUND"

    if len(results) == 1:
        wikidata_item = wbi_core.ItemEngine(item_id=results[0])
        data = wikidata_item.get_json_representation()
        if lang in data['labels']:
            value = data["labels"][lang]["value"]
            if value == search_string:
                if description:
                    if lang in data['descriptions']:
                        value_desc = data["descriptions"][lang]["value"]
                        if value_desc == description:
                            return True, results[0]
                        elif value_desc != description and strict:
                            return False, "NOT FOUND"
                #elif purl_id:
                #    claims = data['claims']

                else:
                    return True, results[0]
            elif aliases:
                value_alias = data["aliases"][lang]
                for alias in value_alias:
                    if search_string == alias['value']:
                        if description:
                            if lang in data['descriptions']:
                                value_desc = data["descriptions"][lang]["value"]
                                if value_desc == description:
                                    return True, results[0]
                        else:
                            return True, results[0]
            # jeżeli szukamy dokładnie takiej etykiety to zawsze ma zwracać NOT FOUND
            elif value != search_string and strict:
                return False, "NOT FOUND"

        else:
            print(f'ERROR, nie znaleziono ["labels"][{lang}] w strukturze odpowiedzi Wikibase.')

        #return False, f"AMBIGIOUS ID FOUND {results}"
        return True, results[0]

    # jeżeli znaleziono wiele elementów/właściwości
    exact_id = ''
    for qid in results:
        wikidata_item = wbi_core.ItemEngine(item_id=qid)
        data = wikidata_item.get_json_representation()
        if lang in data['labels']:
            value = data["labels"][lang]["value"]
            if value == search_string:
                if description:
                    if lang in data['descriptions']:
                        value_desc = data["descriptions"][lang]["value"]
                        print("value:", value)
                        print("search_string:", search_string )
                        print("description:", value_desc)
                        print("search_description", description)
                        if value_desc == description:
                            exact_id = qid
                            break
                else:
                    exact_id = qid
                    break
            elif aliases:
                value_alias = data["aliases"][lang]
                for alias in value_alias:
                    if search_string == alias['value']:
                        if description:
                            if lang in data['descriptions']:
                                value_desc = data["descriptions"][lang]["value"]
                                if value_desc == description:
                                    exact_id = qid
                                    break
                        else:
                            exact_id = qid
                            break
        else:
            print(f'ERROR, nie znaleziono ["labels"][{lang}] w strukturze odpowiedzi Wikibase.')

    if exact_id:
        return True, exact_id

    return False, f"MULTIPLE AMBIGIOUS ID FOUND {results}"


def text_clear(value: str) -> str:
    """ text_clear """
    value = value.strip()
    if ' ' in value:
        value = ' '.join(value.strip().split())

    return value


def get_last_nawias(line: str, only_value: bool = False) -> str:
    """ zwraca zawartość ostatniego nawiasu """
    line = line.strip()
    start = stop = 0
    for i in range(len(line)-1, 0, -1):
        if line[i] == ")":
            stop = i
        elif line[i] == "(":
            start = i + 1

        if start and stop:
            result = line[start:stop]
            break

    if only_value:
        return result

    return result, start - 1


def is_inicial(imie) -> bool:
    """ sprawdza czy przekazany tekst jest inicjałem imienia """
    result = False
    if len(imie) == 2 and imie[0].isupper() and imie.endswith("."):
        result = True

    return result


def ini_only(value: str) -> bool:
    """ sprawdza czy autor ma tylko inicjał pierwszego imienia """
    tmp = value.split(" ")

    return is_inicial(tmp[0])


def format_date(value: str) -> str:
    """ formatuje datę na sposób oczekiwany przez QuickStatements
        np. +1839-00-00T00:00:00Z/9
    """
    result = ''
    if len(value) == 4:                          # tylko rok
        result = f"+{value}-00-00T00:00:00Z/9"
    elif len(value) == 10:                       # dokłada data
        result = f"+{value}T00:00:00Z/11"
    elif len(value) == 2 and value.isnumeric():  # wiek
        result = f"+{str(int(value)-1)}01-00-00T00:00:00Z/7"
    elif len(value) == 1 and value.isnumeric():  # wiek np. X
        value = str(int(value)-1)
        result = f"+{value.zfill(2)}01-00-00T00:00:00Z/7"

    return result


def short_names_in_autor(value: str) -> str:
    """ short names in title """
    zamiana = {}
    lista = re.split(';| i ', value)          # podział na autorów, może być wielu
    for osoba in lista:
        if "Szturm de Sztrem" in osoba:       # specjalna obsługa najpierw
            new_osoba = "T. Szturm de Sztrem"
            zamiana[osoba] = new_osoba
        elif "Wojewódzka Żydowska" in osoba:  # tu bez żadnych zmian
            new_osoba = osoba
            zamiana[osoba] = new_osoba
        elif "na podstawie" in osoba.lower(): # tu bez żadnych zmian
            new_osoba = osoba
            zamiana[osoba] = new_osoba
        elif "red." in osoba.lower():         # tu bez żadnych zmian
            new_osoba = osoba
            zamiana[osoba] = new_osoba
        else:
            osoba = osoba.strip()
            imiona_nazwiska = osoba.split(" ")
            wynik = []
            for i, name_part in enumerate(imiona_nazwiska):
                if i == len(imiona_nazwiska) - 1:         # jeżeli nazwisko
                    wynik.append(name_part)
                elif not is_inicial(name_part):           # jeżeli imię
                    if name_part.startswith('Cz'):
                        wynik.append(name_part[0:2] + ".")
                    elif name_part.startswith('Sz'):
                        wynik.append(name_part[0:2] + ".")
                    else:    
                        wynik.append(name_part[0] + ".")
                else:
                    wynik.append(name_part)               # jeżeli inicjał

            new_osoba = ' '.join(wynik)
            zamiana[osoba] = new_osoba

    for key, val in zamiana.items():
        value = value.replace(key, val)

    return value


def gender_detector(value: str) -> str:
    """ zwraca 'imię męskie' lub 'imię żeńskie' """
    result = ''
    m_wyjatki = ['Zawisza', 'Jarema', 'Kosma', 'Symcha', 'Mustafa', 'Murza',
			    'Baptysta', 'Bonawentura', 'Barnaba', 'Bodzęta', 'Sawa',
                'Benzelstierna', 'Kostka', 'Jura', 'Nata', 'Jona', 'Ilia',
                'Prandota', 'Mrokota', 'Saba', 'Żegota', 'Battista', 'Wierzbięta',
			    'Zaklika', 'Akiba', 'Szaja', 'Sima','Sławęta', 'Szachna', 'Seraja',
                'Prędota', 'Pełka', 'Panięta', 'Ninota', 'Niemira', 'Niemierza',
                'Mykoła', 'Mykola', 'Mikora', 'Luca', 'Kuźma', 'Jursza', 'Janota',
                'Jaksa', 'Hinczka', 'Hincza', 'Bogusza', 'Andrea', 'Dyzma',
                'Ewangelista', 'Juda']
    k_wyjatki = ['Mercedes', 'Denise', 'Huguette', 'Isabel', 'Nijolė', 'Antoinette',
                 'Ruth', 'Rachel', 'Mary', 'Marie', 'Margit', 'Margaret', 'Annie',
                 'Perel', 'Violet']

    if value in m_wyjatki:
        result = 'imię męskie'
    elif value in k_wyjatki:
        result = 'imię żeńskie'

    if result == '':
        if value[len(value)-1].lower() == 'a':
            result = 'imię żeńskie'
        else:
            result = 'imię męskie'

    return result


def get_claim_id(qid: str, claim_property: str, claim_value: str) -> list:
    """ zwraca identyfikator deklaracji """
    claim_id = []

    try:
        wikibase_item = wbi_core.ItemEngine(item_id=qid)
        property_list = wikibase_item.get_property_list()
        if claim_property not in property_list:
            return None

        data = wikibase_item.get_entity()
        if len(data['claims'][claim_property]) > 0:
            for item in data['claims'][claim_property]:
                if item['mainsnak']['datavalue']['value'] == claim_value:
                    claim_id.append(item['id'])

        return claim_id

    except (MWApiError, KeyError, ValueError):
        return None


def search_by_purl(purl_prop_id:str, purl_value: str) -> tuple:
    """ wyszukiwanie elementu na podstawie identyfikatora purl """
    query = f'SELECT ?item WHERE {{ ?item wdt:{purl_prop_id} "{purl_value}". }} LIMIT 5'

    results = execute_sparql_query(query)
    output = []
    for result in results["results"]["bindings"]:
        output.append(result["item"]["value"])

    # wynik to lista adresów http://prunus-208.man.poznan.pl/entity/Q357
    if len(output) == 1:
        search_result = output[0].strip().replace('http://prunus-208.man.poznan.pl/entity/', '')
        return True, search_result

    return False, f'ERROR: brak wyniku lub niejednoznaczny wynik wyszukiwania elementu z identyfikatorem Purl (znaleziono: {len(output)}).'
