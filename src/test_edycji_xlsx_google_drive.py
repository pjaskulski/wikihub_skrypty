""" test połączenia z google api """
import pandas as pd

url = "https://docs.google.com/spreadsheets/d/1aSvr0tyYzkFGBWil26ZdCRngyDozq9_z/edit#gid=1316059203"
file_id = url.split("/")[-2]
path1 = "https://drive.google.com/uc?export=download&id=" + file_id

sp500_price = pd.read_excel(path1, engine='openpyxl')

