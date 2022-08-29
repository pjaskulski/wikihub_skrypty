""" połączenie z serwerem bazy danych ontohgis,
    test importu danych geo do wikibase
"""

import os
import sys
import time
from pathlib import Path
import psycopg2
from shapely import wkb
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikidariahtools import find_name_qid, element_search_adv
from property_import import create_statement_data, has_statement


# pomiar czasu wykonania
start_time = time.time()

WIKIBASE_WRITE = False
q_items = {}

# kolejność języków w polach tablicowych
# 1 - polski
# 2 - rosyjski
# 3 - niemiecki
# 4 - ukraiński
# 5 - białoruski
# 6 - litewski
# 7 - łacina
# 8 - czeski
# 9 - węgierski
# 10 - angielski

lang_code = {0: "pl", 1:"ru", 2:"de", 3:"uk", 4:"be", 5:"lt", 6:"la", 7:"cs", 8:"hu", 9:"en"}

# typy miejscowości (tymczasowy słownik, gdyż wyszukiwanie przez purl może nie działać)
settlement_types = {}
settlement_types[71] = 'Q79356'  # osada wsi
settlement_types[2] = 'Q79095'   # wieś
settlement_types[63] = 'Q79347'  # część wsi
settlement_types[75] = 'Q79348'  # przysiółek wsi
settlement_types[61] = 'Q79349'  # część miasta
settlement_types[33] = 'Q79350'  # osada
settlement_types[66] = 'Q79351'  # kolonia wsi
settlement_types[36] = 'Q79352'  # osada leśna
settlement_types[20] = 'Q79353'  # kolonia
settlement_types[3] = 'Q79354'   # miasto
settlement_types[27] = 'Q79355'  # leśniczówka
settlement_types[71] = 'Q79356'  # osada wsi
settlement_types[60] = 'Q79357'  # część kolonii
settlement_types[69] = 'Q79358'  # osada leśna wsi
settlement_types[8] = 'Q79359'   # folwark
settlement_types[38] = 'Q79360'  # osada młyńska
settlement_types[44] = 'Q79361'  # przysiółek
settlement_types[74] = 'Q79362'  # przysiółek osady
settlement_types[62] = 'Q79363'  # część osady
settlement_types[73] = 'Q79364'  # przysiółek kolonii
settlement_types[43] = 'Q79365'  # przedmieście
settlement_types[76] = 'Q79366'  # schronisko turystyczne
settlement_types[64] = 'Q79367'  # kolonia kolonii
settlement_types[1] = 'Q79368'   # zamek
settlement_types[125] = 'Q79369' # osada kuźnicza
settlement_types[70] = 'Q79370'  # osada osady
settlement_types[65] = 'Q79371'  # kolonia osady
settlement_types[72] = 'Q79372'  # osiedle wsi
settlement_types[112] = 'Q79373' # część przysiółka
settlement_types[68] = 'Q79374'  # osada kolonii
settlement_types[21] = 'Q79375'  # osada górnicza
settlement_types[37] = 'Q79376'  # osada miejska
settlement_types[34] = 'Q79422'  # osiedle
settlement_types[132] = 'Q79421' # klasztor
settlement_types[19] = 'Q79425'  # osada klasztorna
settlement_types[4] = 'Q79442'   # ruiny zamku
settlement_types[99] = 'Q79378'  # osada karczemna
settlement_types[67] = 'Q79443'  # osada kolejowa
settlement_types[7] = 'Q79380'   # dwór - obiekt


# adresy wikibase
wbi_config['MEDIAWIKI_API_URL'] = 'https://prunus-208.man.poznan.pl/api.php'
wbi_config['SPARQL_ENDPOINT_URL'] = 'https://prunus-208.man.poznan.pl/bigdata/sparql'
wbi_config['WIKIBASE_URL'] = 'https://prunus-208.man.poznan.pl'

# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

DB_LOGIN = os.environ.get("DB_LOGIN")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_DATABASE = os.environ.get("DB_DATABASE")

BOT_LOGIN = os.environ.get('WIKIDARIAH_USER')
BOT_PASSWORD = os.environ.get('WIKIDARIAH_PWD')


