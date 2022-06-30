# wikidariah_skrypty
Skrypty pomocnicze do importowania. modyfikacji i wyszukiwania danych w instancji Wikibase - WikiDARIAH 

## 1. proste przykłady:

- example_item_add.py: dodawanie nowego elementu (i deklaracji dla elementu)
- example_property.add.py: dodawanie nowej właściwości
- example_search.py: przykład wyszukiwania
- example_statement_add.py: dodawanie deklaracji do istniejącej właściwości
- example_statement_add_value.py: dodawanie kolejnej wartości do istniejącej deklaracji
- example_statement_edit.py: edycja istniejącej deklaracji w istniejącej właściwości
- example_statement_delete.py: usuwanie deklaracji z elementu (item)
- example_item_delete.py: usuwanie elementu
- bn_marc_artykuly.py: przykład dodawania serii elementów (artykuły z bibliografii udostępnionej
przez Bibliotekę Narodową), szybkość dodawana elementów na testowanej instancji wikibase - ok. 16-17 na minutę (1000/h).
- wikidariahtools: funkcje pomocnicze 

## 2. property_import.py

Skrypt wspomagający tworzenie właściwości (property) i elementów (item) w Wikibase (domyślnie w instancji wikibase WikiDARIAH[nazwa robocza]). Na podstawie zawartości arkuszy w formacie XLSX tworzy właściwości oraz dodaje do nich deklaracje (statement). W arkuszu **P_list** przetwarzanego pliku XLSX powinna znajdować się lista właściwości do dodania, w arkuszu **P_statements** powinna znajdować się lista dodatkowych deklaracji dla istniejących już właściwości. 

Skrypt obsługuje także możliwość dodawania elementów i deklaracji dla nich, z tym że chodzi raczej o tzw. elementy strukturalne/definicyjne  w rodzaju 'human settlement' będące częścią modeli danych dla osób, bibliografii, danych geo a nie będących konkretnymi bytami w rodzaju 'Kraków' czy 'Jan Zamojski'. W przykładowym pliku test.xlsx w folderze /data znajdują się arkusze **Q_list** i **Q_statments**.  

Celem prac nad tym skryptem nie jest stworzenie uniwersalnego systemu do importowania danych do Wikibase z poziomu Excela, tylko prostego narzędzia ułatwiającego tworzenie struktury właściwości według zaprojektowanego modelu danych dotyczącego np. postaci historycznych, bilbiografii, historycznej struktury osadniczej itp. Ponieważ jednak skrypt umożliwia dodawanie elementów Q wraz z deklaracjami (statement) technicznie możliwe jest dodawanie  za jego pomocą krótkich serii danych
(nie definicyjnych).

Dla maksymalnego uproszczenia przyjęto, że w przypadku właściwości (property) ich angielskie etykiety są w danej instancji Wikibase unikalne, podobnie w przypadu tzw. elementów (item) strukturalnych/definicyjnych, tu jednak przyjęto wyjątek - elementy posiadające identyfikator purl mogą mnieć nieunikalne etykiety. 

### Opis działania

Skrypt odczytuje zawartość pliku XLSX wskazanego jako parametr z linii komend np.:
```
python property_import.py data/test.xlsx
```
jeżeli nie podano ścieżki do pliku, szuka domyślnego: `data/arkusz_import.xlsx`

Aby import zadziałał poprawnie (posiadał dane logowania do wikibase) należy ustawić w pliku .env właściwe wartości zmiennych:
 - WIKIDARIAH_USER login użytkownika, który utworzył hasło bota (sam login, bez nazwy bota)
 - WIKIDARIAH_PWD hasło bota (przed hasłem nazwa bota oddzielona znakiem %)

Aby skrypt mógł wprowadzać i modyfikować dane użytkownik tworzący hasło bota w wikibase musi mieć nadane odpowiednie uprawnienia.

### Obsługa właściwości (property)

Plik XLSX, z którym współpracuje skrypt powinien posiadać arkusz o nazwie **P_list**, w którym 
znajdują się kolumny (obecnie 7):

- Label_en - etykieta ang.
- Label_pl - etykieta pl.
- Datatype - typ danych (string', 'wikibase-item', 'wikibase-property', 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate' - skrypt akcpetuje też nazwy alternatywne, zwyczajowe np. 'external identifier', 'monolingual text', 'geographic coordinates', 'point in time', 'item', 'property')
- Description_en - opis ang.
- Description_pl - opis pl.
- Wiki_id - identyfiktor odpowiednika właściwości w wikidata.org
- Inverse_property - odwrotna właściwość

Dwie ostatnie kolumny nie są wymagane, pierwszych pięć powinno być zdefiniowanych w arkuszu, jednak wypełnienie jest wymagane dla Label_en i Description_en (a w przypadku nieznanego tłumaczenia opisu na angielski - wymagane są kolumny Label_en i Label_pl), w każdym przypadku wymagany jest typ danych (kolumna datatype) - w przypadku braku wypełnienia wymaganych kolumn skrypt pominie dany wiersz arkusza). 

