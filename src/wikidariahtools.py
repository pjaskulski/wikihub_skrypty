""" funkcje pomocniczne do obsługi skryptów wikibase """

import re
import sys
import sqlite3
from sqlite3 import Error
import geopy.distance
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_exceptions import MWApiError, SearchError
from wikibaseintegrator.wbi_functions import search_entities
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator.wbi_functions import mediawiki_api_call_helper
from wikibaseintegrator.wbi_config import config


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
        if 'purl_id' in kwargs: # czy to ma być tu obsługiwane czy wystarczy search_by_purl?
            purl_id = kwargs['purl_id']

    # jeżeli search_string jest zbyt długi to tylko 243 pierwsze znaki (błąd w wikibase?)
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


def get_claim_value(qid: str, claim_property: str, wikibase_item = None) -> list:
    """ zwraca wartość deklaracji """
    claim_value = []

    try:
        if not wikibase_item:
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
    """ wyszukiwanie elementu na podstawie identyfikatora purl/onto.kul """
    # czyszczenie identyfikatora onto.kul, w wiki jest zapisywany bez http/https
    if 'https' in purl_value:
        purl_value = purl_value.replace('https://','').strip()
    elif  'http' in purl_value:
        purl_value = purl_value.replace('http://','').strip()

    query = f'SELECT ?item WHERE {{ ?item wdt:{purl_prop_id} "{purl_value}". }} LIMIT 5'

    results = execute_sparql_query(query)
    output = []
    for result in results["results"]["bindings"]:
        output.append(result["item"]["value"])

    # wynik to lista adresów http://prunus-208.man.poznan.pl/entity/Q357
    #                     lub https://prunus-208.man.poznan.pl/entity/Q95773
    if len(output) == 1:
        if 'https' in output[0].strip():
            search_result = output[0].strip().replace('https://prunus-208.man.poznan.pl/entity/', '')
        else:
            search_result = output[0].strip().replace('http://prunus-208.man.poznan.pl/entity/', '')
        return True, search_result

    return False, f'ERROR: brak wyniku lub niejednoznaczny wynik wyszukiwania elementu z identyfikatorem Purl (znaleziono: {len(output)}).'


