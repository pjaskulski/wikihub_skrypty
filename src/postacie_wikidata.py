""" sprawdzenie dat urodzenia i śmierci """
import json
import os
import time
from pathlib import Path
from wikidariahtools import element_search_adv


# ----------------------------------- MAIN -------------------------------------

if __name__ == '__main__':

    label_en = 'Jan III Sobieski'
    parameters = ['P200', )]
    ok, item_id = element_search_adv(label_en, 'en', None, '', max_results_to_verify=500)

    # lista = []
    # with open('../data/postacie.json', "r", encoding='utf-8') as f:
    #     data = json.load(f)
    #     licznik = 0
    #     for i, person in enumerate(data['persons']):
    #             name = person['name']
    #             date_of_birth = person.get('date_of_birth','')
    #             date_of_death = person.get('date_of_death','')
    #             years = person.get('years','')
    #             if len(date_of_death) == 10:
    #                 d_date = date_of_death[6:]
    #             else:
    #                 if '-' in years:
    #                     tmp = years.split('-')
    #                     d_date = tmp[1].strip()
    #             break
    #             lista.append(name, date_of_death)

