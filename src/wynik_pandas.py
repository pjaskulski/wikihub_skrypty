""" pandas wynik """
import csv
import sqlite3
from sqlite3 import Error
from pathlib import Path
import geopy.distance


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

    input_path = Path('..') / 'data' / 'wynik.csv'
    output_path = Path('..') / 'data' / 'wynik_pandas_v2.csv'
    db_path = Path('..') / 'data' / 'ahp_zbiorcza.sqlite'

    db = create_connection(db_path, with_extension=False)

    with open(input_path, 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:

            new_prng = row['new_prng']
            if not new_prng:
                continue

            id_ahp = row['id_miejscowosci']
            zbiorcza_prng = row['zbiorcza_prng']
            ahp_nazwa_wsp  = row['nazwa_wspolczesna']
            ahp_nazwa16w  = row['nazwa_16w']
            ahp_powiat  = row['powiat_p']
            ahp_nazwa_sl = row['nazwa_slownikowa']
            ahp_pkt_WGS84 = row['ahp_pkt_WGS84']
            zbiorcza_prng_nazwa = row['NAZWAGLOWN']
            ahp_prng_dist = float(row['ahp_prng_dist'])

            sql = f"""
                    SELECT PRNG, WGS84, NAZWAGLOWN
                    FROM miejscowosci_wspolna
                    WHERE PRNG = {int(new_prng)}
            """
            cur_prng = db.cursor()
            cur_prng.execute(sql)
            results = cur_prng.fetchone()

            new_dist = 0
            prng_nazwa = ''
            if results:
                prng_nazwa = field_strip(results[2])
                wgs84 = field_strip(results[1])
                if wgs84:
                    new_dist = calculate_distance(ahp_pkt_WGS84, wgs84)

            with open(output_path, 'a', encoding='utf-8') as f:
                f.write(f'"{id_ahp}","{ahp_nazwa_wsp}","{ahp_nazwa16w}","{ahp_nazwa_sl}","{ahp_powiat}","{zbiorcza_prng}","{zbiorcza_prng_nazwa}",{ahp_prng_dist:.2f},"{prng_nazwa}","{new_prng}",{new_dist:.2f}\n')
