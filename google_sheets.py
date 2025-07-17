import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("AI24Solutions_Leads").sheet1

def write_to_sheet(data):
    sheet.append_row([data['user_id'], data['message'], data['reply']])