Jeżeli podano wartość 'Wiki_id' skrypt doda do nowej właściwości deklarację (statement) używając property 'Wikidata ID' (zakładając, że taka już istnieje np. została dodana jako jedna z pierwszych właściwości w arkuszu) oraz doda referencje do tej deklaracji korzystając z property 'reference URL' (również zakładając, że istnieje lub została dodana jako jedna z pierwszych) z wartością równą adresowi url utworzonemu na podstawie zawartości kolumny Wiki_id w arkuszu (np. dla 'P156' skrypt tworzy url równy 'https://www.wikidata.org/wiki/Property:P156'). 

Jeżeli podano wartość 'inverse_property', to właściwość będąca jej wartością automatycznie otrzyma  analogiczną właściwość 'odwrotną', np. jeżeli dodajemy właściwość 'followed by', dla której podaliśmy 'inverse_property' = 'follows' (P161) to skrypt utworzy także dla właścicowści P161 'follows' deklarację z właściwością 'inverse property' wskazującą na nowo dodaną właściwość 'followed by'.

W przypadku importu do całkowicie nowej i pustej instancji Wikibase należałoby więc w pierwszej kolejności umieścić w arkuszu 'P_list' właściwości 'Wikidata ID', 'reference URL', 'inverse property'.

Przykład zawartości arkusza:
```
architectural style | styl architektoniczny | wikibase-item | architectural style of a structure     | styl architektoniczny konstrukcji | P 149 | 
followed by         | następca              | wikibase-item | immediately following item in a series | następny element z serii          | P156  | 
follows             | poprzednik            | wikibase-item | immediately prior item in a series     | poprzedni element z serii         | P155  | followed by
```

**Uwaga**: istnienie arkuszy i kolumn o oczekiwanych nazwach jest weryfikowane przez skrypt.

Plik XLSX powinien też posiadać arkusz **P_statements**, w którym dla istniejących już właściwości P można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć trzy kolumny oraz dwie opcjonalne: 
- 'Label_en' - właściwość do której dodajemy deklarację (jej ang. etykieta lub numer P), 
- 'P' - właściwość, którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 
- 'Value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345. Skrypt rozpoznaje typ danych właściwości z kolumny 'P'. Obecnie obsługiwane typy danych: 'string', 'wikibase-property', 'wikibase-item', 'external-id', 'url', 'monolingualtext', 'quantity', 'time', 'url', 'globe-coordinate'.
- 'Reference_property' - właściwość referencji
- 'Reference_value' - wartość referencji

