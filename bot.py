from dotenv import load_dotenv
import os
load_dotenv()



if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        f.write(os.getenv("CREDENTIALS_JSON_RAW"))

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from sheets import SheetsManager

from exporter import generate_pdf


TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_JSON")

sheets = SheetsManager(CREDENTIALS_PATH, GOOGLE_SHEET_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["Iniciar Bot 🤖"]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    message = "👋 ¡Bienvenido al Bot de Finanzas!\n\nPresiona el botón para iniciar el bot."
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user_data = context.user_data

    # Si aún no ha iniciado el bot
    if not user_data.get("iniciado"):
        if message == "Iniciar Bot 🤖":
            user_data["iniciado"] = True

            keyboard = [
                ["➕ Registrar ingreso", "➖ Registrar egreso"],
                ["📊 Ver balance", "📄 Exportar PDF"]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)
        else:
            await update.message.reply_text("Presiona el botón para iniciar el bot, Zozorrita.")
        return

    # Si está esperando la cantidad
    if user_data.get("esperando") == "cantidad":
        try:
            cantidad = float(message)
            user_data["cantidad"] = cantidad
            user_data["esperando"] = "descripcion"

            await update.message.reply_text("Perfecto, Zozorrita. Ahora escribe una descripción para este movimiento:", reply_markup=ForceReply(selective=True))
        except:
            await update.message.reply_text("Por favor ingresa un número válido, Zozorrita.")
        return

    # Si está esperando la descripción
    if user_data.get("esperando") == "descripcion":
        descripcion = message
        cantidad = user_data["cantidad"]
        tipo = user_data["tipo"]

        sheets.save_transfer(cantidad, tipo, descripcion)

        await update.message.reply_text(f"{tipo} de ${int(cantidad):,} COP registrado con éxito: {descripcion}".replace(",", "."))

        # Limpiar flujo y volver al menú
        user_data.pop("esperando", None)
        user_data.pop("cantidad", None)
        user_data.pop("tipo", None)

        await mostrar_menu(update)
        return

    # Opciones del menú principal
    if message == "➕ Registrar ingreso":
        user_data["tipo"] = "Ingreso"
        user_data["esperando"] = "cantidad"
        await update.message.reply_text("¿Cuánto deseas registrar como ingreso?")

    elif message == "➖ Registrar egreso":
        user_data["tipo"] = "Egreso"
        user_data["esperando"] = "cantidad"
        await update.message.reply_text("¿Cuánto deseas registrar como egreso?")

    elif message == "📊 Ver balance":
        await mostrar_balance(update)

    elif message == "📄 Exportar PDF":
        await exportar_pdf(update)

    else:
        await update.message.reply_text("Usa los botones, Zozorrita.")

async def mostrar_menu(update: Update):
    keyboard = [
        ["➕ Registrar ingreso", "➖ Registrar egreso"],
        ["📊 Ver balance", "📄 Exportar PDF"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text("Selecciona una opción:", reply_markup=reply_markup)

async def mostrar_balance(update: Update):
    ingresos, egresos, saldo = sheets.get_balance()

    mensaje = (
        f"💰 <b>Balance actual:</b>\n\n"
        f"<b>Ingresos:</b> ${int(ingresos):,} COP\n"
        f"<b>Egresos:</b> ${int(egresos):,} COP\n"
        f"<b>Saldo:</b> ${int(saldo):,} COP"
    ).replace(",", ".")

    await update.message.reply_text(mensaje, parse_mode="HTML")

async def exportar_pdf(update: Update):
    ingresos, egresos, saldo = sheets.get_balance()
    registros = sheets.sheet.get_all_values()[1:]

    filename = "reporte_finanzas.pdf"
    generate_pdf(ingresos, egresos, saldo, registros, filename)

    with open(filename, "rb") as pdf:
        await update.message.reply_document(pdf, filename=filename)

def main():
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()