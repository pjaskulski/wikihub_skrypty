""" skrypt do importu autorów biogramów PSB
    uwaga: wymaga biblioteki WikibaseIntegrator w wersji 0.12 lub nowszej
"""
import os
import sys
import time
import json
import logging
from logging import Logger
import warnings
from pathlib import Path
from dotenv import load_dotenv
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.datatypes import ExternalID, Time, MonolingualText, Item, URL
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision
from wikibaseintegrator.wbi_exceptions import MWApiError
from wikibaseintegrator.wbi_enums import ActionIfExists

warnings.filterwarnings("ignore")

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
P_STATED_AS = 'P505'
P_INSTANCE_OF = 'P459'
P_REFERENCE_URL = 'P399'

# elementy definicyjne w instancji wikibase
Q_HUMAN = 'Q1'

# czy zapis do wikibase czy tylko test
WIKIBASE_WRITE = False


class Autor:
    """ dane autora PSB """

    def __init__(self, author_dict:dict, logger_object:Logger,
                 login_object:wbi_login.OAuth1, wbi_object: WikibaseIntegrator,
                 references:list) -> None:

        self.identyfikator = author_dict['ID']
        self.name = author_dict['name']

        self.description_pl = author_dict.get('years', '')
        self.description_en = author_dict.get('years', '')

        self.description_pl += ' ' + author_dict.get('bn_opis', '')
        self.description_pl = self.description_pl.strip()

        self.description_en += ' ' + author_dict.get('description_en', '')
        self.description_en = self.description_en.strip()

        self.aliasy = author_dict.get('aliasy', [])

        self.date_of_birth = author_dict.get('date_of_birth', '')
        self.date_of_death = author_dict.get('date_of_death', '')

        viaf = str(author_dict.get('viaf', ''))
        if 'https' in viaf:
            self.viaf = viaf.replace('https://viaf.org/viaf/','').replace(r'/','')
        else:
            self.viaf = viaf.replace('http://viaf.org/viaf/','').replace(r'/','')

        self.plwabn_id = author_dict.get('plwabn_id', '')

        self.wb_item = None                # element
        self.qid = ''                      # znaleziony lub utworzony QID
        self.logger = logger_object        # logi
        self.login_instance = login_object # login instance
        self.wbi = wbi_object              # WikibaseIntegratorObject
        self.references = references       # referencje


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

        return Time(prop_nr=prop, time=format_time, precision=precision,
                    references=self.references)


    def create_new_item(self):
        """ przygotowuje nowy element do dodania """
        self.wb_item = self.wbi.item.new()

        self.wb_item.labels.set(language='pl', value=self.name)
        self.wb_item.labels.set(language='en', value=self.name)

        self.wb_item.descriptions.set(language='pl', value=self.description_pl)
        self.wb_item.descriptions.set(language='en', value=self.description_en)

        if self.viaf:
            statement = ExternalID(value=self.viaf, prop_nr=P_VIAF,
                                   references=self.references)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.date_of_birth:
            statement = self.time_from_string(self.date_of_birth, P_DATE_OF_BIRTH)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.date_of_death:
            statement = self.time_from_string(self.date_of_death, P_DATE_OF_DEATH)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.plwabn_id:
            statement = ExternalID(value=self.plwabn_id, prop_nr=P_PLWABN_ID,
                                   references=self.references)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.aliasy:
            self.wb_item.aliases.set(language='pl', values=self.aliasy, action_if_exists=ActionIfExists.FORCE_APPEND)
            for alias in self.aliasy:
                statement = MonolingualText(text=alias, language='pl',
                                            prop_nr=P_STATED_AS,
                                            references=self.references)
                self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.FORCE_APPEND)

        statement = Item(value=Q_HUMAN, prop_nr=P_INSTANCE_OF)
        self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)


    def appears_in_wikibase(self) -> bool:
        """ proste wyszukiwanie elementu w wikibase """
        f_result = False

        items = wbi_helpers.search_entities(search_string=self.name,
                                             language='pl',
                                             search_type='item')
        for item in items:
            wbi_item = self.wbi.item.get(entity_id=item)
            item_description = wbi_item.descriptions.get(language='pl')
            item_viaf = ''
            if autor.viaf:
                tmp_viaf = wbi_item.claims.get(P_VIAF)
                if tmp_viaf:
                    item_viaf = tmp_viaf[0]
            if ((not self.description_pl or item_description == self.description_pl) and
               (not self.viaf or item_viaf == self.viaf)):
                f_result = True
                self.qid = item
                break

        return f_result


    def write_or_exit(self):
        """ zapis danych do wikibase lub zakończenie programu """
        loop_num = 1
        while True:
            try:
                new_id = self.wb_item.write()
                break
            except MWApiError as wb_error:
                err_code = wb_error.code
                err_message = wb_error.messages
                self.logger.error(f'ERROR: {err_code}, {err_message}')

                # jeżeli jest to problem z tokenem to próba odświeżenia tokena i powtórzenie
                # zapisu, ale tylko raz, w razie powtórnego błędu bad token, skrypt kończy pracę
                if err_code in ['assertuserfailed', 'badtoken']:
                    if loop_num == 1:
                        self.logger.error('błąd "badtoken", odświeżenie poświadczenia...')
                        self.login_instance.generate_edit_credentials()
                        loop_num += 1
                        continue
                # jeżeli błąd zapisu dto druga próba po 5 sekundach
                elif err_code in ['failed-save']:
                    if loop_num == 1:
                        self.logger.error('błąd zapisu, czekam 5 sekund...')
                        loop_num += 1
                        continue

                sys.exit(1)

        self.qid = new_id


