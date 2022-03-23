""" autorzy.xlsx -> QuickStatements """

import sys
import os
import pickle
from pathlib import Path
from openpyxl import load_workbook
import requests
from urllib.parse import quote
from time import sleep

from biogramy import LOAD_DICT


P_INSTANCE_OF = 'P47'
Q_HUMAN = 'Q32'
P_IMIE = 'P3'
P_NAZWISKO = 'P4'
P_VIAF = 'P79'
P_REFERENCE_URL = 'S182'

# słownik na znalezione identyfikatory
VIAF_ID = {}
LOAD_DICT = True


class Autor:
    """" klasa Autor """

    def __init__(self, p_etykieta: str = '', alias: str = '', p_imie: str = '',
                 p_nazwisko: str = ''):
        """ init """
        self.etykieta = p_etykieta.strip()
        self._alias = alias
        self.imie = p_imie.strip()
        self.nazwisko = p_nazwisko.strip()
        self.viaf = ''
        self.viaf_url = ''

    @property
    def alias(self):
        """ alias """
        return self._alias

    @alias.setter
    def alias(self, value: str):
        """ alias """
        if value:
            value = ' '.join(value.strip().split())
            lista = value.split("|")
            lista = [change_name_forname(item) for item in lista]
            self._alias = lista
        else:
            self._alias = []


def viaf_search(name: str) -> tuple:
    """ szukanie identyfikatora VIAF """
    info = ""
    result = False
    id_url = ""

    # jeżeli identyfikator jest już znany to nie ma potrzeby szukania 
    # przez api
    if name in VIAF_ID:
        result = True
        info = VIAF_ID[name]
        id_url = f"http://viaf.org/viaf/{info}/"    
        return result, info, id_url

    identyfikatory = []  
    urls = {}
    base = 'https://viaf.org/viaf/search'
    format = 'application/json'
    search_person = quote(f'"{name}"')
    adres = f'{base}?query=local.personalNames+=+{search_person}&local.sources+=+"plwabn"&sortKeys=holdingscount&httpAccept={format}'
    
    # mały odstęp między poszukiwaniami
    sleep(0.05)
    
    try:
        response = requests.get(adres)
        result = response.json()
        if 'records' in result['searchRetrieveResponse']:
            rekordy = result['searchRetrieveResponse']['records']
        
            for rekord in rekordy:
                id = rekord['record']['recordData']['viafID']
                if id:
                    url = rekord['record']['recordData']['Document']['@about']
                    if type(rekord['record']['recordData']['mainHeadings']['data']) == list:
                        label = rekord['record']['recordData']['mainHeadings']['data'][0]['text']
                    elif type(rekord['record']['recordData']['mainHeadings']['data']) == dict:
                        label = rekord['record']['recordData']['mainHeadings']['data']['text']
                    
                    if label:
                        label = label.replace(",", "")
                        tmp = name.split(" ")
                        find_items = True
                        for item in tmp:
                            if len(item) > 2 and not item in label:
                                find_items = False
                                break
                        if find_items:
                            identyfikatory.append(id)
                            urls[id] = url
                            VIAF_ID[name] = id  # zapis identyfikatora w słowniku
                            break

    except requests.exceptions.RequestException as e: 
        print(f'Name: {name} ERROR {e}')

    if len(identyfikatory) == 1:
        result = True
        info = identyfikatory[0]
        id_url = urls[info]
    else:
        result = False
        info = f"NOT FOUND"
        id_url = ""

    return result, info, id_url


def change_name_forname(name: str) -> str:
    """ change_name_forname"""
    name_parts = name.split(" ")
    if len(name_parts) == 2 and name_parts[0][0].isupper() and name_parts[1][0].isupper():
        result_name = name_parts[1] + " " + name_parts[0]
    elif (len(name_parts) == 3 and name_parts[0][0].isupper() and name_parts[1][0].isupper()
              and name_parts[2][0].isupper()):
        result_name = name_parts[1] + " " + name_parts[2] + " " + name_parts[0]
    else:
        print(f"ERROR: {name}")
    return result_name


