from dotenv import load_dotenv
import os
load_dotenv()

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from sheets import SheetsManager

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_JSON")

sheets = SheetsManager(CREDENTIALS_PATH, GOOGLE_SHEET_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "👋 ¡Bienvenido al *Bot de Finanzas*\n\n"
        "💸 *Comandos disponibles:*\n"
        "➕ *Registrar ingreso*: \n"
        "`+500 Recibí pago de Juan`\n\n"
        "➖ *Registrar egreso*: \n"
        "`-200 Compré proteína`\n\n"
        "📊 *Ver balance*: \n"
        "/balance\n\n"        
    )
    
    await update.message.reply_text(message, parse_mode="Markdown")
    
async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    
    if message.startswith("+"):
        type = 'Ingreso'
        try:
            amount, description = message[1:].strip().split(" ", 1)
            sheets.save_transfer(amount, type, description)
            await update.message.reply_text(f"Ingreso de {amount} registrado correctamente.")
        except :
            await update.message.reply_text("Formato incorrecto. Debes enviar + seguido de la cantidad y la descripción.")
    elif message.startswith("-"):
        type = 'Egreso'
        try:
            amount, description = message[1:].strip().split(" ", 1)
            sheets.save_transfer(amount, type, description)
            await update.message.reply_text(f"Egreso de {amount} registrado correctamente.")
        except :
            await update.message.reply_text("Formato incorrecto. Debes enviar - seguido de la cantidad y la descripción.")
    else:
        await update.message.reply_text("Formato incorrecto. Debes enviar + o - seguido de la cantidad y la descripción.")
        
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingresos, egresos, balance = sheets.get_balance()
    
    message = (
        f"💰 <b>Balance actual:</b>\n\n"
        f"<b>Ingresos:</b> {ingresos}\n"
        f"<b>Egresos:</b> {egresos}\n"
        f"<b>Saldo:</b> {balance}"
    )
    
    await update.message.reply_text(message, parse_mode="HTML")


def main():
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, register))
    app.add_handler(CommandHandler("balance", balance))
    app.run_polling()
    
    
if __name__ == "__main__":
    main()