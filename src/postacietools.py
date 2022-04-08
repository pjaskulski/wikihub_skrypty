""" moduł """
import re
import roman as romenum
from wyjatki_postacie import WYJATKI

class DateBDF:
    """ obługa daty urodzenia, śmierci lub flourit """

    P_DATE_OF_BIRTH = 'P7'
    P_DATE_OF_DEATH = 'P8'
    P_EARLIEST_DATE = 'P38'
    P_LATEST_DATE = 'P39'
    P_FLORUIT = 'P54'
    Q_CIRCA = 'Q37979'
    P_SOURCING_CIRCUMSTANCES = 'P189'
    P_REFINE_DATE = 'P190'
    Q_FIRST_HALF = 'Q40688'
    Q_SECOND_HALF = 'Q41336'
    Q_BEGINNING_OF = 'Q41337'
    Q_MIDDLE_OF = 'Q41338'
    Q_END_OF = 'Q41339'
    Q_FIRST_QUARTER = 'Q49427'

    def __init__(self, text:str, typ:str = '') -> None:
        """ init """
        self.text_org = text
        self.text = text.strip().lower()
        self.type = typ
        self.date = ''
        self.date_2 = ''
        self.about = False
        self.between = False
        self.or_date = False
        self.turn = False
        self.before = False
        self.after = False
        self.certain = False
        self.first_half = False
        self.second_half = False
        self.beginning_of = False
        self.middle_of = False
        self.end_of = False
        self.first_quarter = False
        self.somevalue = False
        self.roman = self.roman_numeric()
        if not self.type:
            self.find_type()
        self.find_uncertainty()
        self.find_date()
        if not self.certain and (self.before or self.after or self.between):
            self.somevalue = True


    def find_type(self):
        """ ustala typ daty """
        if 'zm.' in self.text or 'zmarł' in self.text:
            self.type = 'D'
        elif 'um.' in self.text:
            self.type = 'D'
        elif 'ur.' in self.text:
            self.type = 'B'
        else:
            self.type = 'F'


    def find_uncertainty(self):
        """ ustala czy jest i jaka niepewność dla daty """

        tmp = self.text.replace('zm.', '').replace('um.', '').replace('ur.', '').strip()
        if tmp.isnumeric():
            self.certain = True

        if 'prawdopodobnie' in self.text:
            self.about = True

        if 'ok.' in self.text or 'około' in self.text or 'ok ' in self.text:
            self.about = True

        if 'między' in self.text or 'miedzy' in self.text:
            self.between = True

        if 'w okresie II wojny światowej' in self.text_org:
            self.between = True

        if 'lub nieco później' in self.text:
            self.after = True

        if 'w/przed' in self.text:
            self.before = True

        if 'przed lub w' in self.text:
            self.before = True

        if 'w lub po' in self.text or 'po lub w' in self.text:
            self.after = True

        if ('prawdopodobnie' in self.text or 'zapewne' in self.text 
            or 'rzekomo' in self.text):
            self.about = True

        if ('lub' in self.text and not 'po ' in self.text
               and not ' w ' in self.text and not 'przed ' in self.text
               and not 'nieco później' in self.text):
            self.or_date = True

        if 'przed ' in self.text:
            self.before = True

        if 'po ' in self.text:
            self.after = True

        if 'nie później niż' in self.text:
            self.before = True

        if 'najpóźniej' in self.text:
            self.before = True

        # niepewność
        if '?' in self.text:
            self.about = True

        # przełom lat
        match = re.search(r'\d{3,4}/\d{1,2}', self.text)
        if match:
            self.turn = True

        if '1 poł.' in self.text or 'i poł.' in self.text or '1. poł.' in self.text:
            self.first_half = True
        elif '2 poł.' in self.text or 'ii poł.' in self.text or '2. poł.' in self.text:
            self.second_half = True
        elif '1. ćwierć' in self.text:
            self.first_quarter = True
        elif 'pocz.' in self.text:
            self.beginning_of = True
        elif 'koniec' in self.text or 'w końcu' in self.text:
            self.end_of = True


    def roman_numeric(self) -> bool:
        """ czy liczba rzymska?"""
        pattern = r'[IVX]{1,5}\s+w\.{0,1}'
        match = re.search(pattern, self.text_org)
        if not match:
            pattern = r'[IVX]{1,5}'
            match = re.search(pattern, self.text_org)

        return bool(match)

    def find_date(self):
        """ wyszukuje daty """
        # XVI w.
        if self.roman: 
            matches = [x.group() for x in re.finditer(r'[IVX]{1,5}', self.text_org)]
            if len(matches) == 1:
                self.date = str(romenum.fromRoman(matches[0]))
            elif len(matches) == 2:
                matches = [str(romenum.fromRoman(x)) for x in matches]
                self.date = matches[0]
                self.date_2 = matches[1]
        # 1523/4
        elif self.turn:
            match = re.search(r'\d{3,4}/\d{1,2}', self.text)
            if match:
                v_list = match.group().split('/')
                v_list1 = v_list[0].strip()
                v_list2 = v_list1[:len(v_list1)-len(v_list[1].strip())] + v_list[1].strip()
                self.date = v_list1
                self.date_2 = v_list2
        # zwykłe daty (jeszcze obsługa dat dziennych i miesięcznych do zrobienia)
        else:
            if 'w okresie II wojny światowej' in self.text_org:
                self.date = '1939'
                self.date_2 = '1945'
            else:
                pattern = r'\d{3,4}'
                matches = [x.group() for x in re.finditer(pattern, self.text)]
                if len(matches) == 1:
                    self.date = matches[0]
                elif len(matches) > 1:
                    self.date = matches[0]
                    self.date_2 = matches[1]


    def _format_date(self, value: str) -> str:
        """ formatuje datę na sposób oczekiwany przez QuickStatements
            np. +1839-00-00T00:00:00Z/9
        """
        result = ''
        if len(value) == 4:                          # tylko rok
            result = f"+{value}-00-00T00:00:00Z/9"
        elif len(value) == 10:                       # dokłada data
            result = f"+{value}T00:00:00Z/11"
        elif len(value) == 2 and value.isnumeric():  # wiek
            result = f"+{str(int(value)-1)}01-00-00T00:00:00Z/7"
        elif len(value) == 1 and value.isnumeric():  # wiek np. X
            value = str(int(value)-1)
            result = f"+{value.zfill(2)}01-00-00T00:00:00Z/7"

        return result

    def prepare_qs(self, etykieta: str = '') -> str:
        """ drukuje zapisy QuickStatements"""
        # data urodzin
        print_date = print_date_2 = print_kw_date = print_kw_date_2 = ''
        if self.somevalue:
            print_date = 'somevalue'
            print_kw_date = self._format_date(self.date)
            print_kw_date_2 = self._format_date(self.date_2)
        else:
            print_date = self._format_date(self.date)
            if self.or_date or self.turn:
                print_date_2 = self._format_date(self.date_2)

        if self.type == 'B':
            print_type = self.P_DATE_OF_BIRTH
        elif self.type == 'D':
            print_type = self.P_DATE_OF_DEATH
        elif self.type == 'F':
            print_type = self.P_FLORUIT
        else:
            print('ERROR: nieokreślony typ daty.')

        if print_date == 'somevalue':
            qid = etykieta
        else:
            qid = 'LAST'

        line = f'{qid}\t{print_type}\t{print_date}'
        if self.about:
            line += f'\t{self.P_SOURCING_CIRCUMSTANCES}\t{self.Q_CIRCA}'
        if self.or_date:
            line += '\n'
            line += f'{qid}\t{print_type}\t{print_date_2}'
        if self.turn:
            line += '\n'
            line += f'{qid}\t{print_type}\t{print_date_2}'
        if self.after:
            line += f'\t{self.P_EARLIEST_DATE}\t{print_kw_date}'
        if self.before:
            line += f'\t{self.P_LATEST_DATE}\t{print_kw_date}'
        if self.between:
            line += f'\t{self.P_EARLIEST_DATE}\t{print_kw_date}'
            line += f'\t{self.P_LATEST_DATE}\t{print_kw_date_2}'
        if self.beginning_of:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_BEGINNING_OF}'
        if self.middle_of:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_MIDDLE_OF}'
        if self.end_of:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_END_OF}'
        if self.first_half:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_FIRST_HALF}'
        if self.second_half:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_SECOND_HALF}'
        if self.first_quarter:
            line += f'\t{self.P_REFINE_DATE}\t{self.Q_FIRST_QUARTER}'

        line += '\n'
        return line


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
            if (tmp[1].endswith('ski') or tmp[1].endswith('icz')
                or tmp[1].endswith('ska') or tmp[1].endswith('iczowa')
                or tmp[1].endswith('zic')):
                p_imie = tmp[2]
            elif tmp[2].endswith('wic') or tmp[2].endswith('yc'): # Januszowski Jan Łazarzowic
                p_imie = tmp[1]
            else:
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
    # zazwyczaj za taką liczbą jest przydomek, więc pomijam
    roman = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 
             'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']

    is_roman = False
    for i, tmp_value in enumerate(tmp):
        tmp_value = tmp_value.strip()
        if tmp_value in roman:
            is_roman = True
        if is_roman:
            tmp[i] = ''

    tmp = [item for item in tmp if item.strip() != '']

    if len(tmp) == 1:
        # czy to imię czy nazwisko? Dodać słownik typowych imion? na razie wszystkie
        # pojedyncze traktowane są jak imiona, chyba że kończy się na 'ski'
        p_word = tmp[0].strip()
        if p_word.endswith('ski') or p_word.endswith('ska') or p_word.endswith('cki'):
            p_nazwisko = p_word
        else:
            p_imie = p_word

    elif len(tmp) == 2:
        if tmp[0][0].isupper() and tmp[1][0].isupper():
            p_nazwisko = tmp[0].strip()
            p_imie = tmp[1].strip()

    elif len(tmp) == 3:
        if tmp[0][0].isupper() and tmp[1][0].isupper() and tmp[2][0].isupper():
            p_nazwisko = tmp[0].strip()
            if (tmp[1].endswith('ski') or tmp[1].endswith('icz')
                or tmp[1].endswith('ska') or tmp[1].endswith('iczowa')
                or tmp[1].endswith('zic')):
                p_imie = tmp[2]
            elif tmp[2].endswith('wic') or tmp[2].endswith('yc'): # Januszowski Jan Łazarzowic
                p_imie = tmp[1]
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

    # jeżeli imię zaczyna się z małej litery, to błędnie rozpoznano i to nie jest imię
    if p_imie and p_imie[0].islower():
        p_imie = ''
    if p_imie2 and p_imie2[0].islower():
        p_imie2 = ''
    if p_imie3 and p_imie3[0].islower():
        p_imie3 = ''
    if p_imie4 and p_imie4[0].islower():
        p_imie4 = ''

    if not p_imie and not p_nazwisko: 
        print(f'PROBLEM: {original_value}')

    return p_nazwisko, p_imie, p_imie2, p_nazwisko2, p_imie3, p_imie4