# standardowe właściwości i elementy
ok, p_instance_of = find_name_qid('instance of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'instance of' w instancji Wikibase")
    sys.exit(1)
ok, p_stated_as = find_name_qid('stated as', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated as' w instancji Wikibase")
    sys.exit(1)
ok, p_stated_in = find_name_qid('stated in', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated in' w instancji Wikibase")
    sys.exit(1)
ok, p_point_in_time = find_name_qid('point in time', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'point in time' w instancji Wikibase")
    sys.exit(1)
ok, p_starts_at = find_name_qid('starts at', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'starts at' w instancji Wikibase")
    sys.exit(1)
ok, p_ends_at = find_name_qid('ends at', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'ends at' w instancji Wikibase")
    sys.exit(1)
ok, p_part_of = find_name_qid('part of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'part of' w instancji Wikibase")
    sys.exit(1)
ok, p_has_part_or_parts = find_name_qid('has part or parts', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'has part or parts' w instancji Wikibase")
    sys.exit(1)
ok, p_ontohgis_database_id = find_name_qid('ontohgis database id', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'ontohgis database id' w instancji Wikibase")
    sys.exit(1)
ok, q_dwelling = find_name_qid('dwelling', 'item', strict=True)
if not ok:
    print("ERROR: brak elementu 'administrative unit' w instancji Wikibase")
    sys.exit(1)
ok, p_reference_url = find_name_qid('reference URL', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'reference URL' w instancji Wikibase")
    sys.exit(1)
ok, p_prng_id = find_name_qid('PRNG id', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'PRNG id' w instancji Wikibase")
    sys.exit(1)
ok, p_codgik_id = find_name_qid('codgik id', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'codgik id' w instancji Wikibase")
    sys.exit(1)
ok, p_settlement_type = find_name_qid('settlement type', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'settlement type' w instancji Wikibase")
    sys.exit(1)
ok, q_ahp = find_name_qid('Historical Atlas of Poland', 'item', strict=True)
if not ok:
    print("ERROR: brak elementu 'Historical Atlas of Poland' w instancji Wikibase")
    sys.exit(1)
ok, p_coordinate = find_name_qid('coordinate location', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'coordinate location' w instancji Wikibase")
    sys.exit(1)


# wspólna referencja dla wszystkich deklaracji - czy to ma być ontohgis.pl???
references = {}
references[p_reference_url] = 'https://ontohgis.pl'

# logowanie do instancji wikibase
login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD)

# połączenie do serwera DB
conn = psycopg2.connect(
   database=DB_DATABASE,
   user=DB_LOGIN,
   password=DB_PASSWORD,
   host=DB_HOST,
   port= DB_PORT
)

# utworzenie kursora
cursor = conn.cursor()

# zapytanie zwracające listę miejscowości
sql = """
    SELECT "Identifiers", "Names", "codgik_gid_fk", public."miejscowosci_codgik"."id_prng"
    FROM ontology."VariableSettlements"
    LEFT JOIN public."miejscowosci_codgik" ON "codgik_gid_fk" = "gid"
"""

cursor.execute(sql)
results = cursor.fetchall()
result_count = len(results)

print(result_count)

# przygotowanie raportu i listy dla wiki
report_path = '../log/lista_miejscowosci.html'
f = open(report_path, 'w', encoding='utf-8')
f.write('<html>\n')
f.write('<head>\n')
f.write('<meta charset="UTF-8">\n')
f.write('<title>Lista elementów</title>\n')
f.write('</head>\n')
f.write('<body>\n')
f.write('<h2>Lista dodanych/uaktualnionych miejscowości</h2>\n')
f.write('<ol>\n')
wiki_path = '../log/lista_miejscowości.txt'
g = open(wiki_path, 'w', encoding='utf-8')


for index, result in enumerate(results):
    if index > 5:
        sys.exit(1)

    settlement_id = int(result[0])
    label_pl = label_en = result[1]
    ontohgis_database_id = f'ONTOHGIS-VariableSettlements-{settlement_id}'
    id_codgik_gid_fk = result[2]
    if isinstance(id_codgik_gid_fk, int):
        id_codgik_gid_fk = str(id_codgik_gid_fk)
    id_prng = result[3]
    if isinstance(id_prng, int):
        id_prng = str(id_prng)

    print(f'Przetwarzanie {index + 1}/{result_count} - {label_pl} - PRNG: {id_prng}')

    # tworzenie deklaracji
    data = []

    # deklaracja właściwości 'ontohgis database id'
    statement = create_statement_data(
                            p_ontohgis_database_id,
                            ontohgis_database_id,
                            None,
                            None,
                            add_ref_dict=None,
                            if_exists="APPEND",
                        )
    if statement:
        data.append(statement)

    # deklaracja właściwości 'prng id'
    statement = create_statement_data(
                            p_prng_id,
                            id_prng,
                            None,
                            None,
                            add_ref_dict=None,
                            if_exists="APPEND",
                        )
    if statement:
        data.append(statement)

    # deklaracja właściwości 'codgik id'
    statement = create_statement_data(
                            p_codgik_id,
                            id_codgik_gid_fk,
                            None,
                            None,
                            add_ref_dict=None,
                            if_exists="APPEND",
                        )
    if statement:
        data.append(statement)


    # deklaracja właściwości 'instance of'
    statement = create_statement_data(
                            p_instance_of,
                            q_dwelling,
                            references,
                            None,
                            add_ref_dict=None,
                            if_exists="APPEND",
                        )
    if statement:
        data.append(statement)

    # zapytanie zwracające listę nazw i lat obowiązywania dla miejscowosci
    sql = f"""
        SELECT "Names", "StartsAt", "EndsAt", "Source", "AlternativeNames"
        FROM ontology."SettlementNames"
        WHERE "VariableSettlementIdentifiers" = {settlement_id}
    """
    cursor.execute(sql)
    data_settlements_names = cursor.fetchall()
    aliasy = {}
    qualifiers = {}
    for record in data_settlements_names:
        # print(record)
        names = record[0]
        starts_at = record[1]
        ends_at = record[2]
        source = record[3]

        aliasy = {}
        qualifiers = {}

        # kwalifikator 'point in time'
        if (starts_at.year == ends_at.year and starts_at.month == 1
            and starts_at.day == 1 and ends_at.month == 12 and ends_at.day == 31):
            year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_point_in_time] = year
        else:
            start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_starts_at] = start_year
            end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_ends_at] = end_year

        for index, name in enumerate(names):
            # deklaracja 'stated as'
            lang = lang_code[index]
            stated_as = f'{lang_code[index]}:"{name}"'
            statement = create_statement_data(
                            p_stated_as,
                            stated_as,
                            references,
                            qualifiers,
                            add_ref_dict=None,
                            if_exists="APPEND",
                        )
            if statement:
                data.append(statement)
            # jeżeli name inne od polskiej etykiety to dodajemy jako alias
            # w odpowiednim języku
            if name != label_pl:
                aliasy[lang_code[index]] = name

        #print(names, starts_at.year, ends_at, type(starts_at))

    # zapytanie zwracające typy miejscowości (i daty obowiązywania)
    sql = f"""
        SELECT "VariableSettlementIdentifiers",
               "StartsAt",
               "EndsAt",
               "Source",
               "SettlementTypeIdentifiers",
               ontology."SettlementTypesDictionary"."Names" as SettlementTypeName
        FROM ontology."SettlementTypes"
        JOIN ontology."SettlementTypesDictionary" ON ontology."SettlementTypes"."SettlementTypeIdentifiers" = ontology."SettlementTypesDictionary"."Identifiers"
        WHERE "VariableSettlementIdentifiers" = {settlement_id}
    """
    cursor.execute(sql)
    data_settlements_type = cursor.fetchall()

    qualifiers = {}

    for record in data_settlements_type:
        starts_at = record[1]
        ends_at = record[2]
        source = record[3]
        settlement_type_id = int(record[4])
        settlement_type_qid = settlement_types[settlement_type_id]

        qualifiers = {}
        if (starts_at.year == ends_at.year and starts_at.month == 1
            and starts_at.day == 1 and ends_at.month == 12 and ends_at.day == 31):
            year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_point_in_time] = year
        else:
            start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_starts_at] = start_year
            end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_ends_at] = end_year

        local_references = None
        if source == 'AHP':
            local_references= {}
            local_references[p_stated_in] = q_ahp


        statement = create_statement_data(
                            p_settlement_type,
                            settlement_type_qid,
                            references,
                            qualifiers,
                            add_ref_dict=local_references,
                            if_exists="APPEND",
                        )
        if statement:
            data.append(statement)


    # zapytanie zwracające lokalizację miejscowości (i daty obowiązywania)
    sql = f"""
        SELECT "VariableSettlementIdentifiers",
               "StartsAt",
               "EndsAt",
               "Source",
               "the_geom"
        FROM ontology."SettlementLocations"
        WHERE "VariableSettlementIdentifiers" = {settlement_id}
    """
    cursor.execute(sql)
    data_settlements_loc = cursor.fetchall()

    qualifiers = {}

    for record in data_settlements_loc:
        starts_at = record[1]
        ends_at = record[2]
        source = record[3]
        geom = record[4]
        geom = wkb.loads(record[4], hex=True).wkt   # POINT (18.497368539000203 51.663693918985125)
        settlement_location = geom.replace('POINT', '').replace('(', '').replace(')','').strip().replace(' ', ',')

        qualifiers = {}
        if (starts_at.year == ends_at.year and starts_at.month == 1
            and starts_at.day == 1 and ends_at.month == 12 and ends_at.day == 31):
            year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_point_in_time] = year
        else:
            start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_starts_at] = start_year
            end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_ends_at] = end_year

        local_references = None
        if source == 'AHP':
            local_references= {}
            local_references[p_stated_in] = q_ahp

        statement = create_statement_data(
                            p_coordinate,
                            settlement_location,
                            references,
                            qualifiers,
                            add_ref_dict=local_references,
                            if_exists="APPEND",
                        )
        if statement:
            data.append(statement)


    wd_item = wbi_core.ItemEngine(new_item=True, data=data)
    wd_item.set_label(label_en, lang='en')
    wd_item.set_label(label_pl,lang='pl')

    if aliasy:
        for lang_alias, value_alias in aliasy.items():
            wd_item.set_aliases(value_alias, lang_alias)

    # wyszukiwanie po etykiecie i identyfikatorze ontohgis (same etykiety
    # miejscowości się powtarzają!)
    parameters = [(p_ontohgis_database_id, ontohgis_database_id)]
    ok, item_id = element_search_adv(label_en, 'en', parameters=parameters)

    if not ok:
        if WIKIBASE_WRITE:
            new_id = wd_item.write(login_instance, bot_account=True, entity_type='item')
            if new_id:
                print(f'Dodano nowy element: {label_en} ({settlement_id}) = {new_id}')
                q_items[settlement_id] = new_id
                # zapis do raportu
                f.write(f'<li>{label_pl} = <a href="https://prunus-208.man.poznan.pl/wiki/Item:{new_id}">{new_id}</a></li>\n')
                # zapis dla wiki
                g.write(f'# [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_pl}]\n')
        else:
            new_id = 'TEST'
            print(f"Przygotowano dodanie elementu - EN: {label_en} ({settlement_id}) / PL: {label_pl} ({settlement_id})")
            q_items[settlement_id] = new_id
            # zapis testowy do raportu
            f.write(f'<li>{label_pl} = <a href="https://prunus-208.man.poznan.pl/wiki/Item:{new_id}">{new_id}</a></li>\n')
            g.write(f'# [https://prunus-208.man.poznan.pl/wiki/Item:{new_id} {label_pl}]\n')
    else:
        print(f'Element: {label_en} ({settlement_id}) już istnieje: {item_id}')
        q_items[settlement_id] = item_id
        # zapis do raportu
        f.write(f'<li>{label_pl} = <a href="https://prunus-208.man.poznan.pl/wiki/Item:{item_id}">{item_id}</a></li>\n')
        g.write(f'# [https://prunus-208.man.poznan.pl/wiki/Item:{item_id} {label_pl}]\n')

# zamknięcie raportu
f.write('</ol>\n')
f.write('</body>\n')
f.write('</html>\n')
f.close()
g.close()

# zapytania zwracające dane o przynależności miejscowości podrzędnych
# do danej miejscowości
print("Uzupełnianie 'part of' i 'has part or parts'")
for result in results:
    settlement_id = int(result[0])

    sql = f"""
    SELECT "PartIdentifiers", "StartsAt", "EndsAt"
    FROM ontology."SettlementMereologyLinks"
    WHERE "WholeIdentifiers" = {settlement_id}
    """
    item_qid = q_items[settlement_id]
    if item_qid == 'TEST':
        continue

    cursor.execute(sql)
    results_part = cursor.fetchall()
    data = []
    for record in results_part:
        part = record[0]
        starts_at = record[1]
        ends_at = record[2]

        # kwalifikator 'point in time'
        qualifiers = {}
        if starts_at.year == ends_at.year and starts_at.year > 0:
            year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_point_in_time] = year
        else:
            start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_starts_at] = start_year
            end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_ends_at] = end_year

        part_qid = q_items[int(part)]
        statement = create_statement_data(
                            p_has_part_or_parts,
                            part_qid,
                            references,
                            qualifiers,
                            add_ref_dict=None,
                            if_exists="APPEND",
                            )
        if statement:
            data.append(statement)

    if data:
        if not has_statement(item_qid, p_has_part_or_parts, part_qid):
            if WIKIBASE_WRITE:
                wd_item = wbi_core.ItemEngine(item_id=item_qid, data=data, debug=False)
                wd_item.write(login_instance, entity_type='item')
                print(f'Do elementu {item_qid} dodano właściwość {p_has_part_or_parts} o wartości {part_qid}')
            else:
                print(f'Przygotowano dodanie do elementu {item_qid} właściwości {p_has_part_or_parts} o wartości {part_qid}')
        else:
            print(f'Element {item_qid} już posiada właściwość {p_has_part_or_parts} o wartości {part_qid}')

# zapytania zwracające dane o przynależności danej miejscowości do miejscowości nadrzędnej
for result in results:
    adm_unit_id = int(result[0])

    sql = f"""
    SELECT "WholeIdentifiers", "StartsAt", "EndsAt"
    FROM ontology."SettlementMereologyLinks"
    WHERE "PartIdentifiers" = {settlement_id}
    """
    item_qid = q_items[settlement_id]
    if item_qid == 'TEST':
        continue

    cursor.execute(sql)
    results_part = cursor.fetchall()
    data = []
    for record in results_part:
        whole = record[0]
        starts_at = record[1]
        ends_at = record[2]

        # kwalifikator 'point in time'
        qualifiers = {}
        if starts_at.year == ends_at.year and starts_at.year > 0:
            year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_point_in_time] = year
        else:
            start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_starts_at] = start_year
            end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
            qualifiers[p_ends_at] = end_year
            #print("Mamy problem:", starts_at, ends_at)

        whole_qid = q_items[int(whole)]
        statement = create_statement_data(
                            p_part_of,
                            whole_qid,
                            references,
                            qualifiers,
                            add_ref_dict=None,
                            if_exists="APPEND",
                            )
        if statement:
            data.append(statement)

    if data:
        if not has_statement(item_qid, p_part_of, whole_qid):
            if WIKIBASE_WRITE:
                wd_item = wbi_core.ItemEngine(item_id=item_qid, data=data, debug=False)
                wd_item.write(login_instance, entity_type='item')
                print(f'Do elementu {item_qid} dodano właściwość {p_part_of} o wartości {whole_qid}')
            else:
                print(f'Przygotowano dodanie do elementu {item_qid} właściwości {p_part_of} o wartości {whole_qid}')
        else:
            print(f'Element {item_qid} już posiada właściwość {p_part_of} o wartości {whole_qid}')

# !!! uzupełnianie description - miejscowości na razie bez opisów !!!


# zamykanie połączenia z DB
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time
print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
