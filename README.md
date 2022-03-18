# wikidariah_skrypty
Skrypty pomocnicze do importowania. modyfikacji i wyszukiwania danych w instancji Wikibase - WikiDARIAH 

## property_import.py

Skrypt wspomagający tworzenie właściwości w Wikibase (domyślnie w instancji wikibase WikiDARIAH). Na podstawie zawartości arkuszy w formacie xlsx tworzy właściwości oraz dodaje do nich deklaracje. 

Skrypt odczytuje zawartość pliku xlsx wskazanego jako parametr z linii komend np.:
```
python property_import.py data/test.xlsx
```
jeżeli nie podano ścieżki do pliku, szuka domyślnego: `data/arkusz_import.xlsx`

Aby import zadziałał poprawnie należy ustawić w pliku .env właściwe wartości zmiennych:
 - WIKIDARIAH_USER login użytkownika, który utworzył hasło bota (sam login, bez nazwy bota)
 - WIKIDARIAH_PWD hasło bota (przed hasłem nazwa bota oddzielona znakiem %)

Aby skrypt mógł wprowadzać i modyfikować dane użytkownik tworzący hasło bota w wikibase musi mieć nadane odpowiednie uprawnienia.

Plik xlsx, z którym współpracuje skrypt powinien posiadać arkusz o nazwie **P_list**, w którym 
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

Plik xlsx powinien też posiadać arkusz **P_statments**, w którym dla istniejących już właściwości P można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć trzy kolumny: 
- 'Label_en' - właściwość do której dodajemy deklarację (jej ang. etykieta lub numer P), 
- 'P' - właściwość, którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 
- 'value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345. Skrypt rozpoznaje typ danych właściwości z kolumny 'P'. Obecnie obsługiwane typy danych: 'string', 'wikibase-property', 'wikibase-item', 'external-id', 'url', 'monolingualtext'.

Przykład zawartości arkusza:
```
architectural style | refers to          | architecture
architectural style | related properties | painting style
P151                | P47                | Q703
```

W przypadku gdy podano ang. etykietę właściwości (property) lub elementu (item) która nie jest jednoznaczna, skrypt zgłosi problem wraz z listą identyfikatów elementów pasujących do podanej etykiety. W razie braku pasującej właściwości lub elementu zgłoszony zostanie tylko komunikat o braku właściwości. W obu przypadkach deklaracja nie zostanie utworzona. 

Jeżeli podana w arkuszu 'P_list' właściwość już istnieje skrypt po wykryciu jej w wikibase
przechodzi w tryb aktualizacji i modyfikuje dane właściwości według zawartości kolumn w arkuszu.
Podobnie w przypadku deklaracji w arkuszu 'P_statements'. Dane są jednak tylko modyfikowane i dodawane, usunięcie np. wartości z kolumny 'Wiki ID' nie spowoduje usunięcia odpowiedniej deklaracji z wikibase. 

## TODO

- [x]  jeżeli dodano właściwość inverse_property, to właściwość będąca jej wartością powinna dostać odwrotnie analogiczną włąściwość
- [ ]  wyszukiwanie P/Q w wikibase bez względu na wielkość liter
- [x]  modyfikacja istniejących właściwości i deklaracji
- [ ]  druga zakładka (P_statements): obsługa referencji
- [ ]  dodać obsługę pozostałych typów danych podczas dodawania deklaracji (statements): 'quantity', 'time', 'geo-shape', 'globe-coordinate' 