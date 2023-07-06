""" poprawka pliku z unikalnymi miejscowościami """
import re


with open('../data_prng/miejsc_u_unique.txt','r',encoding='utf-8') as f:
    dane = f.read()

lista = re.split(r'\|\d{1,5}',dane)

with open('../data_prng/miejsc_u_unique.txt_new.txt','w',encoding='utf-8') as f:
    licznik = 1
    for item in lista:
        f.write(item + '|' + str(licznik) + '\n')
        licznik += 1
