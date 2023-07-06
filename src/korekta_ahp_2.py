""" dopasowywanie PRNG do miejscowości z przypisanymi nieunikalnymi PRGNG """
import csv
import sqlite3
from sqlite3 import Error
from pathlib import Path
import geopy.distance

wojewodztwa = {
        'brzeskie kujawskie':['kujawsko-pomorskie'],
        'brzeskie kujawskie i inowrocławskie':['kujawsko-pomorskie'],
        'chełmińskie':['pomorskie', 'kujawsko-pomorskie'],
        'inowrocławskie':['kujawsko-pomorskie'],
        'kaliskie':['wielkopolskie','łódzkie'],
        'krakowskie':['małopolskie','podkarpackie'],
        'księstwo siewierskie':['śląskie'],
        'lubelskie':['lubelskie'],
        'malborskie':['pomorskie','warmińsko-mazurskie'],
        'mazowieckie':['mazowieckie',],
        'podlaskie':['podlaskie','warmińsko-mazurskie','mazowieckie'],
        'pomorskie':['pomorskie','kujawsko-pomorskie'],
        'poznańskie':['wielkopolskie','lubuskie', 'kujawsko-pomorskie'],
        'płockie':['mazowieckie'],
        'rawskie':['łódzkie', 'mazowieckie'],
        'rawskie i brzeskie kujawskie':[''],
        'sandomierskie':['lubelskie','świętokrzyskie'],
        'sieradzkie':['łódzkie'],
        'ziemia dobrzyńska':['kujawsko-pomorskie'],
        'łęczyckie':['łódzkie','mazowieckie']
        }

def create_connection(db_file, with_extension=False):
    """ tworzy połączenie z bazą SQLite
        db_file - ścieżka do pliku bazy
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        if with_extension:
            conn.enable_load_extension(True)
            conn.load_extension("../fuzzy.so")
            conn.load_extension("../spellfix.so")
            conn.load_extension("../unicode.so")

    except Error as sql_error:
        print(sql_error)

    return conn


def field_strip(value:str) -> str:
    """ funkcja przetwarza wartość pola z bazy/arkusza """
    if value:
        value = value.strip()
    else:
        value = ''

    return value


def calculate_distance(point_ahp:str, point_prng:str) -> float:
    """ oblicza odległość między dwoma punktami, wynik w km """
    if not point_ahp or not point_prng:
        return -999.0
    point_ahp = point_ahp.replace('Point', '').replace('(', '').replace(')','').strip()
    tmp_ahp = point_ahp.split(' ')
    longitude_ahp = float(tmp_ahp[0])
    latitude_ahp = float(tmp_ahp[1])
    coords_ahp = (longitude_ahp, latitude_ahp)

    point_prng = point_prng.replace('Point', '').replace('(', '').replace(')','').strip()
    tmp_prng = point_prng.split(' ')
    longitude_prng = float(tmp_prng[0])
    latitude_prng = float(tmp_prng[1])
    coords_prng = (longitude_prng, latitude_prng)

    return geopy.distance.geodesic(coords_ahp, coords_prng).km


# ------------------------------------MAIN -------------------------------------
if __name__ == '__main__':

    input_korekta = Path('..') / 'data' / 'AHP_PRNG_korekta.csv'
    output_path = Path('..') / 'data' / 'ahp_prng_korekta_2.csv'

    miejscowosci_path = Path('..') / 'data' / 'ahp_zbiorcza.sqlite'
    db = create_connection(miejscowosci_path, with_extension=True)
    cur = db.cursor()

    with open(input_korekta, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        liczba = 2626
        licznik = 0
        for row in csv_reader:
            licznik += 1
            if licznik < 1120:
                continue
            id_ahp = row["id_miejscowosci"]
            count_ahp = row['PRNG_count']
            zbiorcza_prng = row["zbiorcza_prng"]

            sql = f""" SELECT
                         ahp_zbiorcza_pkt_prng_import.ahp_pkt_WGS84,
                         miejscowosci_wspolna.WGS84,
                         ahp_zbiorcza_pkt_prng_import.woj_p
                       FROM ahp_zbiorcza_pkt_prng_import
                       INNER JOIN miejscowosci_wspolna
                         ON ahp_zbiorcza_pkt_prng_import.zbiorcza_prng = miejscowosci_wspolna.PRNG
                       WHERE ahp_zbiorcza_pkt_prng_import.id_miejscowosci = '{id_ahp}'
                   """
            cur.execute(sql)
            ahp_rows = cur.fetchone()
            if ahp_rows:
                ahp_WGS84 = field_strip(ahp_rows[0])
                zbiorcza_WGS84 = field_strip(ahp_rows[1])
                ahp_woj = field_strip(ahp_rows[2])
                min_dist = calculate_distance(ahp_WGS84, zbiorcza_WGS84)
            else:
                continue

            print(f'({licznik}/{liczba}) Przetwarzanie: {id_ahp}')
            with open(output_path, 'a', encoding='utf-8') as out:
                out.write(f'"{id_ahp}",{count_ahp},"{zbiorcza_prng},{min_dist:.2f}"\n')

            warunek = 'WHERE'
            if ahp_woj:
                prng_wojewodztwa = wojewodztwa[ahp_woj]
                for woj in prng_wojewodztwa:
                    if warunek != 'WHERE':
                        warunek += ' OR '
                    warunek += f" WOJEWODZTW = '{woj}'"

            sql = """SELECT NAZWAGLOWN as prng_nazwa, POWIAT as prng_powiat, PRNG, WGS84, WOJEWODZTW
                     FROM miejscowosci_wspolna """ + warunek
            cur.execute(sql)
            prng_rows = cur.fetchall()

            for row in prng_rows:
                prng_nazwa = field_strip(row[0])
                prng_powiat = field_strip(row[1])
                prng_prng =  row[2]
                prng_WGS84 = field_strip(row[3])

                if ahp_WGS84 and prng_WGS84:
                    dist = calculate_distance(ahp_WGS84, prng_WGS84)
                    if dist < min_dist:
                        with open(output_path, 'a', encoding='utf-8') as out:
                            out.write(f',,,"{prng_nazwa}","{prng_prng}, {dist:.2f}"\n')
