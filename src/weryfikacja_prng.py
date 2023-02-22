""" weryfikacja AHP - PRNG """
import sys
import sqlite3
from pathlib import Path
from wikidariahtools import create_connection, field_strip
import geopy.distance
from Levenshtein import distance as lev_distance


def calculate_distance(point_ahp, point_prng) -> float:
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


# wyniki w bazie w pamięci
db_r = sqlite3.connect(":memory:")
cur_r = db_r.cursor()
sql = """
      CREATE TABLE IF NOT EXISTS wyniki (
	    ahp_id text NOT NULL,
        ahp_nazwa text NOT NULL,
	    ahp_nazwa16w text NOT NULL,
        ahp_nazwa_slow text NOT NULL,
        ahp_powiat text NOT NULL,
        prng_nazwa text NOT NULL,
        prng_powiat text NOT NULL,
        ahp_prng_distance REAL,
        prng text NOT NULL
        );
    """
cur_r.execute(sql)

# dane
miejscowosci_path = '../data/ahp_zbiorcza.sqlite'
db = create_connection(miejscowosci_path)

sql = """SELECT
          ahp_zbiorcza_pkt_prng_import.id_miejscowosci,
          ahp_zbiorcza_pkt_prng_import.zbiorcza_prng,
          ahp_zbiorcza_pkt_prng_import.nazwa_wspolczesna,
          ahp_zbiorcza_pkt_prng_import.nazwa_16w,
          ahp_zbiorcza_pkt_prng_import.nazwa_odmianki,
          ahp_zbiorcza_pkt_prng_import.powiat_p,
          ahp_zbiorcza_pkt_prng_import.ahp_pkt_WGS84,
          miejscowosci_wspolna.NAZWAGLOWN,
          miejscowosci_wspolna.POWIAT,
          miejscowosci_wspolna.WGS84,
          ahp_zbiorcza_pkt_prng_import.nazwa_slownikowa,
          ahp_zbiorcza_pkt_prng_import.zbiorcza_prng
      FROM ahp_zbiorcza_pkt_prng_import
      INNER JOIN miejscowosci_wspolna ON ahp_zbiorcza_pkt_prng_import.zbiorcza_prng = miejscowosci_wspolna.PRNG
      """
cur = db.cursor()
cur.execute(sql)
ahp_rows = cur.fetchall()

licznik_nazwa = 0
licznik_nazwa16w = 0
licznik_nazwa_slow = 0
licznik_distance = 0

for row in ahp_rows:
    ahp_id = field_strip(row[0])
    ahp_prng = field_strip(row[1])
    ahp_nazwa = field_strip(row[2])
    ahp_nazwa16w = field_strip(row[3])
    ahp_odmianki = field_strip(row[4])
    ahp_powiat = field_strip(row[5])
    ahp_WGS84 = field_strip(row[6])
    prng_nazwa = field_strip(row[7])
    prng_powiat = field_strip(row[8])
    prng_WGS84 = field_strip(row[9])
    ahp_prng_distance = calculate_distance(ahp_WGS84, prng_WGS84)
    ahp_nazwa_slow = field_strip(row[10])
    zbiorcza_prng = field_strip(row[11])

    if ahp_nazwa:
        nazwa = ahp_nazwa
    elif ahp_nazwa16w:
        nazwa = ahp_nazwa16w
    elif ahp_nazwa_slow:
        nazwa = ahp_nazwa_slow

    if not nazwa:
        print('ERROR: brak nazwy - ', ahp_id)
        sys.exit(1)

    is_diff = False
    if ahp_nazwa and ahp_nazwa != prng_nazwa:
            #or (ahp_nazwa16w and prng_nazwa == ahp_nazwa16w)
            #or (ahp_nazwa_slow and prng_nazwa == ahp_nazwa_slow)):
        licznik_nazwa += 1
        diff = lev_distance(ahp_nazwa, prng_nazwa)
        if diff > 1:
            is_diff = True
    elif ahp_nazwa16w and ahp_nazwa16w != prng_nazwa:
        licznik_nazwa16w += 1
        diff = lev_distance(ahp_nazwa16w, prng_nazwa)
        if diff > 3:
            is_diff = True
    elif ahp_nazwa_slow and ahp_nazwa_slow != prng_nazwa:
        licznik_nazwa_slow += 1
        diff = lev_distance(ahp_nazwa_slow, prng_nazwa)
        if diff > 3:
            is_diff = True

    if is_diff and (ahp_prng_distance > 1.5 and ahp_prng_distance <= 3.0):
        licznik_distance += 1
        sql_add = f"""insert into wyniki (ahp_id, ahp_nazwa, ahp_nazwa16w, ahp_nazwa_slow, ahp_powiat, prng_nazwa,
                    prng_powiat, ahp_prng_distance,prng)
                    VALUES ('{ahp_id}','{ahp_nazwa}','{ahp_nazwa16w}','{ahp_nazwa_slow}','{ahp_powiat}',
                    '{prng_nazwa}','{prng_powiat}',{ahp_prng_distance},'{zbiorcza_prng}');
                """
        cur_r.execute(sql_add)

    # if ahp_prng_distance > 3.0:
    #     licznik_distance +=1
    #     sql_add = f"""insert into wyniki (ahp_id, ahp_nazwa, ahp_nazwa16w, ahp_nazwa_slow, ahp_powiat, prng_nazwa,
    #                   prng_powiat, ahp_prng_distance,prng)
    #                   VALUES ('{ahp_id}','{ahp_nazwa}','{ahp_nazwa16w}','{ahp_nazwa_slow}','{ahp_powiat}',
    #                   '{prng_nazwa}','{prng_powiat}',{ahp_prng_distance},'{zbiorcza_prng}');
    #                """
    #     cur_r.execute(sql_add)

sql = """SELECT
            ahp_id, ahp_nazwa, ahp_nazwa16w, ahp_nazwa_slow, ahp_powiat, prng_nazwa,
            prng_powiat, ahp_prng_distance, prng
         FROM wyniki
         ORDER BY ahp_prng_distance DESC;
      """
cur_r.execute(sql)
wyniki = cur_r.fetchall()

print('ahp_id,ahp_nazwa,ahp_nazwa16w,ahp_nazwa_slow,ahp_powiat,prng,prng_nazwa,prng_powiat,ahp_prng_distance')
for row in wyniki:
    ahp_id = field_strip(row[0])
    ahp_nazwa = field_strip(row[1])
    ahp_nazwa16w = field_strip(row[2])
    ahp_nazwa_slow = field_strip(row[3])
    ahp_powiat = field_strip(row[4])
    prng_nazwa = field_strip(row[5])
    prng_powiat = field_strip(row[6])
    ahp_prng_distance = row[7]
    prng = field_strip(row[8])

    result = f'"{ahp_id}", "{ahp_nazwa}","{ahp_nazwa16w}","{ahp_nazwa_slow}","{ahp_powiat}","{prng}","{prng_nazwa}","{prng_powiat}",{ahp_prng_distance:.2f}'
    print(result)

print("AHP rows:", len(ahp_rows))
print("Nazwa:", licznik_nazwa)
print("Nazwa16w:", licznik_nazwa16w)
print("Nazwa slow:", licznik_nazwa_slow)
print("Distance:", licznik_distance)
