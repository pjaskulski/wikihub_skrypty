""" połączenie z serwerem bazy danych ontohgis,
    test importu danych geo do wikibase
"""

import os
import sys
from pathlib import Path
import psycopg2
from dotenv import load_dotenv


# login i hasło ze zmiennych środowiskowych
env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

DB_LOGIN = os.environ.get("DB_LOGIN")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_HOST = os.environ.get("DB_HOST")
DB_PORT = os.environ.get("DB_PORT")
DB_DATABASE = os.environ.get("DB_DATABASE")

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
sql = """
    SELECT "Identifiers", "Names", "AdministrativeUnitTypeIdentifiers"
    FROM ontology."VariableAdministrativeUnits"
    WHERE "Identifiers" <100000000
    LIMIT 10
"""

cursor.execute(sql)
data = cursor.fetchall()

for result in data:
    adm_unit_id = int(result[0])
    label_pl = label_en = result[1]
    adm_unit_type = result[2]
    ontohgis_database_id = f'ONTOHGIS-VariableAdministrativeUnits-{adm_unit_id}'
    adm_unit_type_purl = f'http://purl.org/ontohgis#administrative_type_{adm_unit_type}'
    instance_of = 'administrative unit'

    print(adm_unit_id, label_pl, ontohgis_database_id, adm_unit_type_purl)

    # zapytanie zwracające listę nazw i lat obowiązywania dla jednostki administracyjnej
    sql = f"""
    SELECT "Names", "StartsAt", "EndsAt" 
    FROM ontology."AdministrativeUnitNames"
    WHERE "VariableAdministrativeUnitIdentifiers" = {adm_unit_id}
"""
    cursor.execute(sql)
    data_unit_names = cursor.fetchall()
    for record in data_unit_names:
        names = record[0]
        starts_at = record[1]
        ends_at = record[2]

        print(names, starts_at, ends_at)

# zapytanie zwracające dane o przynależności jednostek do jednostki nadrzędnej
# oraz przynależności jednostek podrzędnych do danej jednostki
sql = """
SELECT "WholeIdentifiers", "PartIdentifiers", "StartsAt", "EndsAt" 
FROM ontology."AdministrativeUnitMereologyLinks"
LIMIT 10
"""

cursor.execute(sql)
data_unit_names = cursor.fetchall()
for record in data_unit_names:
    whole = record[0]
    part = record[1]
    starts_at = record[2]
    ends_at = record[3]

    print(f'ONTOHGIS-VariableAdministrativeUnits-{whole}')
    print(f'ONTOHGIS-VariableAdministrativeUnits-{part}')
    print(starts_at)
    print(ends_at)


# zamykanie połączenia z DB
conn.close()