def find_name_qid(name: str, elem_type: str, strict: bool = False, lang: str = 'en') -> tuple:
    """Funkcja sprawdza czy przekazany argument jest identyfikatorem właściwości/elementu
    jeżeli nie to szuka w wikibase właściwości/elementu o etykiecie (ang chyba że przekazano
    parametr lang z kodem języka) równej argumentowi
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
        # onto.kul.pl/ontohgis/administrative_system_1
        onto_pattern = r"onto\.kul\.pl\/ontohgis\/"

        match = re.search(onto_pattern, name)
        # wyszukiwanie elementu z deklaracją 'OntoHGIS ID' o wartości równej
        # zmiennej name
        if match:
            f_result, onto_qid = find_name_qid("OntoHGIS ID", "property")
            if f_result:
                output = search_by_purl(onto_qid, name)
                if not output[0]:
                    output = (False, f"INVALID DATA, {elem_type}: {name}, {output[1]}")
            else:
                output = (False, f"ERROR: {onto_qid}")
        # zwykłe wyszukiwanie
        else:
            output = element_search(name, elem_type, lang, strict=strict)
            if not output[0]:
                output = (False, f"INVALID DATA, {elem_type}: {name}, {output[1]}")

    return output


def get_property_type(p_id: str) -> str:
    """Funkcja zwraca typ właściwości na podstawie jej identyfikatora"""
    # weryfikacja czy typ jest w słowniku typów właściwości, jeżeli jest już taki słownik 
    if hasattr(get_property_type, "PROPERTY_TYPES"):
        if p_id in get_property_type.PROPERTY_TYPES:
            return get_property_type.PROPERTY_TYPES[p_id]
    else:
        # zainicjowanie słownika typów właściwości
        get_property_type.PROPERTY_TYPES = {}

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
        # uzupełnienie słownik typów właściwości
        get_property_type.PROPERTY_TYPES[p_id] = data_type

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


def search_entities_test(search_string, language=None, strict_language=True, search_type='item', mediawiki_api_url=None, max_results=500, dict_result=False, login=None,
                    allow_anonymous=True, user_agent=None):
    """
    Performs a search for entities in the Wikibase instance using labels and aliases.
    :param search_string: a string which should be searched for in the Wikibase instance (labels and aliases)
    :type search_string: str
    :param language: The language in which to perform the search.
    :type language: str
    :param strict_language: Whether to disable language fallback
    :type strict_language: bool
    :param search_type: Search for this type of entity. One of the following values: form, item, lexeme, property, sense
    :type search_type: str
    :param mediawiki_api_url: Specify the mediawiki_api_url.
    :type mediawiki_api_url: str
    :param max_results: The maximum number of search results returned. Default 500
    :type max_results: int
    :param dict_result:
    :type dict_result: boolean
    :param login: The object containing the login credentials and cookies. An instance of wbi_login.Login.
    :param allow_anonymous: Allow anonymous edit to the MediaWiki API. Disabled by default.
    :type allow_anonymous: bool
    :param user_agent: The user agent string transmitted in the http header
    :type user_agent: str
    :return: list
    """

    language = config['DEFAULT_LANGUAGE'] if language is None else language

    params = {
        'action': 'wbsearchentities',
        'search': search_string,
        'language': language,
        'strict_language': strict_language,
        'type': search_type,
        'limit': 50,
        'format': 'json'
    }

    cont_count = 0
    results = []

    while True:
        params.update({'continue': cont_count})

        search_results = mediawiki_api_call_helper(data=params, login=login,
                                                   mediawiki_api_url=mediawiki_api_url,
                                                   user_agent=user_agent,
                                                   allow_anonymous=allow_anonymous)
        #print(search_results)

        if search_results['success'] != 1:
            raise SearchError('Wikibase API wbsearchentities failed')
        else:
            #print('search_results:', len(search_results['search']))
            ile = len(search_results['search'])
            if not ile:
                break
            for i in search_results['search']:
                if dict_result:
                    description = i['description'] if 'description' in i else None
                    aliases = i['aliases'] if 'aliases' in i else None
                    #label = i['label'] if 'label' in i else None
                    #print(label, description)
                    results.append({
                        'id': i['id'],
                        'label': i['label'],
                        'match': i['match'],
                        'description': description,
                        'aliases': aliases
                    })
                else:
                    results.append(i['id'])

        #if 'search-continue' not in search_results:
        #    break
        #else:
        cont_count += ile
        #print('cont_count:', cont_count)

        if cont_count >= max_results:
            break
    #print('search_entities_test results:' ,len(results))
    return results


def element_search_adv(search_string: str, lang: str, parameters: list, description: str = '', max_results_to_verify=10) -> tuple:
    """ wyszukiwanie zaawansowane elementów (item):
        tekst do wyszukania (w etykiecie, opisie, aliasach)
        język
        i lista z parami właściwość-wartość np.
        'województwo poznańskie', [('P202','test')]
        może być pusta (None), wówczas wyszukiwanie tylko po etykiecie i aliasie
        opcjonalnie maksymalna liczba wyników do weryfikacji
        Uwaga: funkcja wyszukuje pierwszy pasujący element, jeżeli w wikibase
        jest więcej elementów pasujących do warunków nie zostaną one znalezione.
        Należy stosować kombinacje jednoznacznych warunków wyszukiwania.
    """

    # jeżeli search_string jest zbyt długi to tylko 241 pierwszych znaków
    if len(search_string) > 240:
        search_string = search_string[:241]

    # obejście problemu z continue w api 'wbsearchentities'
    if max_results_to_verify > 100:
        results = search_entities_test(search_string, language=lang,
                                search_type='item',
                                dict_result=True,
                                max_results=max_results_to_verify)
    else:
        results = search_entities(search_string, language=lang,
                                search_type='item',
                                dict_result=True,
                                max_results=max_results_to_verify)

    if len(results) == 0:
        return False, "NOT FOUND"

    for result in results:
        qid = result['id']
        item_label = result['label']
        item_description = result['description']
        if item_label == search_string:
            if description:
                if item_description != description:
                    continue
            if parameters:
                wb_item = wbi_core.ItemEngine(item_id=qid, search_only=True)
                parameters_count = len(parameters)
                parameters_match = 0
                for par in parameters:
                    property_nr, property_value = par
                    for statement in wb_item.statements:
                        statement_property = statement.get_prop_nr()
                        if statement_property == property_nr:
                            statement_value = statement.get_value()
                            statement_type = get_property_type(statement_property)
                            statement_value = statement_value_fix(statement_value, statement_type)
                            if (statement_value == property_value):
                                parameters_match +=1
                if parameters_match == parameters_count:
                    return True, qid
            else:
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
    latitude_sekundy = tmp_tab[0].split(char)[1].replace('"','').replace('N','').replace('S','').strip()
    sekundy = float(latitude_sekundy)
    if sekundy > 0:
        sekundy = sekundy/60.0
    stopnie = float(latitude.split('.')[0])
    minuty = (float(latitude.split('.')[1]) + sekundy)/60.0
    latitude = str(stopnie + minuty)
    if 'S' in tmp_tab[0]:
        latitude = '-' + latitude

    tmp_tab[1] = tmp_tab[1].strip()
    longitude = tmp_tab[1].split(char)[0].replace('°','.')
    longitude_sekundy = tmp_tab[1].split(char)[1].replace('"','').replace('E','').replace('W','').strip()
    sekundy = float(longitude_sekundy)
    if sekundy > 0:
        sekundy = sekundy/60.0
    stopnie = float(longitude.split('.')[0])
    minuty = (float(longitude.split('.')[1]) + sekundy)/60.0
    longitude = str(stopnie + minuty)
    if 'W' in tmp_tab[1]:
        longitude = '-' + longitude

    return f'{latitude},{longitude}'


def get_properties(prop_list: list) -> dict:
    """ pobiera identyfikatory właściwości z wikibase, zwraca słownik """
    result = {}
    for prop_name in prop_list:
        ok, p_qid = find_name_qid(prop_name, 'property', strict=True)
        if not ok:
            print(f"ERROR: brak właściwości '{prop_name}' w instancji Wikibase")
            sys.exit(1)
        else:
            result[prop_name] = p_qid

    return result


def get_elements(item_list: list) -> dict:
    """ pobiera identyfikatory elementów definicyjnych z wikibase, zwraca słownik """
    result = {}
    for item_name in item_list:
        ok, q_qid = find_name_qid(item_name, 'item', strict=True)
        if not ok:
            # alternatywnie szukanie polskiej wersji etykiety
            ok, q_qid = find_name_qid(item_name, 'item', strict=True, lang='pl')
            if not ok:
                print(f"ERROR: brak elementu '{item_name}' w instancji Wikibase")
                sys.exit(1)

        result[item_name] = q_qid

    return result


def read_qid_from_text(value: str) -> str:
    """ szuka QID w przekazanym tekście """
    result = ''
    pattern = r'Item:Q\d{1,6}' # Item:Q79324
    match = re.search(pattern, value)
    if match:
        result = match.group().split(':')[1]

    return result


def create_connection(db_file, with_extension=False):
    """ tworzy połączenie z bazą SQLite
        db_file - ścieżka do pliku bazy
    """

    conn = None
    try:
        conn = sqlite3.connect(db_file)
        if with_extension:
            conn.enable_load_extension(True)
            conn.load_extension("../fuzzy.so")
            conn.load_extension("../spellfix.so")
            conn.load_extension("../unicode.so")

    except Error as sql_error:
        print(sql_error)

    return conn


def field_strip(value) -> str:
    """ funkcja przetwarza wartość pola z bazy/arkusza """
    if value:
        value = value.strip()
    else:
        value = ''

    return value

def search_sql(db_m, sql: str, latitude: float, longitude: float) -> str:
    """ wyszukiwanie w bazie sqlite,
        db_m - connection do bazy
        sql - zapytanie
        latitude - szerokość geograficzna miejscowości dla której szukamy miejscowości
                   nadrzędnej, w formie dziesiętnej
        longitude - długość geograficzna dla której szukamy miejscowości
                   nadrzędnej, w formie dziesiętnej
        szerokość i długość, służą do obliczania odległości od miejscowości dla której szukamy
        miejscowości nadrzędnej do kandydata na taką miejscowość - w przypadku gdy zapytanie
        zwraca kilka wyników
    """
    result = ''

    cur = db_m.cursor()
    cur.execute(sql)
    rows = cur.fetchall()

    if rows:
        if len(rows) == 1:
            result = field_strip(rows[0][1])
        elif len(rows) > 1:
            coords_1 = (latitude, longitude)
            best_qid = ''
            best_dist = 999999
            for item in rows:
                wgs84 = field_strip(item[3])
                wgs84 = wgs84.replace('Point', '').replace('(', '').replace(')','').strip()
                tmp = wgs84.split(' ')
                item_longitude = float(tmp[0])
                item_latitude = float(tmp[1])
                coords_2 = (item_longitude, item_latitude)
                dist = geopy.distance.geodesic(coords_1, coords_2).km
                if dist < best_dist:
                    best_dist = dist
                    best_qid = field_strip(item[1])
            if best_dist < 999999:
                result = best_qid

    return result


def search_by_unique_id(prop_id: str, id_value: str) -> tuple:
    """ wyszukiwanie elementu na podstawie wartości deklaracji będącej jednoznacznym
        identyfikatorem, zwraca krotkę (True/False, qid) """
    query = f'SELECT ?item WHERE {{ ?item wdt:{prop_id} "{id_value}". }} LIMIT 5'

    results = execute_sparql_query(query)
    output = []
    for result in results["results"]["bindings"]:
        output.append(result["item"]["value"])

    # wynik to lista adresów http://prunus-208.man.poznan.pl/entity/Q357
    #                     lub https://prunus-208.man.poznan.pl/entity/Q95773
    if len(output) == 1:
        if 'https' in output[0].strip():
            search_result = output[0].strip().replace('https://prunus-208.man.poznan.pl/entity/', '')
        else:
            search_result = output[0].strip().replace('http://prunus-208.man.poznan.pl/entity/', '')
        return True, search_result

    return False, f'ERROR: brak wyniku lub niejednoznaczny wynik wyszukiwania elementu z identyfikatorem (znaleziono: {len(output)}).'


def write_or_exit(login_instance, wb_item, logger):
    """ zapis danych do wikibase lub zakończenie programu """
    loop_num = 1
    while True:
        try:
            new_id = wb_item.write(login_instance, entity_type='item')
            break
        except (MWApiError, KeyError) as wb_error:
            err_code = wb_error.error_msg['error']['code']
            message = wb_error.error_msg['error']['info']
            logger.info(f'ERROR: {err_code}, {message}')

            # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
            # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
            if err_code in ['assertuserfailed', 'badtoken']:
                if loop_num == 1:
                    logger.info('Generate edit credentials...')
                    login_instance.generate_edit_credentials()
                    loop_num += 1
                    continue
            # jeżeli błąd zapisu dto druga próba po 5 sekundach
            elif err_code in ['failed-save']:
                if loop_num == 1:
                    logger.info('wait 5 seconds...')
                    loop_num += 1
                    continue

            sys.exit(1)
        except BaseException:
            logger.exception('ERROR: an exception was thrown!')
            sys.exit(1)



    return new_id


def delete_property_or_item(l_instance, params) -> bool:
    """ usuwa wskazany element/właściwość z wikibase
        return: True - usunięto, False - element/właściwość nie istniał/został usunięty wcześniej
    """
    result = False
    # usuwanie z obsługą błędów tokena
    test = 1
    while True:
        try:
            delete_results = mediawiki_api_call_helper(data=params, login=l_instance)
            result = True
            break
        except MWApiError as wb_error:
            err_code = wb_error.error_msg['error']['code']
            message = wb_error.error_msg['error']['info']

            # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
            # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
            if err_code in ['assertuserfailed', 'badtoken']:
                if test == 1:
                    print('Generate edit credentials...')
                    l_instance.generate_edit_credentials()
                    test += 1
                    continue
                else:
                    print(f'ERROR: {err_code}, {message}')
            elif err_code == 'missingtitle': # brak podanego QID w wikibase
                break
            else:
                print(f'ERROR: {err_code}, {message}')

            sys.exit(1) # jeżeli nie obsłużony błąd to koniec pracy

    return result
