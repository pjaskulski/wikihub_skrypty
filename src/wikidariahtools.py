""" funkcje pomocniczne do obsługi skryptów wikibase """

import re
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikibaseintegrator.wbi_functions import search_entities
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper


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
                        #print("value:", value)
                        #print("search_string:", search_string )
                        #print("description:", value_desc)
                        #print("search_description", description)
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


def get_claim_value(qid: str, claim_property: str) -> list:
    """ zwraca identyfikator deklaracji """
    claim_value = []

    try:
        wikibase_item = wbi_core.ItemEngine(item_id=qid)
        property_list = wikibase_item.get_property_list()
        if claim_property not in property_list:
            return None

        data = wikibase_item.get_entity()
        if len(data['claims'][claim_property]) > 0:
            for item in data['claims'][claim_property]:
                if 'value' in item['mainsnak']['datavalue']:
                    value_json = item["mainsnak"]["datavalue"]["value"]
                    if (
                        "type" in item["mainsnak"]["datavalue"]
                        and item["mainsnak"]["datavalue"]["type"] == "string"
                    ):
                        value = value_json
                    elif "text" in value_json and "language" in value_json:
                        value = f"{value_json['language']}:\"{value_json['text']}\""
                    elif "entity-type" in value_json:
                        value = value_json["id"]
                    elif "latitude" in value_json:
                        value = f"{value_json['latitude']},{value_json['longitude']}"
                    elif "time" in value_json:
                        value = f"{value_json['time']}/{value_json['precision']}"
                    elif "amount" in value_json:
                        value = value_json["amount"]
                        if value.startswith("+"):
                            value = value[1:]
                    else:
                        value = "???"

                    claim_value.append(value)

        return claim_value

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


def find_name_qid(name: str, elem_type: str, strict: bool = False) -> tuple:
    """Funkcja sprawdza czy przekazany argument jest identyfikatorem właściwości/elementu
    jeżeli nie to szuka w wikibase właściwości/elementu o etykiecie (ang) równej argumentowi
    (jeżeli strict=True to dokładnie równej) i zwraca jej id
    """
    output = (True, name)  # zakładamy, że w name jest id (np. P47)
    # ale jeżeli nie, to szukamy w wikibase

    # jeżeli szukana wartość name = 'somevalue' lub 'novalue' to zwraca True i wartość
    if name == "somevalue" or name == "novalue":
        return (True, name)

    if elem_type == "property":
        pattern = r"^P\d{1,9}$"
    elif elem_type == "item":
        pattern = r"^Q\d{1,9}$"

    match = re.search(pattern, name)
    if not match:
        # http://purl.org/ontohgis#administrative_system_1
        purl_pattern = r"https?:\/\/purl\.org\/"

        match = re.search(purl_pattern, name)
        # wyszukiwanie elementu z deklaracją 'purl identifier' o wartości równej
        # zmiennej name
        if match:
            f_result, purl_qid = find_name_qid("purl identifier", "property")
            if f_result:
                output = search_by_purl(purl_qid, name)
                if not output[0]:
                    output = (False, f"INVALID DATA, {elem_type}: {name}, {output[1]}")
            else:
                output = (False, f"ERROR: {purl_qid}")
        # zwykłe wyszukiwanie
        else:
            output = element_search(name, elem_type, "en", strict=strict)
            if not output[0]:
                output = (False, f"INVALID DATA, {elem_type}: {name}, {output[1]}")

    return output


def get_property_type(p_id: str) -> str:
    """Funkcja zwraca typ właściwości na podstawie jej identyfikatora"""
    params = {"action": "wbgetentities", "ids": p_id, "props": "datatype"}

    search_results = mediawiki_api_call_helper(
        data=params,
        login=None,
        mediawiki_api_url=None,
        user_agent=None,
        allow_anonymous=True,
    )
    data_type = None
    if search_results:
        data_type = search_results["entities"][p_id]["datatype"]

    return data_type


