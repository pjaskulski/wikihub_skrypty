""" autorzy.xlsx -> imiona i nazwiska do QuickStatements """

import sys
import os
import pickle
from time import sleep
from pathlib import Path
from openpyxl import load_workbook
from wikibaseintegrator.wbi_config import config as wbi_config
from wikidariahtools import element_search, get_last_nawias

# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# listy na znalezione imiona i nazwiska
IMIONA = []
NAZWISKA = []

# słowniki na QID imion i nazwisk
IMIONA_QID = {}
NAZWISKA_QID = {}

LOAD_DICT = True
SAVE_DICT = True


def is_inicial(imie) -> bool:
    """ sprawdza czy przekazany tekst jest inicjałem imienia """
    result = False
    if len(imie) == 2 and imie[0].isupper() and imie.endswith("."):
        result = True

    return result


def get_name(value: str) -> tuple:
    """ get_name """
    p_imie = p_imie2 = p_nazwisko = ''

    not_forname = ['Judaeus', 'Bohemus', 'Hohenzollern', 'Wszewołodowicz',
                   'Caucina', 'Courtenay', 'Vasseur', 'Gallo', 'Chrobry',
                   'Mieszkowic', 'Szczodry', 'Krzywousty', 'Kędzierzawy', 'Wstydliwy',
                   'Wysoki', 'Łysy', 'Pobożny', 'Hojny', 'Sforza', 'Radziwiłłówna', 
                   'III', 'II', 'IV', 'VIII', 'IX', 'VI', 'VII', 'Rachtamowicz',
                   'Michajłowicz', 'Abrahamowic', 'Pesach-Libman', 'Sprawiedliwy',
                   'Odnowiciel', 'Oleksowicz', 'Przecławski', 'Namysłowski',
                   'Mniszchówna', 'Bohuszewicz']

    if 'młodszy' in value:
        value = value.replace("młodszy", "").strip()
    if 'starszy' in value:
        value = value.replace("starszy", "").strip()

    tmp = value.strip().split(" ")
    if len(tmp) == 1:
        # czy to imię czy nazwisko? Słownik typowych imion a jeżeli spoza to nazwisko?
        p_imie = tmp[0].strip()
    elif len(tmp) == 2:
        if tmp[0][0].isupper() and tmp[1][0].isupper():
            if tmp[1].strip() in not_forname:
                p_nazwisko = tmp[1].strip()
                p_imie = tmp[0].strip()
            else:
                p_nazwisko = tmp[0].strip()
                p_imie = tmp[1].strip()
    elif len(tmp) == 3:
        if tmp[0][0].isupper() and tmp[1][0].isupper() and tmp[2][0].isupper():
            if tmp[2].strip() in not_forname:
                p_nazwisko = tmp[2].strip()
                p_imie = tmp[0].strip()
                if tmp[1].strip() not in not_forname:
                    p_imie2 = tmp[1].strip()
            else:
                p_nazwisko = tmp[0].strip()
                p_imie = tmp[1].strip()
                p_imie2 = tmp[2].strip()
        else:
            if ' z ' in value:
                p_imie = tmp[0].strip()
    else:
        if ' de ' in value:
            p_imie = tmp[-1].strip()
            p_nazwisko = ' '.join(tmp[:-1])

    return p_nazwisko, p_imie, p_imie2


