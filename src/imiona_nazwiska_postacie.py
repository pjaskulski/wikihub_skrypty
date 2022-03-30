""" indeks BB -> imiona i nazwiska do QuickStatements """

import sys
import os
import pickle
from time import sleep
from pathlib import Path
from openpyxl import load_workbook
from wikibaseintegrator.wbi_config import config as wbi_config
from wikidariahtools import element_search, get_last_nawias
from postacietools import get_name


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
        name = imie = imie2 = imie3 = imie4 = nazwisko = nazwisko2 = ''

        start = title.find('(')
        if start != -1:
            name = title[:start].strip()
        else:
            name = title.strip()  # jeżeli nie ma nawiasu z latami życia

        print(f'Przetwarzanie: {name}')
        nazwisko, imie, imie2, nazwisko2, imie3, imie4 = get_name(name)
        
        if imie and not imie in IMIONA and not is_inicial(imie) and len(imie) > 1:
            IMIONA.append(imie)

        if imie2 and not imie2 in IMIONA and not is_inicial(imie2) and len(imie2) > 1:
            IMIONA.append(imie2)

        if imie3 and not imie3 in IMIONA and not is_inicial(imie3) and len(imie3) > 1:
            IMIONA.append(imie3)

        if imie4 and not imie4 in IMIONA and not is_inicial(imie4) and len(imie4) > 1:
            IMIONA.append(imie4)

        if nazwisko and not nazwisko in NAZWISKA and len(nazwisko) > 1:
            NAZWISKA.append(nazwisko)
        
        if nazwisko2 and not nazwisko2 in NAZWISKA and len(nazwisko2) > 1:
            NAZWISKA.append(nazwisko2)

    # weryfikacja imion w wikibase
    for imie in IMIONA:
        print(f'Weryfikacja imienia: {imie}')
        if imie in IMIONA_QID:
            ok = True
            qid = IMIONA_QID[imie]
        else:   
            #sleep(0.05) # mały odstęp między poszukiwaniami
            #ok, qid = element_search(imie, 'item', 'pl', description='imię')
            ok = False
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
            qid = NAZWISKA_QID[nazwisko]
        else: 
            #sleep(0.05) # mały odstęp między poszukiwaniami
            #ok, qid = element_search(nazwisko, 'item', 'pl', description='nazwisko')
            ok = False
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
