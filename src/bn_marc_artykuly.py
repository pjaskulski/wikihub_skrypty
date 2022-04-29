""" Test odczytywania MARC21 z BN z bazy artykułów
    (http://data.bn.org.pl/db/institutions/bibs-artykul.marc) i zapisu w Wikibase
"""
import re
import os
import time
from pathlib import Path
from pymarc import MARCReader, Record
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login, wbi_datatype
from dotenv import load_dotenv


Q_TEST = 'Q79111'
P_TITLE = 'P106'
P_SUBTITLE = 'P107'
P_PUBLICATION_PLACE = 'P112'
P_AUTHOR_STRING = 'P180'
P_PUB_YEAR = 'P114'

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# brak ustawienia tych wartości w wikibase powoduje ostrzeżenia, ale skrypt działa
#wbi_config['PROPERTY_CONSTRAINT_PID'] = 'Pxxx'
#wbi_config['DISTINCT_VALUES_CONSTRAINT_QID'] = 'Qxxx'



# funkcje uzupełniające do obiektu Record
def read_field(self, marc_field: str, marc_subfield: str):
    """ zwraca listę z zawartością wskazanego pola i subpola """
    rec_fields = self.get_fields(marc_field)
    values = []
    for f in rec_fields:
        tmp = f.get_subfields(marc_subfield)
        if tmp:
            values += tmp
    return values


def get_czasopismo(self) -> str:
    """ zwraca nazwę czasopisma lub tytuł publikacji zbiorowej"""
    result = ''
    lista = self.read_field('773', 't')
    if len(lista) > 0:
        result = lista[0].strip()
        if result.endswith('.'):
            result = result[:-1].strip()
        if result.endswith(')'):
            pos = result.find('(')
            if pos > -1:
                result = result[:pos].strip()
        if ' : ' in result:
            pos = result.find(' : ')
            result = result[:pos].strip()

    return result


def get_zeszyt(self) -> str:
    """ zwraca rok, nr tomu, zeszytu, numery stron """
    result = ''
    lista = self.read_field('773', 'g')
    if len(lista) > 0:
        result = lista[0].strip()

    return result


def get_wyrazenie_wprowadzajace(self) -> str:
    """ dla prac zbiorowych zwraca wyrażenie wprowadzające """
    result = ''
    lista = self.read_field('773', 'i')
    if len(lista) > 0:
        result = lista[0].strip()

    return result


def czy_wywiad(self) -> bool:
    """ czy publikacja jest wywiadem? """
    result = False
    lista = self.read_field('100', 'e')
    if lista and 'Wywiad' in lista:
        result = True

    return result


def get_autor(self) -> str:
    """ zwraca autora """
    result = ''

    ## zawartość 245c to większy koszmar ('pozostałe elementy strefy tytułu
    ## i oznaczenia odpowiedzialności'), do rozpatrzenia na później
    # lista = self.read_field('245', 'c')
    # if lista:
    #     result = lista[0].strip()
    #     return result

    lista = self.read_field('100', 'e')
    if lista:
        typ = lista[0].strip()
        if typ == 'Autor':
            part1 = self.read_field('100', 'a')
            if part1:
                result =  part1[0].replace(",", "")
    # jeżeli nie ma 100e ale jest 100a to przyjmujemy, że to autor?
    else:
        part1 = self.read_field('100', 'a')
        if part1:
            result = part1[0].replace(",", "")

    # jeżeli nie znalezono autora to szukamy w 700a
    if not result:
        lista = self.read_field('700', 'a')
        if lista:
            lista = [item.replace(",", "") for item in lista]
            result = ', '.join(lista)

    return result.strip()


def get_tytul(self) -> str:
    """ zwraca tytuł artykułu """
    result = ''
    lista = self.read_field('245', 'a')
    if lista:
        result =  lista[0]

    if '/' in result:
        pos = result.find('/')
        result = result[:pos]

    return result.strip()


def get_podtytul(self) -> str:
    """ zwraca podtytuł artykułu """
    result = ''
    lista = self.read_field('245', 'b')
    if lista:
        result =  lista[0]

    if '/' in result:
        pos = result.find('/')
        result = result[:pos]

    return result.strip()


def get_pubyear(self) -> str:
    """ zwraca rok publikacji """
    result = self.pubyear()
    if not result:
        return ''
    result = result.strip()
    if result.endswith('.'):
        result = result[:-1]

    if not result:
        data_w = self.get_data_wydania()
        if data_w:
            match = re.search(pattern=r'\d{4}', string=data_w)
            if match:
                rok = match.group()
                zeszyt = self.get_zeszyt()
                if rok not in zeszyt:
                    result = rok

    return result.strip()


