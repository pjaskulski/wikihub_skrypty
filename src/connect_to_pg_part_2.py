""" połączenie z serwerem bazy danych ontohgis,
    test importu danych geo do wikibase
"""

import os
import sys
import time
from pathlib import Path
import psycopg2
from dotenv import load_dotenv
from wikibaseintegrator import wbi_core
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator.wbi_exceptions import (MWApiError)
from wikidariahtools import find_name_qid, get_claim_value
from property_import import create_statement_data, has_statement


# pomiar czasu wykonania
start_time = time.time()

WIKIBASE_WRITE = True
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

with open('../data/type_names_ang.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

UNIT_TYPE_NAME_PL = {}
UNIT_TYPE_NAME_EN = {}

for line in lines:
    line = line.strip()
    tmp = line.split(',')
    if len(tmp) == 3:
        UNIT_TYPE_NAME_PL[int(tmp[2])] = tmp[0]
        UNIT_TYPE_NAME_EN[int(tmp[2])] = tmp[1]

# wczytanie bazy ontohgis_id-qid
with open('../log/adm_unit_id.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    tmp = line.split("=")
    adm_id = int(tmp[0].strip())
    adm_qid = tmp[1].strip()
    q_items[adm_id] = adm_qid

# standardowe właściwości i elementy
ok, p_instance_of = find_name_qid('instance of', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'instance of' w instancji Wikibase")
    sys.exit(1)
ok, p_administrative_unit_type = find_name_qid('administrative unit type', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'administrative unit type' w instancji Wikibase")
    sys.exit(1)
ok, p_stated_as = find_name_qid('stated as', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'stated as' w instancji Wikibase")
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
ok, q_administrative_unit = find_name_qid('administrative unit', 'item', strict=True)
if not ok:
    print("ERROR: brak elementu 'administrative unit' w instancji Wikibase")
    sys.exit(1)
ok, p_reference_url = find_name_qid('reference URL', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'reference URL' w instancji Wikibase")
    sys.exit(1)
ok, q_administrative_system = find_name_qid('administrative system', 'item', strict=True)
if not ok:
    print("ERROR: brak elementu 'administrative system' w instancji Wikibase")
    sys.exit(1)
ok, p_belongs_adm_sys = find_name_qid('belongs to administrative system', 'property', strict=True)
if not ok:
    print("ERROR: brak właściwości 'belongs to administrative system' w instancji Wikibase")
    sys.exit(1)


# wspólna referencja dla wszystkich deklaracji
references = {}
references[p_reference_url] = 'https://ontohgis.pl'

# logowanie do instancji wikibase
login_instance = wbi_login.Login(user=BOT_LOGIN, pwd=BOT_PASSWORD, token_renew_period=7200)

# tymczasowo - wczytanie słownika QID/Purl (typy jednostek administracyjnych)
purl = {}

with open("temp.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    line = line.strip()
    tmp = line.split(" = ")
    purl[tmp[0]] = tmp[1]

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

# zapytanie zwracające listę jednostek administracyjnych
# sql = """
#     SELECT "Identifiers", "Names", "AdministrativeUnitTypeIdentifiers"
#     FROM ontology."VariableAdministrativeUnits"
#     WHERE "Identifiers" = 5364 or "Identifiers" = 15
# """
sql = """
    SELECT "Identifiers", "Names", "AdministrativeUnitTypeIdentifiers"
    FROM ontology."VariableAdministrativeUnits"
    WHERE "Identifiers" < 100000000
"""

cursor.execute(sql)
results = cursor.fetchall()

# zapytania zwracające dane o przynależności przynależności jednostek podrzędnych
# do danej jednostki
# print("Uzupełnianie 'part of' i 'has part or parts'")

# for result in results:
#     adm_unit_id = int(result[0])

#     sql = f"""
#     SELECT "PartIdentifiers", "StartsAt", "EndsAt"
#     FROM ontology."AdministrativeUnitMereologyLinks"
#     WHERE "WholeIdentifiers" = {adm_unit_id}
#     """
#     item_qid = q_items[adm_unit_id]
#     if item_qid == 'TEST':
#         continue

#     cursor.execute(sql)
#     results_part = cursor.fetchall()
#     data = []
#     for record in results_part:
#         part = record[0]
#         starts_at = record[1]
#         ends_at = record[2]

#         # kwalifikator 'point in time'
#         qualifiers = {}
#         if starts_at.year == ends_at.year and starts_at.year > 0:
#             year = f"+{starts_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_point_in_time] = year
#         else:
#             start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_starts_at] = start_year
#             end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_ends_at] = end_year

#         part_qid = q_items[int(part)]
#         statement = create_statement_data(
#                             p_has_part_or_parts,
#                             part_qid,
#                             references,
#                             qualifiers,
#                             add_ref_dict=None,
#                             if_exists="APPEND",
#                             )
#         if statement:
#             data.append(statement)

#     if data:
#         if not has_statement(item_qid, p_has_part_or_parts, part_qid):
#             if WIKIBASE_WRITE:
#                 wd_item = wbi_core.ItemEngine(item_id=item_qid, data=data, debug=False)
#                 wd_item.write(login_instance, entity_type='item')
#                 print(f'Do elementu {item_qid} dodano właściwość {p_has_part_or_parts} o wartości {part_qid}')
#             else:
#                 print(f'Przygotowano dodanie do elementu {item_qid} właściwości {p_has_part_or_parts} o wartości {part_qid}')
#         else:
#             print(f'Element {item_qid} już posiada właściwość {p_has_part_or_parts} o wartości {part_qid}')

# zapytania zwracające dane o przynależności danej jednostki do jednostki nadrzędnej
# start = False

# for result in results:
#     adm_unit_id = int(result[0])

#     sql = f"""
#     SELECT "WholeIdentifiers", "StartsAt", "EndsAt"
#     FROM ontology."AdministrativeUnitMereologyLinks"
#     WHERE "PartIdentifiers" = {adm_unit_id}
#     """
#     item_qid = q_items[adm_unit_id]
#     if item_qid == 'TEST':
#         continue
#     if item_qid == 'Q85819':
#         start = True
#     if not start:
#         continue

#     cursor.execute(sql)
#     results_part = cursor.fetchall()
#     data = []
#     for record in results_part:
#         whole = record[0]
#         starts_at = record[1]
#         ends_at = record[2]

#         # kwalifikator 'point in time'
#         qualifiers = {}
#         if starts_at.year == ends_at.year and starts_at.year > 0:
#             year = f"+{starts_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_point_in_time] = year
#         else:
#             start_year = f"+{starts_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_starts_at] = start_year
#             end_year = f"+{ends_at.year}-00-00T00:00:00Z/9"
#             qualifiers[p_ends_at] = end_year
#             #print("Mamy problem:", starts_at, ends_at)

#         whole_qid = q_items[int(whole)]
#         statement = create_statement_data(
#                             p_part_of,
#                             whole_qid,
#                             references,
#                             qualifiers,
#                             add_ref_dict=None,
#                             if_exists="APPEND",
#                             )
#         if statement:
#             data.append(statement)

#     if data:
#         if not has_statement(item_qid, p_part_of, whole_qid):
#             if WIKIBASE_WRITE:
#                 wd_item = wbi_core.ItemEngine(item_id=item_qid, data=data, debug=False)
#                 wd_item.write(login_instance, entity_type='item')
#                 print(f'Do elementu {item_qid} dodano właściwość {p_part_of} o wartości {whole_qid}')
#             else:
#                 print(f'Przygotowano dodanie do elementu {item_qid} właściwości {p_part_of} o wartości {whole_qid}')
#         else:
#             print(f'Element {item_qid} już posiada właściwość {p_part_of} o wartości {whole_qid}')

# uzupełnianie description
print('Uzupełnianie description')

start = False
result_count = len(results)

for index, result in enumerate(results):
    adm_unit_id = int(result[0])
    unit_qid = q_items[adm_unit_id]

    if unit_qid == 'Q86136':
        start = True
    if not start:
        continue

    # weryfikacja czy opis już jest, jeżeli tak to pomija
    if unit_qid != 'TEST':
        wb_item = wbi_core.ItemEngine(item_id=unit_qid)
        old_pl = wb_item.get_description('pl')
        old_en = wb_item.get_description('en')
        if old_pl or old_en:
            print(f'{index}/{result_count} {unit_qid}: opis elementu już istnieje.')
            continue

    adm_unit_type = result[2]
    adm_unit_type_purl = f'http://purl.org/ontohgis#administrative_type_{adm_unit_type}'
    unit_type_qid = purl[adm_unit_type_purl]

    wb_unit_type = wbi_core.ItemEngine(item_id=unit_type_qid)
    unit_label_pl = wb_unit_type.get_label('pl')
    # tylko nazwa jednostki (bez nazwy systemu w nawiasach)
    pos = unit_label_pl.find('(')
    if pos != -1:
        unit_label_pl = unit_label_pl[:pos].strip()
    unit_label_en = wb_unit_type.get_label('en')
    pos = unit_label_en.find('(')
    if pos != -1:
        unit_label_en = unit_label_en[:pos].strip()

    parent_unit_label_pl = parent_unit_label_en = ''
    if unit_qid != 'TEST' and has_statement(unit_qid, p_part_of):
        value = get_claim_value(unit_qid, p_part_of)
        if value:
            wb_parent_unit = wbi_core.ItemEngine(item_id=value[0])
            parent_unit_label_pl = wb_parent_unit.get_label('pl')
            # tylko nazwa jednostki (bez nazwy systemu w nawiasach)
            pos = parent_unit_label_pl.find('(')
            if pos != -1:
                parent_unit_label_pl = parent_unit_label_pl[:pos].strip()

            parent_unit_label_en = wb_parent_unit.get_label('en')
            pos = parent_unit_label_en.find('(')
            if pos != -1:
                parent_unit_label_en = parent_unit_label_en[:pos].strip()

    adm_sys_label_pl = adm_sys_label_en = ''
    if has_statement(unit_type_qid, p_belongs_adm_sys):
        value = get_claim_value(unit_type_qid, p_belongs_adm_sys)
        if value:
            # zakładamy, że typ należy do 1 systemu admninistracyjnego
            wb_adm_sys = wbi_core.ItemEngine(item_id=value[0])
            adm_sys_label_pl = wb_adm_sys.get_label('pl')
            adm_sys_label_en = wb_adm_sys.get_label('en')

    is_change = False

    if unit_qid != 'TEST':
        if parent_unit_label_pl and parent_unit_label_en:
            new_pl = f"{unit_label_pl} w {parent_unit_label_pl} w {adm_sys_label_pl}"
            new_en = f"{unit_label_en} in {parent_unit_label_en} in {adm_sys_label_en}"
            if old_pl != new_pl:
                wb_item.set_description(new_pl, 'pl')
                is_change = True
            if old_en != new_en:
                wb_item.set_description(new_en, 'en')
                is_change = True
        else:
            new_pl = f"{unit_label_pl} w {adm_sys_label_pl}"
            new_en = f"{unit_label_en} in {adm_sys_label_en}"
            if old_pl != new_pl:
                wb_item.set_description(new_pl, 'pl')
                is_change = True
            if old_en != new_en:
                wb_item.set_description(new_en, 'en')
                is_change = True

    if is_change:
        if WIKIBASE_WRITE:
            try:
                wb_item.write(login_instance, entity_type='item')
                print(f"{index}/{result_count} {unit_qid}: dodano opis - {new_pl} / {new_en}")
            except MWApiError as api_err:
                print(f'API ERROR: {unit_qid} - {api_err.error_msg}')
        else:
            print(f"{index}/{result_count} {unit_qid}: przygotowano dodanie opisu - {new_pl} / {new_en}")

# zamykanie połączenia z DB
conn.close()

end_time = time.time()
elapsed_time = end_time - start_time
print(f'Czas wykonania programu: {time.strftime("%H:%M:%S", time.gmtime(elapsed_time))} s.')
