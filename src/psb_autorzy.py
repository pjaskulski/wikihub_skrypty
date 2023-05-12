""" skrypt do importu autorów biogramów PSB """
import os
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.datatypes import ExternalID, Time
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision


# adresy wikibase
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'
wbi_config['USER_AGENT'] = 'MyWikibaseBot/1.0'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

# OAuth
WIKIDARIAH_CONSUMER_TOKEN = os.environ.get('WIKIDARIAH_CONSUMER_TOKEN')
WIKIDARIAH_CONSUMER_SECRET = os.environ.get('WIKIDARIAH_CONSUMER_SECRET')
WIKIDARIAH_ACCESS_TOKEN = os.environ.get('WIKIDARIAH_ACCESS_TOKEN')
WIKIDARIAH_ACCESS_SECRET = os.environ.get('WIKIDARIAH_ACCESS_SECRET')

P_VIAF = 'P517'
P_DATE_OF_BIRTH = 'P422'
P_DATE_OF_DEATH = 'P423'
P_PLWABN_ID = 'P484'

# czy zapis do wikibase czy tylko test
WIKIBASE_WRITE = False


def find_item(label:str, description:str, search:str='item', language:str='pl') -> str:
    """ proste wyszukiwanie elementu w wikibase """
    result = ''

    result = wbi_helpers.search_entities(search_string=label, language=language, search_type=search)
    for item in result:
        wbi_item = wbi.item.get(entity_id=item)
        item_description = wbi_item.descriptions.get(language=language)
        if item_description == description:
            result = item
            break

    return result


def time_from_string(value:str, prop: str) -> str:
    """ przekształca datę z json na time oczekiwany przez wikibase """
    year = value[:4]
    month = value[5:7]
    day = value[8:]

    precision = WikibaseDatePrecision.YEAR
    if day != '00':
        precision = WikibaseDatePrecision.DAY
    elif day == '00' and month != '00':
        precision = WikibaseDatePrecision.MONTH
        day = '01'
    else:
        day = month = '01'

    format_time =  f'+{year}-{month}-{day}T00:00:00Z'

    return Time(prop_nr=prop, time=format_time, precision=precision)



# ------------------------------------------------------------------------------
if __name__ == '__main__':

    # pomiar czasu wykonania
    start_time = time.time()

    login_instance = wbi_login.OAuth1(consumer_token=WIKIDARIAH_CONSUMER_TOKEN,
                                      consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                      access_token=WIKIDARIAH_ACCESS_TOKEN,
                                      access_secret=WIKIDARIAH_ACCESS_SECRET)

    wbi = WikibaseIntegrator(login=login_instance)

    input_path = Path("..") / "data" / "autorzy.json"

    with open(input_path, "r", encoding='utf-8') as f:
        data = json.load(f)
        for i, autor in enumerate(data['authors']):
            name = autor['name']
            date_of_birth = date_of_death = viaf = plwabn_id = ''
            autor_id = description_pl = description_en = ''
            if 'years' in autor:
                description_pl = description_en =  autor['years']
            if 'date_of_birth' in autor:
                date_of_birth = autor['date_of_birth']
            if 'date_of_death' in autor:
                date_of_death = autor['date_of_death']
            if 'viaf' in autor:
                viaf = str(autor['viaf'])
                if 'https' in viaf:
                    viaf = viaf.replace('https://viaf.org/viaf/','').replace(r'/','')
                else:
                    viaf = viaf.replace('http://viaf.org/viaf/','').replace(r'/','')
            if 'plwabn_id' in autor:
                plwabn_id = autor['plwabn_id']
            if 'autor_id' in autor:
                autor_id = autor['ID']
            if  'bn_opis' in autor:
                description_pl += ' ' + autor['bn_opis']
            if "description_en" in autor:
                description_en += ' ' + autor['description_en']

            item_exists = find_item(label=name, description=description_pl)
            if not item_exists:
                wb_item = wbi.item.new()

                wb_item.labels.set(language='pl', value=name)
                wb_item.labels.set(language='en', value=name)

                wb_item.descriptions.set(language='pl', value=description_pl)
                wb_item.descriptions.set(language='en', value=description_en)

                data = []
                if viaf:
                    statement = ExternalID(value=viaf, prop_nr=P_VIAF)
                    data.append(statement)

                if date_of_birth:
                    statement = time_from_string(date_of_birth, P_DATE_OF_BIRTH)
                    data.append(statement)

                if date_of_death:
                    statement = time_from_string(date_of_death, P_DATE_OF_DEATH)
                    data.append(statement)

                if plwabn_id:
                    statement = ExternalID(value=plwabn_id, prop_nr=P_PLWABN_ID)
                    data.append(statement)

                if data:
                    wb_item.claims.add(data)

                if WIKIBASE_WRITE:
                    result = wb_item.write()
                else:
                    result = 'TEST'

                print(f'Dodano element: {name} z QID: {result}')

            else:
                print(f'Element "{name}" już istnieje w tej instancji Wikibase.')


    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
