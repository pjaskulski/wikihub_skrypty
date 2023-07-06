
with open('../data_prng/miejscowosci_u_qid.txt','r',encoding='utf-8') as f:
    dane = f.read()

with open('../data_prng/miejscowosci_u_qid_new.txt','w',encoding='utf-8') as f:
    licznik = 0
    linia = ''
    for znak in dane:
        linia += znak
        if znak == ';':
            licznik = 0
        else:
            licznik += 1
        if licznik == 7:
            f.write(linia + '\n')
            linia = ''
            licznik = 0

    f.write(linia + '\n')
