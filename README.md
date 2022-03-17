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
 - WIKIDARIAH_USER login użytkownika, który utworzył hasło bota
 - WIKIDARIAH_PWD hasło bota

Plik xlsx, z którym współpracuje skrypt powinien posiadać arkusz o nazwie **P_list**, w którym 
znajdują się kolumny (obecnie 7):

- Label_en - etykieta ang.
- Label_pl - etykieta pl.
- datatype - typ danych (string', 'wikibase-item', 'wikibase-property', 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate')
- Description_en - opis ang.
- Description_pl - opis pl.
- Wiki_id - identyfiktor odpowiednika właściwości w wikidata.org
- inverse_property - odwrotna właściwość

Dwie ostatnie nie są wymagane. Przykład:

```
architectural style | styl architektoniczny | wikibase-item | architectural style of a structure     | styl architektoniczny konstrukcji | P 149 | 
followed by         | następca              | wikibase-item | immediately following item in a series | następny element z serii     | P156  | 
follows             | poprzednik            | wikibase-item | immediately prior item in a series     | poprzedni element z serii    | P155  | followed by
```

Istnienie arkuszy i kolumn o oczekiwanych nazwach jest weryfikowane przez skrypt.

Plik xlsx powinien też posiadać arkusz **P_statments**, w którym dla istniejących już właściwości P można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć trzy kolumny: 
- 'Label_en' - właściwość do której dodajemy deklarację (jej ang. etykieta lub numer P), 
- 'P' - właściwość, którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 
- 'value' - wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345 
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