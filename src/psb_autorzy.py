""" skrypt do importu autorów biogramów PSB """
import os
import sys
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
from wikibaseintegrator.wbi_exceptions import MWApiError


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

# właściwości w testowej instancji wikibase
P_VIAF = 'P517'
P_DATE_OF_BIRTH = 'P422'
P_DATE_OF_DEATH = 'P423'
P_PLWABN_ID = 'P484'

# czy zapis do wikibase czy tylko test
WIKIBASE_WRITE = False


class Autor:
    """ dane autora PSB """

    def __init__(self, author_dict:dict) -> None:

        self.identyfikator = author_dict['ID']
        self.name = author_dict['name']
        if 'years' in author_dict:
            self.description_pl = author_dict['years']
            self.description_en = author_dict['years']
        else:
            self.description_pl = ''
            self.description_en = ''

        if 'date_of_birth' in author_dict:
            self.date_of_birth = author_dict['date_of_birth']
        else:
            self.date_of_birth = ''

        if 'date_of_death' in author_dict:
            self.date_of_death = author_dict['date_of_death']
        else:
            self.date_of_death = ''

        if 'viaf' in author_dict:
            viaf = str(author_dict['viaf'])
            if 'https' in viaf:
                self.viaf = viaf.replace('https://viaf.org/viaf/','').replace(r'/','')
            else:
                self.viaf = viaf.replace('http://viaf.org/viaf/','').replace(r'/','')
        else:
            self.viaf = ''

        if 'plwabn_id' in author_dict:
            self.plwabn_id = author_dict['plwabn_id']
        else:
            self.plwabn_id = ''

        if  'bn_opis' in author_dict:
            self.description_pl += ' ' + author_dict['bn_opis']
        else:
            self.description_pl = ''

        if "description_en" in author_dict:
            self.description_en += ' ' + author_dict['description_en']
        else:
            self.description_en = ''

        # element
        self.wb_item = None
        self.qid = ''


    def time_from_string(self, value:str, prop: str) -> Time:
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


    def create_new_item(self, t_wbi:WikibaseIntegrator):
        """ przygotowuje nowy element do dodania """
        self.wb_item = t_wbi.item.new()

        self.wb_item.labels.set(language='pl', value=self.name)
        self.wb_item.labels.set(language='en', value=self.name)

        self.wb_item.descriptions.set(language='pl', value=self.description_pl)
        self.wb_item.descriptions.set(language='en', value=self.description_en)

        data = []
        if self.viaf:
            statement = ExternalID(value=self.viaf, prop_nr=P_VIAF)
            data.append(statement)

        if self.date_of_birth:
            statement = self.time_from_string(self.date_of_birth, P_DATE_OF_BIRTH)
            data.append(statement)

        if self.date_of_death:
            statement = self.time_from_string(self.date_of_death, P_DATE_OF_DEATH)
            data.append(statement)

        if self.plwabn_id:
            statement = ExternalID(value=self.plwabn_id, prop_nr=P_PLWABN_ID)
            data.append(statement)

        if data:
            self.wb_item.claims.add(data)


    def appears_in_wikibase(self, t_wbi:WikibaseIntegrator) -> bool:
        """ proste wyszukiwanie elementu w wikibase """
        f_result = False

        items = wbi_helpers.search_entities(search_string=self.name,
                                             language='pl',
                                             search_type='item')
        for item in items:
            wbi_item = t_wbi.item.get(entity_id=item)
            item_description = wbi_item.descriptions.get(language='pl')
            if item_description == self.description_pl:
                f_result = True
                break

        return f_result


    def write_or_exit(self, login):
        """ zapis danych do wikibase lub zakończenie programu """
        loop_num = 1
        while True:
            try:
                new_id = self.wb_item.write()
                break
            except MWApiError as wb_error:
                err_code = wb_error.code
                message = wb_error.messages
                print(f'ERROR: {err_code}, {message}')

                # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                if err_code in ['assertuserfailed', 'badtoken']:
                    if loop_num == 1:
                        print('błąd "badtoken", odświeżenie poświadczenia...')
                        login.generate_edit_credentials()
                        loop_num += 1
                        continue
                # jeżeli błąd zapisu dto druga próba po 5 sekundach
                elif err_code in ['failed-save']:
                    if loop_num == 1:
                        print('błąd zapisu, czekam 5 sekund...')
                        loop_num += 1
                        continue

                sys.exit(1)

        self.qid = new_id


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
        json_data = json.load(f)
        for i, autor_record in enumerate(json_data['authors']):
            autor = Autor(autor_record)
            if not autor.appears_in_wikibase(wbi):
                if WIKIBASE_WRITE:
                    autor.create_new_item(wbi)
                    autor.write_or_exit(login_instance)
                else:
                    autor.qid = 'TEST'

                print(f'Dodano element: {autor.name} z QID: {autor.qid}')

            else:
                print(f'Element "{autor.name}" już istnieje w tej instancji Wikibase.')


    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
