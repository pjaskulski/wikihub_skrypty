""" funkcje pomocniczne do obsługi skryptów wikibase """

import re
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikibaseintegrator.wbi_functions import search_entities


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


def element_search(search_string: str, element_type: str, lang: str) -> tuple:
    """
    Funkcja poszukuje kodu item lub property na podstawie podanego tekstu.
    Wywołanie:
        element_search('subclass of', 'property', 'en')
    Zwraca tuple np.: (True, 'P133') lub (False, 'NOT FOUND')
    """
    results = search_entities(search_string, language=lang, search_type=element_type, max_results=5)
    if len(results) == 1:
        return True, results[0]
    else:
        exact_id = ''
        for qid in results:
            wikidata_item = wbi_core.ItemEngine(item_id=qid)
            data = wikidata_item.get_json_representation()
            value = data["labels"]["en"]["value"]
            if value == search_string:
                exact_id = qid
                break
        if exact_id:
            return True, exact_id

        return False, "NOT FOUND"

def text_clear(value: str) -> str:
    """ text_clear """
    value = value.strip()
    if ' ' in value:
        value = ' '.join(value.strip().split())

    return value


def get_last_nawias(line: str) -> str:
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
        +1839-00-00T00:00:00Z/9
    """
    result = ''
    if len(value) == 4:
        result = f"+{value}-00-00T00:00:00Z/9"
    elif len(value) == 10:
        result = f"+{value}T00:00:00Z/11"

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
                    wynik.append(name_part[0] + ".")
                else:
                    wynik.append(name_part)               # jeżeli inicjał

            new_osoba = ' '.join(wynik)
            zamiana[osoba] = new_osoba

    for key, val in zamiana.items():
        value = value.replace(key, val)

    return value
