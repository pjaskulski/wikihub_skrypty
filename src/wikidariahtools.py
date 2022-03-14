# funkcje pomocniczne do obsługi skryptów wikibase
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_functions import execute_sparql_query
from wikibaseintegrator import wbi_login, wbi_datatype
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
    except:
        data = None

    return True if data else False


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
        return False, "NOT FOUND" if len(results) == 0 else "MULTIPLE FOUND"