if __name__ == "__main__":
    xlsx_path = Path('.').parent / 'data/autorzy.xlsx'
    output = Path('.').parent / 'out/autorzy.qs'
    log_path = Path('.').parent / 'out/autorzy.log'
    autorzy_pickle = Path('.').parent / 'out/autorzy.pickle'

    # odmrażanie słownika identyfikatorów VIAF
    if LOAD_DICT:
        if os.path.isfile(autorzy_pickle):
            with open(autorzy_pickle, 'rb') as handle:
                VIAF_ID = pickle.load(handle)

    try:
        wb = load_workbook(xlsx_path)
    except IOError:
        print(f"ERROR. Can't open and process file: {xlsx_path}")
        sys.exit(1)

    ws = wb['Arkusz1']

    col_names = {'NAZWA WŁAŚCIWA':0, 'NAZWA WARIANTYWNA (znany też jako)':1}

    autor_list = []
    with open(log_path, "w", encoding='utf-8') as f_log:
        max_row = 50
        for row in ws.iter_rows(2, max_row):
            osoba = row[col_names['NAZWA WŁAŚCIWA']].value
            osoba_alias = row[col_names['NAZWA WARIANTYWNA (znany też jako)']].value

            if osoba:
                autor = Autor()
                osoba = ' '.join(osoba.strip().split()) # podwójne, wiodące i kończące spacje
                tmp = osoba.split(" ")

                if len(tmp) == 2 and tmp[0][0].isupper() and tmp[1][0].isupper():
                    autor.etykieta = tmp[1] + " " + tmp[0]
                    autor.imie = tmp[1]
                    # jeżeli znamy tylko inicjał imienia to nie zakładamy Q
                    if len(autor.imie) == 2 and autor.imie.endswith("."):
                        continue
                    autor.nazwisko = tmp[0]
                elif (len(tmp) == 3 and tmp[0][0].isupper() and tmp[1][0].isupper()
                        and tmp[2][0].isupper()):
                    autor.etykieta = tmp[1] + " " + tmp[2] + " " + tmp[0]
                    autor.imie = tmp[1]
                    autor.nazwisko = tmp[0]
                elif tmp[0].startswith('d’'):
                    autor.etykieta = tmp[1] + " " + tmp[0]
                    autor.imie = tmp[1]
                    autor.nazwisko = tmp[0]
                elif "Szturm de Sztrem" in osoba:
                    autor.etykieta = "Tadeusz Szturm de Sztrem"
                    autor.imie = "Tadeusz"
                    autor.nazwisko = "Szturm de Sztrem"
                else:
                    print(f'ERROR: {osoba}')
                    f_log.write(f'ERROR: {osoba}\n')

                if osoba_alias:
                    autor.alias = osoba_alias

                if autor.etykieta:
                    # szukanie VIAF
                    ok, wynik, wynik_url = viaf_search(autor.etykieta)
                    if ok:
                        autor.viaf = wynik
                        autor.viaf_url = wynik_url
                        print(f'VIAF, {autor.etykieta}, {wynik}, {wynik_url} ')
                    else: 
                        print(f'VIAF, {autor.etykieta}, {wynik}, ')
                        f_log.write(f'VIAF, {autor.etykieta}, {wynik}, \n')

                autor_list.append(autor)

    # zapis Quickstatements w pliku 
    with open(output, "w", encoding='utf-8') as f:
        for autor in autor_list:
            f.write('CREATE\n')
            f.write(f'LAST\tLpl\t"{autor.etykieta}"\n')
            f.write(f'LAST\tLen\t"{autor.etykieta}"\n')
            f.write(f'LAST\t{P_INSTANCE_OF}\t{Q_HUMAN}\n')
            f.write(f'LAST\t{P_IMIE}\t"{autor.imie}"\n')
            f.write(f'LAST\t{P_NAZWISKO}\t"{autor.nazwisko}"\n')
            if autor.alias:
                for item in autor.alias:
                    f.write(f'LAST\tApl\t"{item}"\n')
                    f.write(f'LAST\tAen\t"{item}"\n')
            if autor.viaf and autor.viaf_url:
                f.write(f'LAST\t{P_VIAF}\t"{autor.viaf}"\t{P_REFERENCE_URL}\t"{autor.viaf_url}"\n')

    # zamrażanie słownika identyfikatów VIAF_ID 
    if LOAD_DICT:
        with open(autorzy_pickle, 'wb') as handle:
            pickle.dump(VIAF_ID, handle, protocol=pickle.HIGHEST_PROTOCOL)
