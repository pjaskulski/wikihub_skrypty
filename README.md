# wikidariah_skrypty
Skrypty pomocnicze do importowania. modyfikacji i wyszukiwania danych w instancji Wikibase - WikiDARIAH 

Skrypt **property_import.py** odczytuje zawartość pliku xlsx wskazanego jako parametr z linii komend np.:
```
python property_import.py data/test.xlsx
```
jeżeli nie podano ścieżki do pliku, szuka domyślnego: `data/arkusz_import.xlsx`

Aby import zadziałał poprawnie należy ustawić w pliku .env właściwe wartości zmiennych:
 - WIKIDARIAH_USER login użytkownika, który utworzył hasło bota
 - WIKIDARIAH_PWD hasło bota

Domyślnie skrypt działa w trybie testowym, sprawdzając które property z arkusza już istnieją
a które należy dodać. Aby skrypt faktycznie dodawał property należy wartość zmiennej TEST_ONLY ustawić na False.

Plik xlsx, z którym współpracuje skrypt powinien mieć arkusz o nazwie **P_list**, w którym 
znajdują się kolumny:

- Label_en - etykieta ang.
- Label_pl - etykieta pl.
- datatype - typ danych (string', 'wikibase-item', 'wikibase-property', 'monolingualtext', 'external-id', 'quantity', 'time', 'geo-shape', 'url', 'globe-coordinate')
- Description_en - opis ang.
- Description_pl - opis. pl
- Wiki_id - identyfiktor odpowiednika właściwości w wikidata.org
- inverse_property - odwrotna właściwość

Dwie ostatnie mogą być puste.

Plik xlsx może też mieć arkusz **P_statments**, w którym dla istniejących już właściwości P można przygotować listę dodatkowych deklaracji (statements).
Arkusz powinien mieć trzy kolumny: 1) właściwość do której dodajemy deklarację (jej ang. etykieta lub numer P), 2) właściwość którą chcemy dopisać w deklaracji (jej ang. etykieta lub numer P) oraz 3) wartość dopisywanej właściwości. W przypadku gdy typem wartości jest item Q lub property P w kolumnie powinna znaleźć się ang. etykieta takiego elementu lub konkretny identyfikator - np. Q2345 
```
architectural style | refers to          | architecture
architectural style | related properties | painting style
P151                | P47                | Q703
```

W przypadku gdy podano ang. etykietę właściwości (property) lub elementu (item) która nie jest jednoznaczna, skrypt zgłosi problem wraz z listą identyfikatów elementów pasujących do podanej etykiety. W razie braku pasującej właściwości lub elementu zgłoszony zostanie tylko komunikat o braku właściwości. W obu przypadkach deklaracja nie zostanie utworzona. 

## TODO

- [ ]  jeżeli dodano właściwość inverse_property, to właściwość będąca jej wartością powinna dostać odwrotnie analogiczną włąściwość
- [ ]  wyszukiwanie P/Q w wikibase bez względu na wielkość liter
- [ ]  modyfikacja istniejących właściwości i deklaracji
- [ ]  druga zakładka (P_statements): obsługa referencji