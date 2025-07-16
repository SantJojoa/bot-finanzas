import gspread

from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

class SheetsManager:
    def __init__(self, creds_path, sheet_name):
        scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
        client = gspread.authorize(creds)
        self.sheet = client.open_by_key(sheet_name).sheet1
        
        
    def save_transfer(self, amount, type, description):
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_amount = f"${int(amount):,} COP".replace(",", ".")
        self.sheet.append_row([date, formatted_amount, type, description])
        
    def get_balance(self):
        registers = self.sheet.get_all_values()[1:]
        
        ingresos = 0
        egresos = 0
        
        
        for row in registers:
            amount = float(row[1])
            type = row[2]
            
            if type == 'Ingreso':
                ingresos += amount
            elif type == 'Egreso':
                egresos += amount
        
        balance = ingresos - egresos
        return ingresos, egresos, balance
    
    
    def get_all_records(self):
        registros = self.sheet.get_all_values()[1:]  # Saltar cabecera
        return registros
        
        