def set_logger(path:str) -> Logger:
    """ utworzenie loggera """
    logger_object = logging.getLogger(__name__)
    logger_object.setLevel(logging.INFO)
    log_format = logging.Formatter('%(asctime)s - %(message)s')
    c_handler = logging.StreamHandler()
    c_handler.setFormatter(log_format)
    c_handler.setLevel(logging.DEBUG)
    logger_object.addHandler(c_handler)
    # zapis logów do pliku tylko jeżeli skrypt uruchomiono z zapisem do wiki
    if WIKIBASE_WRITE:
        f_handler = logging.FileHandler(path)
        f_handler.setFormatter(log_format)
        f_handler.setLevel(logging.INFO)
        logger_object.addHandler(f_handler)

    return logger_object


# ------------------------------------------------------------------------------
if __name__ == '__main__':

    # pomiar czasu wykonania
    start_time = time.time()

    # tworzenie obiektu loggera
    file_log = Path('..') / 'log' / 'psb_autorzy.log'
    logger = set_logger(file_log)

    logger.info('POCZĄTEK IMPORTU')

    # referencje globalne (czy referencja do BN będzie URL-em czy Item-em?)
    references_bn = [[ URL(value='https://data.bn.org.pl/institutions/authorities',
                           prop_nr=P_REFERENCE_URL) ]]

    # zalogowanie do instancji wikibase
    login_instance = wbi_login.OAuth1(consumer_token=WIKIDARIAH_CONSUMER_TOKEN,
                                      consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                      access_token=WIKIDARIAH_ACCESS_TOKEN,
                                      access_secret=WIKIDARIAH_ACCESS_SECRET)

    wbi = WikibaseIntegrator(login=login_instance)

    input_path = Path("..") / "data" / "autorzy.json"
    output_path = Path("..") / "data" / "autorzy_qid.json"

    with open(input_path, "r", encoding='utf-8') as f:
        json_data = json.load(f)
        for i, autor_record in enumerate(json_data['authors']):

            autor = Autor(autor_record, logger_object=logger, login_object=login_instance,
                          wbi_object=wbi, references=references_bn)

            if not autor.appears_in_wikibase():
                autor.create_new_item()

                if WIKIBASE_WRITE:
                    autor.write_or_exit()
                else:
                    autor.qid = 'TEST'

                message = f'Dodano element: {autor.name} z QID: {autor.qid}'
            else:
                message = f'Element "{autor.name}" już istnieje w tej instancji Wikibase (QID: {autor.qid}).'

            autor_record['QID'] = autor.qid
            logger.info(message)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    message = f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.'
    logger.info(message)
