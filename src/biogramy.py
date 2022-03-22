""" lista haseł PSB (biogramy zwane też 'rodziałami') -> QuickStatements """

import sys
import re
import pickle
import os
from pathlib import Path
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator.wbi_functions import search_entities


# adresy
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

P_INSTANCE_OF = 'P47'
P_PAGE = 'P168'
Q_CHAPTER = 'Q708'
P_PUBLISHED_IN = 'P167'
P_ISSUE = 'P169'
P_AUTHOR_SHORT_NAME = 'P180'
P_WRITTEN_BY = 'P105'
P_TITLE = 'P106'

PSB = {}
AUTORZY = {}


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
        exact_id = ''
        for qid in results:
            wikidata_item = wbi_core.ItemEngine(item_id=qid)
            data = wikidata_item.get_json_representation()
            value = data["labels"]["en"]["value"]
            if value == search_string:
                exact_id = qid
                break
        if exact_id:
            return True, exact_id
        else:
            return False, "NOT FOUND"


def get_last_nawias(line: str) -> str:
    """ zwraca zawartość ostatniego nawiasu """
    line = line.strip()
    start = stop = 0
    for i in range(len(line)-1, 0, -1):
        if line[i] == ")":
            stop = i
        elif line[i] == "(":
            start = i + 1

        if start and stop:
            result = line[start:stop]
            break

    return result, start - 1

def text_clear(value: str) -> str:
    """ text_clear """
    value = value.strip()
    if ' ' in value:
        value = ' '.join(value.strip().split())

    return value


if __name__ == "__main__":
    file_path = Path('.').parent / 'data/lista_hasel_PSB_2020.txt'
    output = Path('.').parent / 'out/biogramy.qs'
    psb_pickle = Path('.').parent / 'out/psb.pickle'
    autorzy_pickle = Path('.').parent / 'out/autorzy.pickle'

    # odmrażanie słowników 
    if os.path.isfile(psb_pickle):
        with open(psb_pickle, 'rb') as handle:
            PSB = pickle.load(handle)
    
    if os.path.isfile(autorzy_pickle):
        with open(autorzy_pickle, 'rb') as handle:
            AUTORZY = pickle.load(handle)    
    
    with open(file_path, "r", encoding='utf-8') as f:
        indeks = f.readlines()

    if not indeks:
        print('ERROR: empty index')
        sys.exit(1)

    with open(output, "w", encoding='utf-8') as o:
        for item in indeks:
            nawias, title_stop = get_last_nawias(item)
            title = item[:title_stop].strip()
            l_nawias = nawias.split(",")
            if len(l_nawias) != 4:
                print(f'ERROR: {l_nawias}')
                sys.exit(1)
            autor = text_clear(l_nawias[0])
            tom = text_clear(l_nawias[1])
            tom = tom.replace("t.","").strip()
            rok = text_clear(l_nawias[2])
            strony = text_clear(l_nawias[3])
            if "-" in strony:
                strony_ang = strony.replace("s.", "pp.")
            else:
                strony_ang = strony.replace("s.", "p.")
            nr_strony = strony.replace("s.", "").strip()

            if "na podstawie" in autor:
                l_autor = [autor]
            elif "Wojewódzka Żydowska" in autor:
                l_autor = [autor]
            else:
                l_autor = re.split(';| i ', autor)
                l_autor = [item.strip() for item in l_autor]

            print(title)

            # zapis w pliku quick_statements
            o.write('CREATE\n')

            # etykiety
            o.write(f'LAST\tLpl\t"{autor}, {title}, w: PSB {tom}, {strony}"\n')
            o.write(f'LAST\tLen\t"{autor}, {title}, in: PSB {tom}, {strony_ang}"\n')

            # jest to
            o.write(f'LAST\t{P_INSTANCE_OF}\t{Q_CHAPTER}\n')

            # autor, autorzy
            for t_autor in l_autor:
                if "na podstawie" in t_autor or "Wojewódzka Żydowska" in t_autor:
                    o.write(f'LAST\t{P_AUTHOR_SHORT_NAME}\t"Red."\n')
                elif "Wojewódzka Żydowska" in t_autor:
                    o.write(f'LAST\t{P_AUTHOR_SHORT_NAME}\t"{t_autor}"\n')
                else:
                    if t_autor in AUTORZY:
                        autor_qid = AUTORZY[t_autor]
                        ok = True
                    else:
                        ok, autor_qid = element_search(f"{t_autor}", 'item', 'en')
                        if ok:
                            AUTORZY[t_autor] = autor_qid

                    if ok:
                        o.write(f'LAST\t{P_WRITTEN_BY}\t{autor_qid}\n')
                    else:
                        t_autor = "{Q:" + t_autor + "}"
                        o.write(f'LAST\t{P_WRITTEN_BY}\t{t_autor}\n')

            #tytuł
            o.write(f'LAST\t{P_TITLE}\tpl:"{title}"\n')

            # opublikowano w
            if tom in PSB:
                tom_qid = PSB[tom]
                ok = True
            else:
                ok, tom_qid = element_search(f"PSB {tom}", 'item', 'en')
                if ok: 
                    PSB[tom] = tom_qid

            if ok:
                o.write(f'LAST\t{P_PUBLISHED_IN}\t{tom_qid}\n')
            else:
                print(f"ERROR: tom PSB {tom}, {tom_qid}")
            # nr stron
            o.write(f'LAST\t{P_PAGE}\t"{nr_strony}"\n')

    # zamrażanie słowników 
    with open(psb_pickle, 'wb') as handle:
        pickle.dump(PSB, handle, protocol=pickle.HIGHEST_PROTOCOL)
    
    with open(autorzy_pickle, 'wb') as handle:
        pickle.dump(AUTORZY, handle, protocol=pickle.HIGHEST_PROTOCOL)
    