def czy_praca_zbiorowa(self) -> bool:
    """ czy to artykuł w pracy zbiorowej a nie w czasopiśmie """
    result = False
    lista = self.read_field('655', 'a')
    if 'Artykuł z pracy zbiorowej' in lista:
        result = True

    return result


def czy_historia(self) -> bool:
    """ czy to praca z dziedziny Historia """
    result = False
    lista = self.read_field('658', 'a')
    if 'Historia' in lista:
        result = True

    return result


def get_miejsce_wydania(self) -> str:
    """ zwraca miejsce wydania """
    result = ''
    lista = self.read_field('260', 'a')
    if lista:
        result = lista[0].strip()

    return result


def get_data_wydania(self) -> str:
    """ zwraca datę wydania """
    result = ''
    lista = self.read_field('260', 'c')
    if lista:
        result = lista[0].strip()

    return result


def create_label(self) -> str:
    """ tworzy etykietę elementu w wikibase """
    result = ''
    autor_name = self.get_autor()
    article_title = self.get_tytul()
    subtitle = self.get_podtytul()

    if subtitle:
        article_title += ' ' + subtitle

    czasopismo = self.get_czasopismo()
    czy_zbiorowa = self.czy_praca_zbiorowa()
    wyr_wpr = self.get_wyrazenie_wprowadzajace()
    opublikowano = f'{wyr_wpr} "{czasopismo}"'

    if czy_zbiorowa:
        rok_publ = self.get_pubyear()
        miejsce = self.get_miejsce_wydania()
        miejsce_rok = f'{miejsce} {rok_publ}'.strip()
    else:
        miejsce_rok = ''

    lista = [autor_name, article_title, opublikowano, miejsce_rok]
    result = ', '.join(lista)
    result = result.strip().strip(',').strip()
    zeszyt = self.get_zeszyt()
    result += f', {zeszyt}'

    return result


if __name__ == '__main__':
      # login i hasło ze zmiennych środowiskowych
    env_path = Path('.').parent / 'src/.env'
    load_dotenv(dotenv_path=env_path)
    BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
    BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')

    login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)
    file_marc = Path('.').parent / 'data/bibs-artykul.marc'


    with open(file_marc, 'rb') as fh:
        # dodatkowe metody do klasy record z pymarc
        Record.czy_historia = czy_historia
        Record.czy_wywiad = czy_wywiad
        Record.create_label = create_label
        Record.read_field = read_field
        Record.get_czasopismo = get_czasopismo
        Record.get_zeszyt = get_zeszyt
        Record.get_wyrazenie_wprowadzajace = get_wyrazenie_wprowadzajace
        Record.get_autor = get_autor
        Record.get_tytul = get_tytul
        Record.get_podtytul = get_podtytul
        Record.get_pubyear = get_pubyear
        Record.czy_praca_zbiorowa = czy_praca_zbiorowa
        Record.get_miejsce_wydania = get_miejsce_wydania
        Record.get_data_wydania = get_data_wydania

        reader = MARCReader(fh)
        historia = total = 0

        print('Początek dodawania bibliografii.')
        start = time.time()

        for rec in reader:
            total += 1
            # pomijanie wywiadów
            if rec.czy_wywiad():
                continue

            if rec.czy_historia():
                historia += 1
                label = rec.create_label()

                # deklaracja, że to element testowy
                data_test = wbi_datatype.ItemID(value=Q_TEST, prop_nr='P47')
                data = [data_test]

                # autor
                autor = rec.get_autor()
                data_autor = wbi_datatype.String(value=autor, prop_nr=P_AUTHOR_STRING)
                data.append(data_autor)

                # tytuł
                title = rec.get_tytul()
                data_title = wbi_datatype.MonolingualText(text=title, prop_nr=P_TITLE,
                                                          language='pl')
                data.append(data_title)

                # data wydania
                wydano = rec.get_pubyear()
                if wydano and len(wydano) == 4:
                    data_wydanie = wbi_datatype.Time(time=f'+{wydano}-00-00T00:00:00Z',
                                                     precision=9, prop_nr=P_PUB_YEAR)
                    data.append(data_wydanie)

                wd_item = wbi_core.ItemEngine(new_item=True, data=data)
                wd_item.set_label(label.replace(' s. ', ' p. '), lang='en')
                wd_item.set_label(label,lang='pl')
                wd_item.set_description('publikacja (artykuł)', lang='pl')
                wd_item.set_description('publication (article)', lang='en')

                new_id = wd_item.write(login_instance, bot_account=True, entity_type='item')
                print(new_id)
                #print(label)

                # tylko 100 pierwszych z dziedziny historia
                if historia > 100:
                    break

        end = time.time()
        print(f'\nDodawanie bibliografii zakończone, czas: {end - start} s.')
