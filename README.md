# wikihub_skrypty
Skrypty pomocnicze do importowania. modyfikacji i wyszukiwania danych w instancji Wikibase - WikiHUB 

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

### Jak wprowadzać modele danych do arkuszy XLSX.

Model danych Wikibase składa się z właściwości (property) i elementów (item) opisujących wybrany fragment rzeczywistości np. osoby, miejscowości, publikacje. Aby ułatwić wprowadzanie i uzupełnianie modelu opracowany został mechanizm składający się ze skryptu w języku Python i pliku XLSX o określonej zawartości. Skrypt obsługuje import danych z pliku XLSX do wskazanej instancji Wikibase. Plik XLSX zawiera 5 arkuszy w których zapisane powinny być listy: właściwości, dodatkowych cech (deklaracji - statements) właściwości, elementów i dodatkowych cech (deklaracji - statements) elementów. Piąty arkusz zawiera tzw. definicje globalne, ułatwiające wprowadzanie powtarzających się referencji. 

![Lista arkuszy](/doc/lista_arkuszy_w_pliku_xlsx.png)

Lista właściwości danego modelu znajduje się w arkuszu **P_list**. Każda właściwość może być opisana
przez wartości kilku kolumn, najważniejsze z nich to: Label_en (angielska etykieta właściwości), Label_pl (etykieta polska), Datatype (typ danych np. 'string', 'time', 'item'), oraz kolumny z opisami właściwości: Description_en (agielski opis), Description_pl (polski opis). Dodatkowo można (opcjonalnie) wypełnić kolumny Wiki_id (z identyfikatorem Q z wikidata.org, wówczas automatycznie utworzona zostanie deklaracja wskazująca na odpowiednik właściwości w wikidata.org) oraz Inverse_property (odwrotność bieżącej właściwości w formie identyfikatora Q lub angielskiej etykiety tamtej właściwości). Wypełnienie tej ostatniej kolumny spowoduje utworzenie takiej deklaracji
dla dodawanej właściwości (właściwość P1 -> jest odwrotnością -> P2), automatycznie zostanie dodana odwrotność w drugą stronę (P2 -> jest odwrotnością -> P1).

![Arkusz P_list](/doc/arkusz_wlasciwosci_P_list.png)

Uwaga: aby nowa właściwość była w ogóle uwzględniona przez skrypt przewtwarzający należy wypełnić kolumnę Datatype, oraz parę: Label_en i Description_pl, lub parę Label_en i Label_pl, w innym przypadku wiersz arkusza zostanie uznany za niepełny i pominięty.

Wypełnienie tylko tego arkusza już pozwala na przeprowadzenie importu do Wikibase. Powstaną wówczas (o ile ich nie dodano wcześniej) proste definicje właściwości z wypełnionym nagłówkiem (etykiety i opisy), typem danych i opcjonalnie 2 deklaracjami ('Wikidata ID' i 'inverse property').

Jeżeli chcemy wprowadzić więcej informacji dla naszych właściwości, można skorzystać z drugiego arkusza o nazwie **P_statements**. Ma on trzy podstawowe kolumny: 'Label_en', 'P', 'Value', które pozwalają na zapis dowolnej deklaracji dla właściwości, można również zapisać w nich aliasy, opisy i etykiety w różnych językach. Kolumna 'Label_en' powinna zawierać wartość jednoznacznie identyfikującą właściwość do której chcemy zapisać deklarację, może to być angielska etykieta właściwości, może to być identyfikator P właściwości (jeżeli już jest w wikibase). Kolumna 'P' powinna zawierać właściwość którą chcemy dodać jako deklarację, znów może to być jej angielska etykieta np. 'instance of', ale może to być symbol istniejącej już właściwości w Wikibase np. P47. Jeżeli chcemy dopisać do właściwości alias, opis czy etykietę w języku innym niż polski czy angielski, w tej kolunie umieszczamy kod takiej informacji np. 'A' i kod języka np. 'de', czyli razem: 'Ade' co oznacza alias w języku niemieckim. Analogicznie 'Lde' oznacza etykietę w języku niemieckim, a 'Dde' - opis w języku niemieckim. Wartość nowej deklaracji jest zapisywana w kolumnie 'Value', format zawartość tej kolumny zależy od typu danych deklaracji (opis formatów dla różnych typów danych jest poniżej w sekcji szczegółowych informacji).