def statement_value_fix(s_value, s_type) -> str:
    """poprawia wartość pobraną z deklaracji właściwości"""
    if s_value is None:
        return s_value

    if s_type == "monolingualtext":
        s_value = s_value[1] + ':"' + s_value[0] + '"'
    elif s_type == "quantity":
        if isinstance(s_value, tuple):
            s_value = s_value[0].replace("+", "").replace("-", "")
        else:
            s_value = str(s_value)
    elif s_type == "globe-coordinate":
        if isinstance(s_value, tuple):
            s_value = str(s_value[0]) + "," + str(s_value[1])
        else:
            s_value = str(s_value)
    elif s_type == "wikibase-item":
        if isinstance(s_value, int):
            s_value = str(s_value)
        if not s_value.startswith("Q"):
            s_value = "Q" + s_value
    elif s_type == "time":
        if isinstance(s_value, tuple):
            s_value_time = s_value[0]
            if s_value_time is None:
                s_value = None
            elif isinstance(s_value_time, str):
                s_value = s_value_time + "/" + str(s_value[3])
            else:
                print(f"ERROR: wartość typu time: {s_value}")
    else:
        if not isinstance(s_value, str):
            s_value = str(s_value)

    return s_value


def element_search_adv(search_string: str, lang: str, parameters: list, description: str = '') -> tuple:
    """ wyszukiwanie zaawansowane elementów (item):
        tekst do wyszukania (w etykiecie, opisie, aliasach)
        język
        i lista z parami właściwość-wartość np.
        'województwo poznańskie', [('P202','test')]
    """

    if not parameters:
        print('ERROR - brak dodatkowych parametrów wyszukiwania.')
        return False, "NOT FOUND"

    # jeżeli search_string jest zbyt długi to tylko 243 pierwsze znaki
    if len(search_string) > 240:
        search_string = search_string[:241]

    results = search_entities(search_string, language=lang,
                              search_type='item', max_results=50)

    if len(results) == 0:
        return False, "NOT FOUND"

    for qid in results:
        wb_item = wbi_core.ItemEngine(item_id=qid)
        label = wb_item.get_label(lang)
        if description:
            item_description = wb_item.get_description(lang)
        if label == search_string:
            for par in parameters:
                property_nr, property_value = par
                for statement in wb_item.statements:
                    statement_property = statement.get_prop_nr()
                    if statement_property == property_nr:
                        statement_value = statement.get_value()
                        statement_type = get_property_type(statement_property)
                        statement_value = statement_value_fix(statement_value, statement_type)
                        if (statement_value == property_value and
                            (description == '' or item_description == description)):
                            return True, qid

    return False, "NOT FOUND"


def get_coord(value: str) -> str:
    """ funkcja przyjmuje współrzędne w formie stopni, minut i sekund (długość i szerokość
        geograficzna) np. # 56°30'00" N, 23°30'00" E
        a zwraca współrzędne w formie oczekiwanej przez wikibase (stopnie
        w formie liczby zmiennoprzecinkowej np.: 56.5, 23.5.
    """
    if value.strip() == '':
        return ''

    tmp_tab = value.split(',')
    char = "'"
    latitude = tmp_tab[0].split(char)[0].replace('°','.')
    stopnie = float(latitude.split('.')[0])
    minuty = float(latitude.split('.')[1])/60.0
    latitude = str(stopnie + minuty)
    if 'S' in tmp_tab[0]:
        latitude = '-' + latitude

    tmp_tab[1] = tmp_tab[1].strip()
    longitude = tmp_tab[1].split(char)[0].replace('°','.')
    stopnie = float(longitude.split('.')[0])
    minuty = float(longitude.split('.')[1])/60.0
    longitude = str(stopnie + minuty)
    if 'W' in tmp_tab[1]:
        longitude = '-' + longitude

    return f'{latitude},{longitude}'