Dla właściwości o type danych 'globe-coordinate' należy wprowadzić wartość w formie 'latitude,longitude,precision' zgodnie z dokumentacją (https://www.wikidata.org/wiki/Help:Data_type#Globe_coordinate), np. '19.9,54.8,0.01', jeżeli wartość precision zostanie pominięta skrypt przyjmie domyślną wartość 0.1.

Dla właściwości o typie danych 'time' (https://www.wikidata.org/wiki/Help:Data_type#Time) należy wprowadzić wartość w standardzie ISO 8601 z określeniem precyzji daty po znaku / (0-14, zgodnie z opisem: https://www.wikidata.org/wiki/Special:ListDatatypes#time) np. 
'+1900-00-00T00:00:00Z/9' dla roku 1900. Skrypt zaakceptuje także krótszą formę daty np.: w formie 4 znakowego roku: 1525, w formie zwykłej daty 1525-04-11, także z samym miesiącem 1525-10, te krótsze formy skrypt automatycznie przekształca w zapis z precyzją.

Dla właściości typu 'wikibase-item' ('item') należy wprowadzić symbol Qxxx elementu (jeżeli jest znany) angielską etykietę elementu, lub identyfikator purl, który szukany element ma przypisany w formie deklaracji 'purl identifier'.

Przykład zawartości arkusza:
```
architectural style | refers to          | architecture   |      |
architectural style | related properties | painting style | P144 | Id_Testowe_0150 
P151                | P47                | Q703           |      |
```

W przypadku gdy podano ang. etykietę właściwości (property) lub elementu (item) która nie jest jednoznaczna, skrypt zgłosi problem wraz z listą identyfikatów elementów pasujących do podanej etykiety. W razie braku pasującej właściwości lub elementu zgłoszony zostanie tylko komunikat o braku właściwości. W obu przypadkach deklaracja nie zostanie utworzona. Można wówczas zmodyfikować zawartość arkusza wprowadzając zamiast ang. etykiety konkretny identyfikator P. 

Jeżeli podana w arkuszu 'P_list' właściwość już istnieje skrypt po wykryciu jej w wikibase
przechodzi w tryb aktualizacji i modyfikuje dane właściwości według zawartości kolumn w arkuszu (etykiety i opisy).
W przypadku deklaracji w arkuszu 'P_statements' skrypt weryfikuje i pomija już istniejące w wikibase dla danej właściwości deklaracje. 

Deklaracja właściwości może posiadać referencję złożoną z wielu właściwości ('blokową' referencję), jeżeli po wierszu z definicją deklaracji i pierwszej referencji będą dodane kolejne wiersze z pustymi kolumnami 'Label_en', 'P', 'Value' lecz z wypełnioną zawartością 'Reference_property', 'Reference_value' to skrypt przyjmie, że są to kolejne elementy definicji tej samej referencji i utworzy taką 'blokową' referencję np. https://prunus-208.man.poznan.pl/wiki/Property:P193.

### Obsługa elementów (item) strukturalnych/definicyjnych

Plik XLSX, z którym współpracuje skrypt powinien posiadać arkusz o nazwie **Q_list**, wówczas
podejmie próbę uzupełnienia Wikibase o elementy strukturalne/definicyjne. Obecnie obśługiwanych
jest w arkuszy Q_list 8 kolumn: 'Label_en', 'Label_pl', 'Description_en', 'Description_pl', 'Wiki_id', 'StartsAt', 'EndsAt', 'Instance of', z tego ostatnie 4 opcjonalnie. Opis kolumn:

- Label_en - etykieta ang.
- Label_pl - etykieta pl.
- Description_en - opis ang.
- Description_pl - opis pl.
- Wiki_id - (opcjonalnie) identyfiktor odpowiednika właściwości w wikidata.org (samo id w postaci Qxxx, skrypt sam utworzy adres url do referencji deklaracji), wypełnienie Wiki_id spowoduje utworenie deklaracji 'Wikidata ID' (typu external-id) z podaną wartością identyfikatora Q i referencją w formie url prowadzącego do elementu w serwisie wikidata.org.
- StartsAt (opcjonalnie) - jeżeli zostanie wypełniona skrypt utworzy deklarację 'starts at' typu 'time', zawartość powinna być datą w jednym akceptowanych (zob. wyżej) formatów.
- EndsAt (opcjonalnie) - jeżeli zostanie wypełniona skrypt utworzy deklarację 'ends at' typu 'time', zawartość powinna być datą w jednym akceptowanych (zob. wyżej) formatów.
- Instance of (opcjonalnie) - jeżeli zostanie wypełniona, skrypt utworzy deklarację 'instance of' ze wskazaniem na element znaleziony na podstawie zawartości kolumny (może to być symbol Qxxx elementu, jeżeli jest znany, angielska etykieta elementu, lub identyfikator purl który szukany element ma przypisany w formie deklaracji 'purl identifier').

Pola etykiet i pola opisów nie powinny zawierać więcej niż 1000 znaków - tyle obecnie obsługuje instancja Wikibase projektu DARIAH. 

Plik XLSX powinien też posiadać arkusz **Q_statments**, w którym dla istniejących już elementów Q można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć minimum trzy kolumny: 
- 'Label_en' - element do której dodajemy deklarację (jego ang. etykieta lub numer Q), 
- 'P' - właściwość, którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 
- 'Value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości właściwości jest item lub property można wprowadzić ich angielskie etykiety lub identyfikatory Q lub P.

Opcjonalnie można dodać do deklaracji kwalifikatory, służą do tego kolejne dwie kolumny:
- 'Qualifier' - etykieta właściwości która ma być kwalifikatorem (lub identyfikator P)
- 'Qualifier_value' - wartość kwalifikatora, w przypadku gdy ma to być np. element można podać jego ang. etykietę lub konkretny identyfikator Qxx (obsługiwany jest także identyfikator purl, jeżeli oczeiwany element ma przypisaną deklarację właściwości 'purl identifier'), dla kwalifikatorów typu String to będzie po prostu tekst, który stanie się zawartością kwalifikatora.

Deklaracja może zawierać wiele kwalifikatorów, jeżeli po wierszu z definicją deklaracji
i pierwszego kwalifikatora będą dodane kolejne wiersze z pustymi kolumnami 'Label_en', 'P', 'Value' lecz z wypełnioną zawartością 'Qualifier', 'Qualifier_value' to skrypt przyjmie że są to kolejne 
definicje kwalifikatorów do tej samej deklaracji.

Piątym arkuszem pliku XLSX powinien być arkusz **Globals** zawierający definicje tzw. referencji globalnych. Arkusz zawiera 3 kolumny: 'Sheets', 'Reference_property', 'Reference_value':
- 'Sheet' - nazwa arkusza np. 'Q_statements', dla którego będzie obowiązywała definicja referencji
- 'Reference property' - np. 'P186'
- 'Reference value' - np. 'Wielka Encyklopedia'

Wypełnienie arkusza jest opcjonalne (musi jednak istniejć i posiadać zdefiniowane kolumny). Jeżeli 
zostanie wypełniony to dla wskazanego arkusza, np. podczas importu deklaracji dla elementów Q, do wszystkich deklaracji zostanie podpięta referencja opisana w kolumnach 'Rerefence property', 'Reference value'. Nie dotyczy to jednak deklaracji właściwości typu external-id np. 'purl identifier' (które same w sobie są referencją). 


### TODO

- [x]  jeżeli dodano właściwość inverse_property, to właściwość będąca jej wartością powinna dostać odwrotnie analogiczną włąściwość
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