![Arkusz P_statements](/doc/arkusz_deklaracji_dla_wlasciwosci_P_statements.png)

Lista elementów danego modelu znajduje się w arkuszu **Q_list**. Każdy element może być opisany przez wartość kilku kolumn, podstawowe: Label_en i Label_pl oznaczają etykietę w języku angielskim i polskim, Description_en i Description_pl analogicznie - opisy ang i pl. Opcjonalne kolumny: Wiki_id - identyfikator odpowiednika elementu w wikidata.org, StartsAt i EndsAt wyznaczają ramy czasowe dla opisywanego elementu np. element Księstwo Warszawskie może mieć przypisane wartości StartsAt=1807 i EndsAt=1815, kolumna Instance of może wskazywać element którego instacją jest bieżący element np. Bolesław Prus może mieć deklarację Instance of = human. Wartość w kolumnie Instance of może być angielską etykietą elementu, identyfikatorem Q jeżeli jest już w wikibase lub identyfikatorem Purl, jeżeli docelowy element posiada identyfikator Purl.

![Arkusz Q_list](/doc/arkusz_elementów_Q_list.png)

Tak jak w przypadku właściwości, jeżeli chcemy wprowadzić dodatkowe informacje dla elementu, można skorzystać z czwartego arkusza o nazwie **Q_statements**. W nim znajdują się kolumny 'Label_en', 'P', 'Value' które pozwalają na zapis dowolnej deklaracji dla elementu, w identyczny sposób jak to było wyżej opisywane dla arkusza 'P_statements' dla właściwości. Dla elementów można ponadto uzupełnić dodatkowe kolumny: Qualifier i Qualifier_value z danymi kwalifikatorów dla bieżącej deklaracji. W pierwszej z nich powinien znaleźć się identyfikator Q lub angielska etykieta właściwości kwalifikatora, w drugiej jego wartość. Można przypisać wiele kwalifikatorów do deklaracji, jeżeli w arkuszu kolejne wiersze nie będa miały wypełnionych kolumn 'Label_en', 'P', 'Value', ale będą wypełnione kolumny kwalifikatorów to skrypt importujący przyjmie że są to kolejne kwalifikatory do tej samej deklaracji.

![Arkusz Q_statements](/doc/arkusz_deklaracji_dla_elementow_Q_statements.png)

W przypadku importu modelu danych częstą sytuacją będzie przypisywanie tej samej referencji do deklaracji dopisywanych do elementów, gdyż źródłem modelu jest jedna publikacja, jedna ontologia. Aby to ułatwić można uzupełnić piąty arkusz pliku XLSX o nazwie **Globals**, gdzie można zdefiniować referencje globalne dla arkuszy. Arkusz posiada trzy kolumny: 'Sheet' - na nazwę arkusza dla którego będzie obowiązywała referencja globalna, 'Reference_property' na właściwość referencji (wartość kolumny w formie identyfikatora Q lub angielskiej etykiety), 'Referencje_value' - na wartość referencji (zwykle będzie to element lub adres url).

![Arkusz Globals](/doc/arkusz_Globals.png)

Uwaga: dla maksymalnego uproszczenia przyjęto, że w przypadku właściwości (property) ich angielskie etykiety są w danej instancji Wikibase unikalne, podobnie w przypadu tzw. elementów (item) strukturalnych/definicyjnych, tu jednak przyjęto wyjątek - elementy posiadające identyfikator purl mogą mnieć nieunikalne etykiety.

