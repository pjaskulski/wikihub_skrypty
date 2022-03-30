""" """
from wyjatki_postacie import WYJATKI


def get_name_simple(value: str) -> tuple:
    """ get name simple """
    p_nazwisko = p_imie = p_imie2 = ''

    tmp = value.split(" ")
    if len(tmp) == 1:
        p_imie = tmp[0].strip()
    elif len(tmp) == 2:
        if tmp[0][0].isupper() and tmp[1][0].isupper():
            p_nazwisko = tmp[0].strip()
            p_imie = tmp[1].strip()
    elif len(tmp) == 3:
        if tmp[0][0].isupper() and tmp[1][0].isupper() and tmp[2][0].isupper():
            p_nazwisko = tmp[0].strip()
            p_imie = tmp[1].strip()
            p_imie2 = tmp[2].strip()

    return p_nazwisko, p_imie, p_imie2


def get_name(value: str) -> tuple:
    """ get_name """
    p_imie = p_imie2 = p_imie3 = p_imie4 = p_nazwisko = p_nazwisko2 = ''
    original_value = value

    lista = ['(młodszy)', '(starszy)', '(Młodszy)', '(Starszy)',
             'młodszy', 'starszy', 'Młodszy', 'Starszy', 'junior', 'senior',
             'właśc.', 'jr']
    for item in lista:
        if item in value:
            value = value.replace(item, '').strip()

    # jeżeli postać jest w wyjątkach to funkcja zwraca wartości z tablicy wyjątków
    if value in WYJATKI:
        if 'imie' in WYJATKI[value]:
            p_imie = WYJATKI[value]['imie'].strip()
        if 'imie2' in WYJATKI[value]:
            p_imie2 = WYJATKI[value]['imie2'].strip()
        if 'imie3' in WYJATKI[value]:
            p_imie3 = WYJATKI[value]['imie3'].strip() 
        if 'imie4' in WYJATKI[value]:
            p_imie4 = WYJATKI[value]['imie4'].strip()       
        if 'nazwisko' in WYJATKI[value]:
            p_nazwisko = WYJATKI[value]['nazwisko'].strip()
        if 'nazwisko2' in WYJATKI[value]:
            p_nazwisko2 = WYJATKI[value]['nazwisko2'].strip()
              
        return p_nazwisko, p_imie, p_imie2, p_nazwisko2, p_imie3, p_imie4

    tmp = value.strip().split(" ")

    # liczby rzymskie w przypadku władców - nie są imionami i nazwiskami
    roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 
             'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']

    for i in range(0, len(tmp)):
        tmp[i] = tmp[i].strip()
        if tmp[i] in roman:
            tmp[i] = ''
    
    for item in tmp:
        if item.strip() == '':
            tmp.remove(item)

    if len(tmp) == 1:
        # czy to imię czy nazwisko? Dodać słownik typowych imion? na razie wszystkie 
        # pojedyncze traktowane są jak imiona
        p_imie = tmp[0].strip()

    elif len(tmp) == 2:
        if tmp[0][0].isupper() and tmp[1][0].isupper():
            p_nazwisko = tmp[0].strip()
            p_imie = tmp[1].strip()

    elif len(tmp) == 3:
        if tmp[0][0].isupper() and tmp[1][0].isupper() and tmp[2][0].isupper():
            p_nazwisko = tmp[0].strip()
            if tmp[1].endswith('ski') or tmp[1].endswith('icz') or tmp[1].endswith('ska') or tmp[1].endswith('iczowa'):
                p_nazwisko2 = tmp[1]
                p_imie = tmp[2]
            else:
                p_imie = tmp[1]
                p_imie2 = tmp[2]
        else:
            if ' z ' in value or ' ze ' in value: # Szymon ze Stawu
                p_imie = tmp[0].strip()
            if (' zw. ' in value or 'zwany' in value or 'zapewne' in value 
                  or ' z ' in value or ' ze ' in value or ' w zak. ' in value
                  or ' zak. ' in value or ' syn ' in value):
                pos = value.find(' zw. ')
                pos1 = value.find(' zwany') 
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1
                pos1 = value.find(' zapewne ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1     
                pos1 = value.find(' z ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1    
                pos1 = value.find(' ze ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1
                pos1 = value.find(' w zak. ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1    
                pos1 = value.find(' zal. ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1
                pos1 = value.find(' syn ')
                if pos1 > 0 and (pos == -1 or pos1 < pos):
                    pos = pos1
                if pos != -1:
                    value = value[:pos].strip().replace(',', '')
                    p_nazwisko, p_imie, p_imie2 = get_name_simple(value)
            elif tmp[1] == 'de':  # Camelin de Jan
                p_nazwisko = tmp[1] + ' ' + tmp[0].strip()
                p_imie = tmp[2]
            elif tmp[-1] == 'de':  # Girard Filip de
                p_nazwisko = tmp[-1] + ' ' + tmp[0].strip()
                p_imie = tmp[1]
            elif tmp[-1] == 'von': # Kempen Eggert von
                p_nazwisko = tmp[-1] + ' ' + tmp[0].strip()
                p_imie = tmp[1]
            elif tmp[1] == 'del':  # Pace del Luca
                p_nazwisko = tmp[1] + ' ' + tmp[0].strip()
                p_imie = tmp[2]

    else:
        if ' de ' in value:
            p_imie = tmp[-1].strip()
            p_nazwisko = ' '.join(tmp[:-1])
        elif ' z ' in value or ' ze ' in value or ' zw. ' in value or 'syn' in value:  
            # Boner Seweryn z Balic, Abraham ben Joszijahu z Trok, Łukasz z Nowego Miasta
            pos = value.find(' z ')
            pos1 = value.find(' ze ')
            if pos1 > 0 and (pos == -1 or pos1 < pos):
                pos = pos1
            pos1 = value.find(' zw. ')
            if pos1 > 0 and (pos == -1 or pos1 < pos):
                pos = pos1
            pos1 = value.find(' syn ')
            if pos1 > 0 and (pos == -1 or pos1 < pos):
                pos = pos1    
            
            if pos != -1:
                value = value[:pos].strip()
                tmp = value.split(" ")
                p_nazwisko, p_imie, p_imie2 = get_name_simple(value)        
        elif tmp[-1] == 'de':  # Caraccioli Ludwik Antoni de
            p_nazwisko = tmp[-1] + ' ' + tmp[0].strip()
            p_imie = tmp[1]
            p_imie2 = tmp[2]
        elif 'van der' in value and len(tmp) == 4:
            p_nazwisko = 'van der' + ' ' + tmp[0].strip()
            p_imie = tmp[-1].strip()
        elif 'w zakonie' in value or 'w zak.' in value or ' zak. ' in value:
            pos = value.find(' w zak')
            pos1 = value.find(' zak. ')
            if pos1 > 0 and (pos == -1 or pos1 < pos):
                pos = pos1
            if pos != -1:
                value = value[:pos].strip().replace(',', '')
                p_nazwisko, p_imie, p_imie2 = get_name_simple(value)
        else:
            if len(tmp) == 4:
                p_nazwisko = tmp[0]
                if tmp[1].endswith('ski') or tmp[1].endswith('icz') or tmp[1].endswith('ska') or tmp[1].endswith('iczowa'):
                    p_nazwisko2 = tmp[1]
                    p_imie = tmp[2]
                    p_imie2 = tmp[3]
                else:
                    p_imie = tmp[1]
                    p_imie2 = tmp[2]
                    p_imie3 = tmp[3]

    # zakładam że otczewstwo to nie imię     
    if p_imie2.endswith('icz') or p_imie2.endswith('cki'):
        p_imie2 = ''
    if p_imie3.endswith('icz') or p_imie3.endswith('cki'):
        p_imie3 = ''
    if p_imie2 == 'ben':
        p_imie2 = ''
    if p_imie3 == 'ben':
        p_imie3 = ''

    if not p_imie and not p_nazwisko: 
        print(f'PROBLEM: {original_value}')
    
    return p_nazwisko, p_imie, p_imie2, p_nazwisko2, p_imie3, p_imie4
