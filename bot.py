from dotenv import load_dotenv
import os
load_dotenv()

if not os.path.exists("credentials.json"):
    with open("credentials.json", "w") as f:
        f.write(os.getenv("CREDENTIALS_JSON_RAW"))

from telegram import Update, ReplyKeyboardMarkup, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from sheets import SheetsManager
from exporter import generate_pdf

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_JSON")

sheets = SheetsManager(CREDENTIALS_PATH, GOOGLE_SHEET_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = context.user_data
    user_data.clear()  # Limpiar estado al hacer /start

    init_keyboard = [["🔰 Iniciar Bot"]]
    reply_markup = ReplyKeyboardMarkup(init_keyboard, resize_keyboard=True)

    message = "👋 ¡Bienvenido al Bot de Finanzas!\n\nPresiona el botón para iniciar el bot."
    await update.message.reply_text(message, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user_data = context.user_data

    if not user_data.get("iniciado"):
        if message != "🔰 Iniciar Bot":
            init_keyboard = [["🔰 Iniciar Bot"]]
            reply_markup = ReplyKeyboardMarkup(init_keyboard, resize_keyboard=True)

            await update.message.reply_text(
                "👋 ¡Hola! Por favor, presiona el botón para iniciar el bot.",
                reply_markup=reply_markup
            )
            return
        
        # El usuario presionó "Iniciar Bot"
        user_data["iniciado"] = True
        
        keyboard = [
            ["➕ Registrar ingreso", "➖ Registrar egreso"],
            ["📊 Ver balance", "📄 Exportar PDF"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("✅ Bot iniciado correctamente. ¿Qué deseas hacer?", reply_markup=reply_markup)
        return

    # Si ya está iniciado, sigue el flujo normal
    if "esperando" in user_data:
        await procesar_flujo(update, context, message)
        return

    if message == "➕ Registrar ingreso":
        user_data["modo"] = "Ingreso"
        await update.message.reply_text("¿Cuánto deseas registrar como ingreso?", reply_markup=ForceReply(selective=True))

    elif message == "➖ Registrar egreso":
        user_data["modo"] = "Egreso"
        await update.message.reply_text("¿Cuánto deseas registrar como egreso?", reply_markup=ForceReply(selective=True))

    elif message == "📊 Ver balance":
        await mostrar_balance(update, context)

    elif message == "📄 Exportar PDF":
        await exportar_pdf(update, context)

    elif "modo" in user_data:
        try:
            cantidad = float(message.replace(",", "").replace("$", ""))
            user_data["cantidad"] = cantidad
            user_data["esperando"] = "descripcion"
            await update.message.reply_text("Perfecto. Ahora escribe una descripción:", reply_markup=ForceReply(selective=True))
        except ValueError:
            await update.message.reply_text("Por favor ingresa un número válido (puedes usar puntos o comas).")
    
    else:
        await update.message.reply_text("Usa los botones del menú o escribe /start para reiniciar.")

async def procesar_flujo(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    user_data = context.user_data

    if user_data.get("esperando") == "descripcion":
        descripcion = message
        cantidad = user_data.get("cantidad")
        tipo = user_data.get("modo")

        sheets.save_transfer(cantidad, tipo, descripcion)

        await update.message.reply_text(f"✅ {tipo} de {format_cop(cantidad)} registrado con éxito: {descripcion}")

        # Limpiar estado del flujo pero mantener iniciado = True
        for key in ["modo", "cantidad", "esperando"]:
            user_data.pop(key, None)

        # Menú principal
        keyboard = [
            ["➕ Registrar ingreso", "➖ Registrar egreso"],
            ["📊 Ver balance", "📄 Exportar PDF"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("¿Quieres registrar otro movimiento o ver tu balance?", reply_markup=reply_markup)

async def mostrar_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingresos, egresos, saldo = sheets.get_balance()

    mensaje = (
        f"💰 <b>Balance actual:</b>\n\n"
        f"<b>Ingresos:</b> {format_cop(ingresos)}\n"
        f"<b>Egresos:</b> {format_cop(egresos)}\n"
        f"<b>Saldo:</b> {format_cop(saldo)}"
    )

    await update.message.reply_text(mensaje, parse_mode="HTML")

async def exportar_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingresos, egresos, saldo = sheets.get_balance()
    registros = sheets.get_all_records()

    filename = "reporte_finanzas.pdf"
    generate_pdf(ingresos, egresos, saldo, registros, filename)

    await update.message.reply_document(open(filename, "rb"))

def format_cop(amount):
    return f"${int(amount):,} COP".replace(",", ".")

def main():
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