if __name__ == "__main__":
    file_path = Path('.').parent / 'data/lista_hasel_PSB_2020.txt'
    output_imiona = Path('.').parent / 'out/postacie_imiona.qs'
    output_nazwiska = Path('.').parent / 'out/postacie_nazwiska.qs'
    imiona_qid_pickle = Path('.').parent / 'out/imiona_qid.pickle'
    nazwiska_qid_pickle = Path('.').parent / 'out/nazwiska_qid.pickle'
    
    # odmrażanie słowników QID dla imion i nazwisk
    if LOAD_DICT:
        if os.path.isfile(imiona_qid_pickle):
            with open(imiona_qid_pickle, 'rb') as handle:
                IMIONA_QID = pickle.load(handle)
        if os.path.isfile(nazwiska_qid_pickle):
            with open(nazwiska_qid_pickle, 'rb') as handle:
                NAZWISKA_QID = pickle.load(handle)

    with open(file_path, "r", encoding='utf-8') as f:
        indeks = f.readlines()

    if not indeks:
        print('ERROR: empty index')
        sys.exit(1)
    
    for line in indeks:
        nawias, title_stop = get_last_nawias(line)
        title = line[:title_stop].strip()
        name = imie = imie2 = nazwisko = ''

        start = title.find('(')
        name = title[:start].strip()
        nazwisko, imie, imie2 = get_name(name)
        print(f'Przetwarzanie: {nazwisko} {imie} {imie2}')

        if imie and not imie in IMIONA and not is_inicial(imie) and len(imie) > 1:
            IMIONA.append(imie)

        if imie2 and not imie2 in IMIONA and not is_inicial(imie2) and len(imie2) > 1:
            IMIONA.append(imie2)

        if nazwisko and not nazwisko in NAZWISKA and len(nazwisko) > 1:
            NAZWISKA.append(nazwisko)

    # weryfikacja imion w wikibase
    for imie in IMIONA:
        print(f'Weryfikacja imienia: {imie}')
        if imie in IMIONA_QID:
            ok = True
            qid = IMIONA_QID[imie]
        else:   
            sleep(0.05) # mały odstęp między poszukiwaniami
            ok, qid = element_search(imie, 'item', 'pl', description='imię')
            if ok:
                IMIONA_QID[imie] = qid
        
        if ok:
            print(f'Znaleziono: {imie} w Wikibase: {qid}.')
            IMIONA.remove(imie)
    
    # IMIONA = set(IMIONA) # zbiór zawiera tylko unikalne (kontrola jest też wyżej)
    
    # zapis imiona Quickstatements w pliku 
    print('Zapis quickstatements dla imion...')
    with open(output_imiona, "w", encoding='utf-8') as f:
        for imie in sorted(IMIONA):
            #męskie czy żeńskie?
            f.write('CREATE\n')
            f.write(f'LAST\tLpl\t"{imie}"\n')
            f.write(f'LAST\tLen\t"{imie}"\n')
            f.write(f'LAST\tDpl\t"imię"\n')
            f.write(f'LAST\tDen\t"given name"\n')

    # weryfikacja nazwisk w wikibase
    for nazwisko in NAZWISKA:
        print(f'Weryfikacja nazwiska: {nazwisko}')
        if nazwisko in NAZWISKA_QID:
            ok = True
            qid = NAZWISKA_QID[imie]
        else: 
            sleep(0.05) # mały odstęp między poszukiwaniami
            ok, qid = element_search(nazwisko, 'item', 'pl', description='nazwisko')
            if ok:
                NAZWISKA_QID[nazwisko] = qid
        
        if ok:
            print(f'Znaleziono: {nazwisko} w Wikibase: {qid}.')
            NAZWISKA.remove(nazwisko)

    # NAZWISKA = set(NAZWISKA) # zbiór zawiera tylko unikalne (kontrola jest też wyżej)

    # zapis nazwisk Quickstatements w pliku 
    print('Zapis quickstatements dla nazwisk...')
    with open(output_nazwiska, "w", encoding='utf-8') as f:
        for nazwisko in NAZWISKA:
            f.write('CREATE\n')
            f.write(f'LAST\tLpl\t"{nazwisko}"\n')
            f.write(f'LAST\tLen\t"{nazwisko}"\n')
            f.write(f'LAST\tDpl\t"nazwisko"\n')
            f.write(f'LAST\tDen\t"family name"\n')

    # zamrażanie słowników imion i nazwisk znalezionych w wikibase 
    if SAVE_DICT:
        with open(imiona_qid_pickle, 'wb') as handle:
            pickle.dump(IMIONA_QID, handle, protocol=pickle.HIGHEST_PROTOCOL)
        with open(nazwiska_qid_pickle, 'wb') as handle:
            pickle.dump(NAZWISKA_QID, handle, protocol=pickle.HIGHEST_PROTOCOL)
