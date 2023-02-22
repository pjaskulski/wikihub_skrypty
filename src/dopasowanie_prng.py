""" wyszukiwanie nowych połączeń AHP - PRNG """
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


def get_rows(db, szukana_nazwa:str, lev_dist:int=2) -> list:
    """ wyszukiwanie w bazie PRNG według podanej nazwy z uwzględnieniem przybliżeń
        db - obiekt bazy sqlite
        szukana_nazwa - nazwa do wyszukiwania z przybliżeniami
        lev_dist - dopuszczalna odlgłość Levensteina
    """

    sql_leven = f"""
                SELECT NAZWAGLOWN as prng_nazwa, POWIAT as prng_powiat, PRNG, WGS84
                FROM miejscowosci_wspolna
                WHERE
                (levenshtein(translit(LOWER(NAZWAGLOWN)), translit('{szukana_nazwa.lower()}')) <= {lev_dist})
    """
    cur_prng = db.cursor()
    cur_prng.execute(sql_leven)
    results = cur_prng.fetchall()
    return results


def process_rows(result_rows, best_min_dist, org_ahp_prng) -> tuple:
    """ przetwarzanie wyników zapytania """
    result = (False, '', '', '')

    for result_row in result_rows:
        result_prng = result_row[2]
        # jeżeli to ten sam PRNG co już jest w AHP to nie ma potrzeby przetwarzania
        if result_prng == org_ahp_prng:
            continue
        result_nazwa = field_strip(result_row[0])
        result_powiat = field_strip(result_row[1])
        result_WGS84 = field_strip(result_row[3])
        dist = calculate_distance(ahp_WGS84, result_WGS84)
        if dist < best_min_dist:
            best_min_dist = dist
            result =  (True, dist, result_prng, result_nazwa, result_powiat)

    return result


# ------------------------------------MAIN -------------------------------------
if __name__ == '__main__':

    # wynik w pliku tekstowym (ścieżka do pliku)
    output_path = Path('..') / 'data' / 'dopasowanie_prng_v3.csv'
    # dane
    miejscowosci_path = Path('..') / 'data' / 'ahp_zbiorcza.sqlite'
    db = create_connection(miejscowosci_path, with_extension=True)

    sql = """SELECT
            ahp_zbiorcza_pkt_prng_import.id_miejscowosci,
            ahp_zbiorcza_pkt_prng_import.zbiorcza_prng,
            ahp_zbiorcza_pkt_prng_import.nazwa_wspolczesna,
            ahp_zbiorcza_pkt_prng_import.nazwa_16w,
            ahp_zbiorcza_pkt_prng_import.nazwa_odmianki,
            ahp_zbiorcza_pkt_prng_import.powiat_p,
            ahp_zbiorcza_pkt_prng_import.ahp_pkt_WGS84,
            ahp_zbiorcza_pkt_prng_import.nazwa_slownikowa,
            miejscowosci_wspolna.WGS84,
            miejscowosci_wspolna.NAZWAGLOWN
        FROM ahp_zbiorcza_pkt_prng_import
        INNER JOIN miejscowosci_wspolna ON ahp_zbiorcza_pkt_prng_import.zbiorcza_prng = miejscowosci_wspolna.PRNG
        """
    cur = db.cursor()
    cur.execute(sql)
    ahp_rows = cur.fetchall()

    licznik = 0
    licznik_total = 0
    ahp_count = len(ahp_rows)

    for row in ahp_rows:
        licznik_total += 1
        ahp_id = field_strip(row[0])
        ahp_zbiorcza_prng = field_strip(row[1])
        ahp_nazwa = field_strip(row[2])
        ahp_nazwa16w = field_strip(row[3])
        ahp_odmianki = field_strip(row[4])
        ahp_powiat = field_strip(row[5])
        ahp_WGS84 = field_strip(row[6])
        ahp_nazwa_slow = field_strip(row[7])
        ahp_prng_WGS84 = field_strip(row[8]) # współrzędne punktu PRNG przypiętego do AHP
        ahp_prng_nazwa = field_strip(row[9])
        ahp_prng_distance = calculate_distance(ahp_WGS84, ahp_prng_WGS84) # odległość punktów AHP i PRNG

        # status przetwarzania
        print(f'({licznik_total}/{ahp_count}/{licznik}) przetwarzam: {ahp_id} {ahp_nazwa} {ahp_prng_distance}')

        # flaga czy znaleziono bardziej pasujący PRNG
        is_diff = False

        # początkowa wartość minimalnej odległości ustawiona na odległość dla
        # pary punktów AHP-PRNG z bazy AHP
        min_distance = ahp_prng_distance

        find_prng = ''
        find_prng_nazwa = ''
        find_prng_powiat = ''

        # wyszukiwanie w bazie PRNG według nazwy współczesnej w AHP
        prng_rows = get_rows(db, ahp_nazwa, lev_dist=2)

        # wyszukiwanie w bazie PRNG według nazwy z XVI wieku w AHP
        prng_rows_2 = get_rows(db, ahp_nazwa16w, lev_dist=2)
        prng_rows.extend(prng_rows_2)

        # wyszukiwanie w bazie PRNG według nazwy słownikowej w PRNG
        prng_rows_3 = get_rows(db, ahp_nazwa_slow, lev_dist=2)
        prng_rows.extend(prng_rows_3)

        # w wynikach wyszukiwanie najbardziej pasujących PRNG wg odległości punktów
        res = process_rows(prng_rows, min_distance, ahp_zbiorcza_prng)
        if res[0]:
            _, min_distance, find_prng, find_prng_nazwa, find_prng_powiat = res

        # jeżeli znaleziono punkt PRNG i jest on inny niż przypisany w AHP i jego odległość
        # od punktu AHP jest mniejsza od odległości między punktem AHP i punktem przypisanym w AHP
        if (find_prng and
            find_prng != ahp_zbiorcza_prng and
            min_distance < ahp_prng_distance):
            is_diff = True

        # jeżeli znaleziono to zapis wyników
        if is_diff:
            licznik += 1

            with open(output_path, 'a', encoding='utf-8') as f:
                result = f'"{ahp_id}","{ahp_nazwa}","{ahp_nazwa16w}","{ahp_nazwa_slow}","{ahp_powiat}","{ahp_zbiorcza_prng}","{ahp_prng_nazwa}",{ahp_prng_distance:.2f},"{find_prng_nazwa}","{find_prng_powiat}","{find_prng}",{min_distance:.2f}\n'
                f.write(result)

    print("AHP rows:", len(ahp_rows))
    print("Znaleziono inny PRNG:", licznik)
