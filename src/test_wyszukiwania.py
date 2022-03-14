from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import execute_sparql_query
# do odczytywania danych z naszej wikibase nie trzeba się logować
#from wikibaseintegrator import wbi_login
from wikidariahtools import element_exists, element_search

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia wartości poniżej w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'


if __name__ == "__main__":

    # pobieranie wskazanego elementu - tu Q30 (Kazimierz Jagiellończyk)
    try:
        my_first_wikidata_item = wbi_core.ItemEngine(item_id='Q30')
        data = my_first_wikidata_item.get_json_representation()
    except:
        data = None

    if data:
        print(len(data))
        print(data["labels"]["pl"]["value"])

    print('Q30: ', element_exists('Q30'))
    print('Q3000: ', element_exists('Q3000'))
    print('P4: ', element_exists('P4'))
    print('Q4000: ', element_exists('Q4000'))

    print('subclass of: ', element_search('subclass of', 'property', 'en'))
    print('date of birth: ', element_search('date of birth', 'property', 'en'))
    print('very unique property: ', element_search('very unique property', 'property', 'en'))
    print('place of: ', element_search('place of', 'property', 'en'))

    print('Świeżawski Tadeusz Michał: ', element_search('Świeżawski Tadeusz Michał', 'item', 'en'))
    print('Świeżowiecki Edwin Gerhard: ', element_search('Świeżowiecki Edwin Gerhard', 'item', 'en'))

    # zapytanie SPARQL o listę wszystkich elementów posiadających właściwość P47 
    # (instance_of) o wartości Q32 (human), z limitem do 5 resultatów
    query = """
        SELECT ?item
        WHERE
        {
            # ?item  instance_of human
            ?item wdt:P47 wd:Q32.
        }
        LIMIT 5
    """

    results = execute_sparql_query(query)
    for result in results["results"]["bindings"]:
        print(result["item"]["value"])