### Uzupełnianie danych

Machanizm tworzenia modeli można używać także do ich uzupełniania, podczas przetwarzania zawartości arkuszy skrypt weryfikuje czy dana właściwość już istnieje (cechą identyfikacyjną jest angielska etykieta), jeżeli tak to przechodzi w tryb uaktualniania sprawdzając czy różni się opis w języku angielskim lub polskim (między arkuszem a zawartością Wikibase). Jeżeli tak - wprowadza nową ich wartość, podobnie weryfikowana jest zawartość kolumn Wiki_id i Inverse_property, jeżeli nie ma takich zapisów w Wikibase - zostaną dodane. 

Tryb aktualizacji działa także w arkuszu deklaracji dla właściwości (P_statements), każdy wiersz arkusza podlega weryfikacji czy zdefiniowana deklaracja (lub wartość aliasu, etykiety lub opisu) już istnieje (czy właściwość ma deklarację o takiej wartości jak w arkuszu). Jeżeli tak - zapis do Wikibase jest pomijany.

Jeżeli w instancji Wikibase istniała już deklaracja np. właściwości 'Instance of' lecz o innej wartości, skrypt doda nową wartość do istniejącego zapisu. Jeżeli istniał juz alias dla danego języka, zostanie on nadpisany, podobnie w przypadku opisów. Jeżeli w arkuszu dopisano referencję do deklaracji a w instancji Wikibase deklaracja nie posiada takiej referencji zostanie ona dopisana. 

Analogicznie skrypt działa w przypadku elementów, dane są uaktualniane i uzupełniane, jeżeli w arkuszu deklaracji dla elementów dopisano nowe kwalifikatory, skrypt doda je do istniejących.
Skrypt nie usuwa natomiast istniejących danych: deklaracji, referencji, kwalifikatorów.

### Kontrola danych

Skrypt podczas przetwarzania pliku kontroluje istnienie wymaganych arkuszy o określonych wyżej nazwach, podobnie kontrolowana jest zawartość arkusza, lista obowiązkowych kolumn o określonych nazwach (wielkość liter ma znaczenie). Podczas przetwarzania wierszy arkusza, skrypt pomija puste wiersze, oraz te w których nie wypełniono wymaganych kolumn. Dane z wierszy arkusza są weryfikowane z zawartością instancji Wikibase, dane które już są w Wikibase są pomijane, skrypt wyświetla stosowną informację. Weryfikowana jest możliwość dodania danych, np, deklaracja do elementu którego jeszcze nie ma w Wikibase, czy deklaracja właściwości jeszcze nie dodanej do Wikibase, wywoła odpowiedni komunikat, skrypt pominie dany wiersz i będzie kontynuował przetwarzanie kolejnych. Wszyskie komunikaty są wypisywane na ekran terminala, można wyjście skryptu przekierować do pliku w celu późniejszej analizy. Po poprawieniu i uzupełnieniu arkusza można przetwarzanie uruchomić ponownie.

Fragment logów przetwarzania arkusza XLSX:

