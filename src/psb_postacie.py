""" skrypt do importu postaci z PSB
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
from wikibaseintegrator.datatypes import ExternalID, Time, MonolingualText, Item, URL, String
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.wbi_enums import WikibaseDatePrecision
from wikibaseintegrator.wbi_exceptions import MWApiError
from wikibaseintegrator.wbi_enums import ActionIfExists

# czy zapis do wikibase czy tylko test
WIKIBASE_WRITE = False

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
P_STATED_IN = 'P506'
P_PAGES = 'P479'
P_VOLUME = 'P518'
P_AUTHOR = 'P404'
P_AUTHOR_STR = 'P405'

# elementy definicyjne w testowej instancji wikibase
Q_HUMAN = 'Q229050'

# tomy PSB w testowej instancji PSB jeżeli będą to tomy
PSB = { "1":"Q0001", "2":"Q0002", "3":"Q0002", "4":"Q0002", "5":"Q0002", "6":"Q0002",
       "7":"Q0001", "8":"Q0002", "9":"Q0002", "10":"Q0002", "11":"Q0002", "12":"Q0002",
       "13":"Q0001", "14":"Q0002", "15":"Q0002", "16":"Q0002", "17":"Q0002", "18":"Q0002",
       "19":"Q0001", "20":"Q0002", "21":"Q0002", "22":"Q0002", "23":"Q0002", "24":"Q0002",
       "25":"Q0001", "26":"Q0002", "27":"Q0002", "28":"Q0002", "29":"Q0002", "30":"Q0002",
       "31":"Q0001", "32":"Q0002", "33":"Q0002", "34":"Q0002", "35":"Q0002", "36":"Q0002",
       "37":"Q0001", "38":"Q0002", "39":"Q0002", "40":"Q0002", "41":"Q0002", "42":"Q0002",
       "43":"Q0001", "44":"Q0002", "45":"Q0002", "46":"Q0002", "47":"Q0002", "48":"Q0002",
       "49":"Q0001", "50":"Q0002", "51":"Q0002"
}

# element PSB jeżeli będzie to jeden item
PSB_ITEM = 'Q22343'


class Postac:
    """ dane postaci PSB """

    def __init__(self, postac_dict:dict, logger_object:Logger,
                 login_object:wbi_login.OAuth1, wbi_object: WikibaseIntegrator) -> None:

        self.identyfikator = postac_dict['ID']
        self.name = postac_dict['name']

        self.years = postac_dict.get('years', '')
        if self.years:
            self.years_start = None
            self.years_end = None
            years = self.years.replace('(','').replace(')','').strip()
            tmp = years.split('-')
            if len(tmp) != 2:
                print('ERROR!', years)
            else:
                self.years_start = tmp[0].strip()
                self.years_end = tmp[1].strip()

        self.description_pl = postac_dict.get('description_pl', '')
        self.description_en = postac_dict.get('description_en', '')

        # aliasy z BN, czyli referencja w 'stated as' będzie do BN, nie PSB
        self.aliasy = postac_dict.get('bn_400', [])

        self.date_of_birth = postac_dict.get('date_of_birth', '')
        self.date_of_death = postac_dict.get('date_of_death', '')
        # zmiana formatu dat z DD-MM-YYYY na YYYY-MM-DD
        if self.date_of_birth:
            b_date = self.date_of_birth[6:] + '-' + self.date_of_birth[3:5] + self.date_of_birth[:2]
            self.date_of_birth = b_date
            if self.date_of_birth.startswith('YYYY') and self.years_start:
                self.date_of_birth = self.date_of_birth.replace('YYYY', self.years_start)
        if self.date_of_death:
            d_date = self.date_of_death[6:] + '-' + self.date_of_death[3:5] + self.date_of_death[:2]
            self.date_of_death= d_date
            if self.date_of_death.startswith('YYYY') and self.years_end:
                self.date_of_death = self.date_of_death.replace('YYYY', self.years_end)

        # lata życia postaci z deskryptora BN
        self.bn_years = postac_dict.get('bn_years', '')
        # ~ ? ok. ca po 16.. 1855-06-05 uu przed post non ante 1562/1563 fl. ca 1800%

        # informacje do utworzenia referencji do PSB
        self.volume = postac_dict.get('volume', '')
        self.publ_year = postac_dict.get('publ_year', '')
        self.page = postac_dict.get('page', '')
        self.autor = postac_dict.get('autor', [])

        # identyfikatory
        self.plwabn_id = str(postac_dict.get("id_bn", '')).strip()
        self.id_bn_a = str(postac_dict.get("id_bn_a", '')).strip()
        viaf = str(postac_dict.get('viaf', '')).strip()
        if 'https' in viaf:
            self.viaf = viaf.replace('https://viaf.org/viaf/','').replace(r'/','')
        else:
            self.viaf = viaf.replace('http://viaf.org/viaf/','').replace(r'/','')

        # pola techniczne
        self.wb_item = None                # element
        self.qid = ''                      # znaleziony lub utworzony QID
        self.logger = logger_object        # logi
        self.login_instance = login_object # login instance
        self.wbi = wbi_object              # WikibaseIntegratorObject
        self.reference_psb = None          # referencje do PSB
        self.reference_bn = None           # referencje do Biblioteki Narodowej

        # referencja do elementu PSB (tomu?), do podpięcia dla daty urodzin i śmierci
        if self.volume and self.publ_year:
            self.reference_psb = self.create_psb_reference()
        if self.plwabn_id:
            self.reference_bn = self.create_bn_reference()


    def create_psb_reference(self) -> list:
        """ metoda tworzy referencję do tomu PSB """
        author_list = []
        if self.autor:
            for item in self.autor:
                autor_name = item.get('autor_name','')
                autor_years = item.get('autor_years','')
                as_string = item.get('as_string','')
                if as_string == '1':
                    author_list.append(String(value=autor_name, prop_nr=P_AUTHOR_STR))
                else:
                    autor_qid = self.find_autor(autor_name, autor_years)
                    author_list.append(Item(value=autor_qid, prop_nr=P_AUTHOR))

        # jeżeli osobne tomy PSB
        # result = [[Item(value=PSB[self.volume], prop_nr=P_STATED_IN)],
        #          [String(value=self.page, prop_nr=P_PAGES)],
        #          ]

        # jeżeli jeden element PSB
        result = [[Item(value=PSB_ITEM, prop_nr=P_STATED_IN)],
                  [String(value=self.volume, prop_nr=P_VOLUME)],
                  [String(value=self.page, prop_nr=P_PAGES)],
                  ]

        if author_list:
            result += result

        return result


    def create_bn_reference(self) -> list:
        """ metoda tworzy referencję do deskryptora BN """
        result = None
        if self.id_bn_a:
            adres = f'https://dbn.bn.org.pl/descriptor-details/{self.id_bn_a}'
            result = [[ URL(value=adres, prop_nr=P_REFERENCE_URL) ]]

        return result


    def time_from_string(self, value:str, prop: str, ref:list=None) -> Time:
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
                    references=ref)


    def create_new_item(self):
        """ przygotowuje nowy element do dodania """
        self.wb_item = self.wbi.item.new()

        self.wb_item.labels.set(language='pl', value=self.name)
        self.wb_item.labels.set(language='en', value=self.name)

        self.wb_item.descriptions.set(language='pl', value=self.description_pl)
        self.wb_item.descriptions.set(language='en', value=self.description_en)

        # VIAF
        if self.viaf:
            statement = ExternalID(value=self.viaf, prop_nr=P_VIAF)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # DATY URODZENIA i ŚMIERCI
        if self.date_of_birth:
            statement = self.time_from_string(self.date_of_birth, P_DATE_OF_BIRTH, ref=self.reference_psb)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.date_of_death:
            statement = self.time_from_string(self.date_of_death, P_DATE_OF_DEATH, ref=self.reference_psb)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # lata życia z deskryptora Biblioteki Narodowej

        # PLWABN ID
        if self.plwabn_id:
            statement = ExternalID(value=self.plwabn_id, prop_nr=P_PLWABN_ID)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # ALIASY
        if self.aliasy:
            # wszystkie do j. polskiego, w aliasach nie ma języka 'und'?
            self.wb_item.aliases.set(language='pl', values=self.aliasy, action_if_exists=ActionIfExists.FORCE_APPEND)
            for alias in self.aliasy:
                # TODO: dodać określanie języka i dodawać z pl lub językiem 'und' lub 'mul'
                statement = MonolingualText(text=alias, language='pl',
                                            prop_nr=P_STATED_AS, references=self.reference_bn)
                self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.FORCE_APPEND)

        statement = Item(value=Q_HUMAN, prop_nr=P_INSTANCE_OF)
        self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)


    def update_item(self, update_qid:str):
        """ aktualizacja istniejącego elementu """

        self.wb_item = self.wbi.item.get(entity_id=update_qid)
        description = self.wb_item.descriptions.get(language='pl')
        if not description or description == '-':
            self.wb_item.descriptions.set(language='pl', value=self.description_pl)
            self.wb_item.descriptions.set(language='en', value=self.description_en)

        # VIAF
        item_viaf = ''
        tmp = self.wb_item.claims.get(P_VIAF)
        if tmp:
            item_viaf = tmp[0]
        if self.viaf and (not item_viaf or self.viaf != item_viaf):
            statement = ExternalID(value=self.viaf, prop_nr=P_VIAF)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # DATY URODZENIA i ŚMIERCI
        if self.date_of_birth:
            statement = self.time_from_string(self.date_of_birth, P_DATE_OF_BIRTH, ref=self.reference_psb)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        if self.date_of_death:
            statement = self.time_from_string(self.date_of_death, P_DATE_OF_DEATH, ref=self.reference_psb)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # PLWABN
        item_plwabn = ''
        tmp = self.wb_item.claims.get(P_PLWABN_ID)
        if tmp:
            item_plwabn = tmp[0]
        if self.plwabn_id and (not item_plwabn or self.plwabn_id != item_plwabn):
            statement = ExternalID(value=self.plwabn_id, prop_nr=P_PLWABN_ID)
            self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)

        # ALIASY i STATED AS
        if self.aliasy:
            # wszystkie do j. polskiego, w aliasach nie ma języka 'und'?
            self.wb_item.aliases.set(language='pl', values=self.aliasy, action_if_exists=ActionIfExists.APPEND_OR_REPLACE)
            item_aliasy = self.wb_item.claims.get(P_STATED_AS)
            for alias in self.aliasy:
                if alias not in item_aliasy:
                    # TODO: dodać określanie języka i dodawać z pl lub językiem 'und' lub 'mul'
                    statement = MonolingualText(text=alias, language='pl',
                                            prop_nr=P_STATED_AS, references=self.reference_bn)
                    self.wb_item.claims.add([statement], action_if_exists=ActionIfExists.APPEND_OR_REPLACE)


    def find_autor(self, value:str, years:str) -> str:
        """ wyszukuje autora w wikibase, zwraca QID """
        result = ''

        items = wbi_helpers.search_entities(search_string=value,
                                                language='pl',
                                                search_type='item')
        for item in items:
            wbi_item = self.wbi.item.get(entity_id=item)
            #item_label = wbi_item.labels.get(language='pl')
            item_description = wbi_item.descriptions.get(language='pl')

            years = years.replace('(','').replace(')', '').strip()
            tmp = years.split('-')
            y_start = y_end = ''
            y_start = tmp[0].strip()
            if len(tmp) == 2:
                y_end = tmp[1].strip()
            if ((not y_start or y_start in item_description) and
                (not y_end or y_end in item_description)):
                result = item
                break

        return result


    def appears_in_wikibase(self) -> bool:
        """ proste wyszukiwanie elementu w wikibase, dokładna zgodność imienia i nazwiska
            lata życia
        """
        f_result = False

        items = wbi_helpers.search_entities(search_string=self.name,
                                             language='pl',
                                             search_type='item')
        for item in items:
            wbi_item = self.wbi.item.get(entity_id=item)
            item_label = wbi_item.labels.get(language='pl')

            d_birth = None
            lista = wbi_item.claims.get(P_DATE_OF_BIRTH)
            # uproszczenie, zakładam że obecnie mamy tylko po 1 dacie dla osoby
            if lista:
                d_birth = lista[0]
                print('DATE_OF_BIRTH', d_birth)

            d_death = None
            lista = wbi_item.claims.get(P_DATE_OF_DEATH)
            # uproszczenie, zakładam że obecnie mamy tylko po 1 dacie dla osoby
            if lista:
                d_death = lista[0]
                print('DATE_OF_DEATH', d_death)

            if (item_label == self.name and
                (not d_birth or d_birth == self.date_of_birth) and
                (not d_death or d_death == self.date_of_death) ):
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

        self.qid = new_id.id


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
    file_log = Path('..') / 'log' / 'psb_postacie.log'
    logger = set_logger(file_log)

    logger.info('POCZĄTEK IMPORTU')

    # zalogowanie do instancji wikibase
    login_instance = wbi_login.OAuth1(consumer_token=WIKIDARIAH_CONSUMER_TOKEN,
                                      consumer_secret=WIKIDARIAH_CONSUMER_SECRET,
                                      access_token=WIKIDARIAH_ACCESS_TOKEN,
                                      access_secret=WIKIDARIAH_ACCESS_SECRET)

    wbi = WikibaseIntegrator(login=login_instance)

    input_path = Path("..") / "data" / "postacie.json"
    # test: input_path = '/home/piotr/ihpan/psb_import/data/probka.json'
    output_path = Path("..") / "data" / "postacie_qid.json"

    with open(input_path, "r", encoding='utf-8') as f:
        json_data = json.load(f)
        for i, postac_record in enumerate(json_data['persons']):
            # utworzenie instancji obiektu autora
            postac = Postac(postac_record, logger_object=logger, login_object=login_instance,
                          wbi_object=wbi)

            if not postac.appears_in_wikibase():
                postac.create_new_item()
                if WIKIBASE_WRITE:
                    postac.write_or_exit()
                else:
                    postac.qid = 'TEST'

                message = f'Dodano element: # [https://prunus-208.man.poznan.pl/wiki/Item:{postac.qid} {postac.name}]'
            else:
                message = f'Element istnieje: # [https://prunus-208.man.poznan.pl/wiki/Item:{postac.qid} {postac.name}]'
                postac.update_item(postac.qid)
                if WIKIBASE_WRITE:
                    postac.write_or_exit()

            postac_record['QID'] = postac.qid
            logger.info(message)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, indent=4, ensure_ascii=False)

    end_time = time.time()
    elapsed_time = end_time - start_time
    message = f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.'
    logger.info(message)
