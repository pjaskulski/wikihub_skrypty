""" test połączenia z google api """

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Connect to Google Sheets
scope = ['https://www.googleapis.com/auth/spreadsheets']

credentials_json = 'dane-do-importu-do-wikihum-10414f8acea1.json'
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_json, scope)
client = gspread.authorize(credentials)

sheet = client.open_by_url('https://docs.google.com/spreadsheets/d/1aSvr0tyYzkFGBWil26ZdCRngyDozq9_z')

print('OK')