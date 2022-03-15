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

Plik xlsx, z którym współpracuje skrypt powinien mieć arkusz o nazwie P_list w którym 
znajdują się kolumny:

- Label_en
- Label_pl
- datatype
- Description_en
- Description_pl
- Wiki_id
- inverse_property

Dwie ostatnie mogą być puste.