```
PROPERTY: Wikidata ID
Property: 'Wikidata ID' already exists: P50, update mode.
SKIP: właściwość: P50 (Wikidata ID) posiada już opis w języku: "en" o wartości: Wikidata entity ID
SKIP: właściwość: P50 (Wikidata ID) posiada już opis w języku: "pl" o wartości: Identyfikator w Wikidata
PROPERTY: located in the administrative territorial entity, STATEMENT: subproperty of, VALUE: part of
SKIP: właściwość: 'P127' (located in the administrative territorial entity) already has a statement: 'P208 with value: P212'.
PROPERTY: located in the administrative territorial entity, STATEMENT: subproperty of, VALUE: located in
SKIP: właściwość: 'P127' (located in the administrative territorial entity) already has a statement: 'P208 with value: P219'.
ITEM: 'village' already exists: Q79095, update mode enabled.
SKIP: element: Q79095 (village) posiada już dla języka: "en" opis: Village is a locality composed of a group of buildings, mostly of residential and economic character, but sometimes, also industrial ones (i.e. ironworks, mill) as well as a belonging land, inhabited by people involved particularly in agricultural and construction activities or in farming industry (i.e. blacksmith or mill work), and not having city rights nor a status of a city or a town. Some villages in Early Middle Ages had a right to organise a fair and a market.
SKIP: element Q79095 (village) posiada deklarację: P50 o wartości: Q532
ITEM: part of a village, STATEMENT: purl identifier, VALUE: http://purl.org/ontohgis#settlement_unit_63
Pominięto referencję globalną dla deklaracji: Q79347->P197 typu external-id.
SKIP: element: 'Q79347' (part of a village) już posiada deklarację: 'P197' o wartości: http://purl.org/ontohgis#settlement_unit_63.
ITEM: city/town, STATEMENT: described by source, VALUE: Irsigler, Die Stadt im Mittelalter
ERROR: w instancji Wikibase brak elementu -> Irsigler, Die Stadt im Mittelalter będącego wartością -> described by source
ITEM: colony, STATEMENT: described by source, VALUE: Słownik języka polskiego (Trzaska)
STATEMENT ADDED, Q79353 (colony): P218 -> Słownik języka polskiego (Trzaska)
ITEM: forest settlement of a village, STATEMENT: subclass of, VALUE: disctrict
ERROR: w instancji Wikibase brak elementu -> disctrict będącego wartością -> subclass of
ITEM: forest settlement of a village, STATEMENT: instance of, VALUE: settlement
SKIP: element: 'Q79358' (forest settlement of a village) już posiada deklarację: 'P47' o wartości: Q79350.
```

### Szczegółowy opis działania

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
- 'Value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345. Skrypt rozpoznaje typ danych właściwości z kolumny 'P'. Obecnie obsługiwane typy danych: 'string', 'wikibase-property' ('property'), 'wikibase-item' ('item'), 'external-id', 'url', 'monolingualtext', 'quantity', 'time', 'url', 'globe-coordinate'.
- 'Reference_property' - właściwość referencji
- 'Reference_value' - wartość referencji

Dla właściwości o type danych 'globe-coordinate' należy wprowadzić wartość w formie 'latitude,longitude,precision' zgodnie z dokumentacją (https://www.wikidata.org/wiki/Help:Data_type#Globe_coordinate), np. '19.9,54.8,0.01', jeżeli wartość precision zostanie pominięta skrypt przyjmie domyślną wartość 0.1.

Dla właściwości o typie danych 'time' (https://www.wikidata.org/wiki/Help:Data_type#Time) należy wprowadzić wartość w standardzie ISO 8601 z określeniem precyzji daty po znaku / (0-14, zgodnie z opisem: https://www.wikidata.org/wiki/Special:ListDatatypes#time) np. 
'+1900-00-00T00:00:00Z/9' dla roku 1900. Skrypt zaakceptuje także krótszą formę daty np.: w formie 4 znakowego roku: 1525, w formie zwykłej daty 1525-04-11, także z samym miesiącem 1525-10, te krótsze formy skrypt automatycznie przekształca w zapis z precyzją.

Dla właściości typu 'wikibase-item' ('item') należy wprowadzić symbol Qxxx elementu (jeżeli jest znany) angielską etykietę elementu, lub identyfikator purl, który szukany element ma przypisany w formie deklaracji 'purl identifier'.

Właściwość typu 'monolingualtext' powinna zawierać, oprócz tekstu, informację o języku w jakim jest zapisany w formie np.: pl:"To jest tekst w języku polskim".

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

Przykładowe dane do importu z katalogu data pochodzą z bazy ontoghis.pl i zostały przygotowane w ramach prac projektu Dariah-PL w IH PAN.


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
