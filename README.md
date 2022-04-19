# wikidariah_skrypty
Skrypty pomocnicze do importowania. modyfikacji i wyszukiwania danych w instancji Wikibase - WikiDARIAH 

## 1. proste przykłady:

- example_item_add.py: dodawanie nowego elementu (i deklaracji dla elementu)
- example_property.add.py: dodawanie nowej właściwości
- example_search.py: przykład wyszukiwania
- example_statement_add.py: dodawanie deklaracji do istniejącej właściwości
- example_statement_edit.py: edycja istniejącej deklaracji w istniejącej właściwości
- wikidariahtools: funkcje pomocnicze 

## 2. property_import.py

Skrypt wspomagający tworzenie właściwości w Wikibase (domyślnie w instancji wikibase WikiDARIAH). Na podstawie zawartości arkuszy w formacie XLSX tworzy właściwości oraz dodaje do nich deklaracje. W arkuszu P_list przetwarzanego pliku XLSX powinna znajdować się lista właściwości do dodania, w arkuszu P_statements powinna znajdować się lista dodatkowych deklaracji dla istniejących już właściwości. 

W przyszłości skrypt będzie mógł obsługować także tzw. definicyjne elementy (item) w rodzaju 'human settlement' będące częścią modeli danych dla osób, bibliografii, danych geo a nie będących konkretnymi bytami w rodzaju 'Kraków' czy 'Jan Zamojski' (w przykładowym pliku test.xlsx w folderze data znajdują się już arkusze Q_list i Q_statments, ale ich struktura może się jeszcze zmienić).  

Celem prac nad tym skryptem nie jest stworzenie skomplikowanego systemu do zarządzania Wikibase z poziomu Excela, tylko prostego narzędzia ułatwiającego tworzenie struktury właściwości według zaprojektowanego modelu danych dotyczącego np. postaci historycznych, bilbiografii, historycznej struktury osadniczej itp.  

Dla maksymalnego uproszczenia przyjęto, że w przypadku właściwości (property) ich angielskie etykiety są w danej instancji Wikibase unikalne, podobnie w przypadu tzw. elementów (item) definicyjnych. 

### Opis działania

Skrypt odczytuje zawartość pliku XLSX wskazanego jako parametr z linii komend np.:
```
python property_import.py data/test.xlsx
```
jeżeli nie podano ścieżki do pliku, szuka domyślnego: `data/arkusz_import.xlsx`

Aby import zadziałał poprawnie należy ustawić w pliku .env właściwe wartości zmiennych:
 - WIKIDARIAH_USER login użytkownika, który utworzył hasło bota (sam login, bez nazwy bota)
 - WIKIDARIAH_PWD hasło bota (przed hasłem nazwa bota oddzielona znakiem %)

Aby skrypt mógł wprowadzać i modyfikować dane użytkownik tworzący hasło bota w wikibase musi mieć nadane odpowiednie uprawnienia.

Plik XLSX, z którym współpracuje skrypt powinien posiadać arkusz o nazwie **P_list**, w którym 
znajdują się kolumny (obecnie 7):

- Label_en - etykieta ang.
- Label_pl - etykieta pl.
- datatype - typ danych (string', 'wikibase-item', 'wikibase-property', 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate')
- Description_en - opis ang.
- Description_pl - opis pl.
- Wiki_id - identyfiktor odpowiednika właściwości w wikidata.org
- inverse_property - odwrotna właściwość

Dwie ostatnie nie są wymagane. Jeżeli podano wartość 'Wiki_id' skrypt doda do nowej właściwości deklarację (statement) używając property 'Wikidata ID' (zakładając, że taka już istnieje np. została dodana jako jedna z pierwszych właściwości w arkuszu) oraz doda referencje do tej deklaracji korzystając z property 'Wikidata URL' (również zakładając, że istnieje lub została dodana jako jedna z pierwszych) z wartością równą adresowi url utworzonemu na podstawie zawartości kolumny Wiki_id w arkuszu (np. dla 'P156' skrypt tworzy url równy 'https://www.wikidata.org/wiki/Property:P156'). 

Jeżeli podano wartość 'inverse_property', to właściwość będąca jej wartością automatycznie otrzyma  analogiczną właściwość 'odwrotną', np. jeżeli dodajemy właściwość 'followed by', dla której podaliśmy 'inverse_property' = 'follows' (P161) to skrypt utworzy także dla właścicowści P161 'follows' deklarację z właściwością 'inverse property' wskazującą na nowo dodaną właściwość 'followed by'.

W przypadku importu do całkowicie nowej i pustej instancji Wikibase należałoby więc w pierwszej kolejności umieścić w arkuszu 'P_list' właściowości 'Wikidata ID', 'Wikidata URL', 'inverse property'.

