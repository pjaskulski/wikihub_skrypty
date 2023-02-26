""" dopasowanie ahp - prng z użyciem pandas """
from pathlib import Path
import pandas as pd
from rapidfuzz import process
import geopy.distance
from tqdm import tqdm


def calculate_distance(point_ahp, point_prng) -> float:
    """ oblicza odległość między dwoma punktami, wynik w km """
    if pd.isna(point_ahp) or pd.isna(point_prng):
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


def select_name(nazwa_wsp, nazwa_16, nazwa_slow) -> str:
    """ select name """
    result = ''
    if not pd.isna(nazwa_wsp):
        result = nazwa_wsp
    elif not pd.isna(nazwa_16):
        result = nazwa_16
    elif not pd.isna(nazwa_slow):
        result = nazwa_slow

    return result


def get_best(text, min_dist, ahp_prng_WGS84):
    """ get_best """
    best_prng = ''
    result = process.extract(text, df_prng['NAZWAGLOWN'], score_cutoff=90)
    for item in result:
        name, score, line_number = item
        prng = df_prng['PRNG'][line_number]
        prng_WGS84 = df_prng['WGS84'][line_number]
        dist = calculate_distance(ahp_prng_WGS84, prng_WGS84)
        if dist < min_dist:
            min_dist = dist
            best_prng = prng

    return best_prng


tqdm.pandas()

ahp_path = Path('..') / 'data' / 'ahp_zbiorcza_prng.csv'
prng_path = Path('..') / 'data' / 'miejscowosci_wspolna_p.csv'
output_path = Path('..') / 'data' / 'wynik.csv'

df_ahp = pd.read_csv(ahp_path, sep=',', header=0)
df_prng = pd.read_csv(prng_path, sep=',', header=0, low_memory=False)

df_ahp['ahp_prng_dist'] = df_ahp.progress_apply(lambda row: calculate_distance(row['ahp_pkt_WGS84'], row['WGS84']), axis=1)
df_ahp['nazwa_analiza'] = df_ahp.progress_apply(lambda row: select_name(row['nazwa_wspolczesna'], row['nazwa_16w'], row['nazwa_slownikowa']), axis=1)

df_ahp['new_prng'] = df_ahp.progress_apply(lambda row: get_best(row['nazwa_analiza'], row['ahp_prng_dist'], row['ahp_pkt_WGS84']), axis=1)

df_ahp.to_csv(output_path)
