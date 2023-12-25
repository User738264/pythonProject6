import os
import apiclient
import gspread
import httplib2
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv, find_dotenv, dotenv_values
import os

load_dotenv(find_dotenv())

CREDENTIALS_FILE = 'data/creds1.json'
spreadsheet_id = os.getenv('SPREADSHEET_ID')

# Авторизуемся и получаем service — экземпляр доступа к API
credentials = ServiceAccountCredentials.from_json_keyfile_name(
    CREDENTIALS_FILE,
    ['https://www.googleapis.com/auth/spreadsheets',
     'https://www.googleapis.com/auth/drive'])
httpAuth = credentials.authorize(httplib2.Http())
service = apiclient.discovery.build('sheets', 'v4', http=httpAuth)
gc = gspread.service_account(filename=CREDENTIALS_FILE)
ws = gc.open_by_key(spreadsheet_id).worksheet('тест')

rating_sheet = gc.open_by_key(spreadsheet_id).worksheet('рейтинг')