Przykład zawartości arkusza:
```
architectural style | styl architektoniczny | wikibase-item | architectural style of a structure     | styl architektoniczny konstrukcji | P 149 | 
followed by         | następca              | wikibase-item | immediately following item in a series | następny element z serii          | P156  | 
follows             | poprzednik            | wikibase-item | immediately prior item in a series     | poprzedni element z serii         | P155  | followed by
```

Istnienie arkuszy i kolumn o oczekiwanych nazwach jest weryfikowane przez skrypt.

Plik XLSX powinien też posiadać arkusz **P_statments**, w którym dla istniejących już właściwości P można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć trzy kolumny: 
- 'Label_en' - właściwość do której dodajemy deklarację (jej ang. etykieta lub numer P), 
- 'P' - właściwość, którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 
- 'value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345. Skrypt rozpoznaje typ danych właściwości z kolumny 'P'. Obecnie obsługiwane typy danych: 'string', 'wikibase-property', 'wikibase-item', 'external-id', 'url', 'monolingualtext', 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate'.
- 'reference_property' - właściwość referencji
- 'reference_value' - wartość referencji

Dla właściwości o type danych 'globe-coordinate' należy wprowadzić wartość w formie 'latitude,longitude,precision' zgodnie z dokumentacją (https://www.wikidata.org/wiki/Help:Data_type#Globe_coordinate), np. '19.9,54.8,0.01', jeżeli wartość precision zostanie pominięta skrypt przyjmie domyślną wartość 0.1.

Dla właściwości o typie danych 'time' (https://www.wikidata.org/wiki/Help:Data_type#Time) należy wprowadzić wartość w standardzie ISO 8601 z określeniem precyzji daty po znaku / (0-14, zgodnie z opisem: https://www.wikidata.org/wiki/Special:ListDatatypes#time) np. 
'+1900-00-00T00:00:00Z/9' dla roku 1900.

Przykład zawartości arkusza:
```
architectural style | refers to          | architecture   |      |
architectural style | related properties | painting style | P144 | Id_Testowe_0150 
P151                | P47                | Q703           |      |
```

W przypadku gdy podano ang. etykietę właściwości (property) lub elementu (item) która nie jest jednoznaczna, skrypt zgłosi problem wraz z listą identyfikatów elementów pasujących do podanej etykiety. W razie braku pasującej właściwości lub elementu zgłoszony zostanie tylko komunikat o braku właściwości. W obu przypadkach deklaracja nie zostanie utworzona. Można wówczas zmodyfikować zawartość arkusza wprowadzając zamiast ang. etykiety konkretny identyfikato P. 

Jeżeli podana w arkuszu 'P_list' właściwość już istnieje skrypt po wykryciu jej w wikibase
przechodzi w tryb aktualizacji i modyfikuje dane właściwości według zawartości kolumn w arkuszu (etykiety i opisy).
W przypadku deklaracji w arkuszu 'P_statements' skrypt weryfikuje i pomija już istniejące w wikibase dla danej właściwości deklaracje. 

### TODO

- [x]  jeżeli dodano właściwość inverse_property, to właściwość będąca jej wartością powinna dostać odwrotnie analogiczną włąściwość
- [ ]  wyszukiwanie P/Q w wikibase bez względu na wielkość liter
- [x]  modyfikacja istniejących właściwości
- [x]  druga zakładka (P_statements): obsługa referencji
- [x]  dodać obsługę pozostałych typów danych podczas dodawania deklaracji (statements): 'quantity', 'time', 'geo-shape', 'globe-coordinate' 

## 3. Imiona Nazwiska

imiona_nazwiska.py - skrypt do generowania zapisów w formacie QuickStatements V1 z listy autorów biogramów PSB utworzonej na podstawie indeksu biogramów PSB, tworzy listę imion i nazwisk autorów, które będą zaimportowane do Wikibase jako elementy. 

## 4. Autorzy

autorzy.py - skrypt do generowania zapisów w formacie QuickStatements V1 z listy autorów biogramów PSB utworzonej na podstawie indeksu biogramów PSB, tworzy listę autorów do zaimportowania w Wikibase.

## 5. Biogramy

biogramy.py - skrypt do generowania zapisów w formacie QuickStatements V1 z indeksu biogramów PSB, tworzy listę biogramów postaci historycznych do zaimportowania do Wikibase.

## 6. Imiona Nazwiska Postacie

imiona_nazwiska_postacie.py - skrypt do generowania zapisów w formacie QuickStatements V1 z listy autorów biogramów PSB, tworzy listę imion i nazwisk postaci, które będą zaimportowane do Wikibase jako elementy.

## 7. Postacie

postacie.py - skrypt do generowania zapisów w formacie QuickStatements V1 z indeksu biogramów PSB - tworzy listę postaci historycznych do zaimportowania do Wikibase.
