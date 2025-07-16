from dotenv import load_dotenv
import os
load_dotenv()

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, ForceReply
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from sheets import SheetsManager

TOKEN_TELEGRAM = os.getenv("TOKEN_TELEGRAM")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
CREDENTIALS_PATH = os.getenv("CREDENTIALS_JSON")

sheets = SheetsManager(CREDENTIALS_PATH, GOOGLE_SHEET_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    init_keyboard = [["🔰 Iniciar Bot"]]
    
    reply_markup = ReplyKeyboardMarkup(init_keyboard, resize_keyboard=True)
    
    message = "👋 ¡Bienvenido al Bot de Finanzas!\n\nPresiona el botón para iniciar el bot."
    await update.message.reply_text(message, reply_markup=reply_markup, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    user_data = context.user_data
    
    if not user_data.get("iniciado"):
        init_keyboard = [["🔰 Iniciar Bot"]]
        reply_markup = ReplyKeyboardMarkup(init_keyboard, resize_keyboard=True)
        
        if message != "🔰 Iniciar Bot":
            await update.message.reply_text(
                "👋 ¡Hola! Presiona el botón para iniciar el bot.",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            return
        
        user_data["iniciado"] = True
        
        keyboard = [
            ["➕ Registrar ingreso", "➖ Registrar egreso"],
            ["📊 Ver balance"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("Bot iniciado. ¿Qué deseas hacer?", reply_markup=reply_markup)
        return
    
    
    if message == "➕ Registrar ingreso":
        user_data["modo"] = "Ingreso"
        await update.message.reply_text("¿Cuánto deseas registrar como ingreso?", reply_markup=ForceReply(selective=True))

    elif message == "➖ Registrar egreso":
        user_data["modo"] = "Egreso"
        await update.message.reply_text("¿Cuánto deseas registrar como egreso?", reply_markup=ForceReply(selective=True))

    elif message == "📊 Ver balance":
        await mostrar_balance(update, context)

    elif "esperando" in user_data:
        await procesar_flujo(update, context, message)

    elif "modo" in user_data:
        try:
            cantidad = float(message)
            user_data["cantidad"] = cantidad
            user_data["esperando"] = "descripcion"
            await update.message.reply_text("Perfecto. Ahora escribe una descripción:", reply_markup=ForceReply(selective=True))
        except:
            await update.message.reply_text("Por favor ingresa un número válido.")

    else:
        await update.message.reply_text("Usa los botones. Si quieres volver al menú escribe /start.")

async def procesar_flujo(update: Update, context: ContextTypes.DEFAULT_TYPE, message: str):
    user_data = context.user_data

    if user_data.get("esperando") == "descripcion":
        descripcion = message
        cantidad = user_data.get("cantidad")
        tipo = user_data.get("modo")

        sheets.save_transfer(cantidad, tipo, descripcion)

        await update.message.reply_text(f"✅ {tipo} de {cantidad} registrado con éxito: {descripcion}")

        # Limpiar estado
        for key in ["modo", "cantidad", "esperando", "estado_anterior"]:
            user_data.pop(key, None)
        
        # Volver al menú principal
        keyboard = [
            ["➕ Registrar ingreso", "➖ Registrar egreso"],
            ["📊 Ver balance"]
        ]
        
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("¿Quieres registrar otro movimiento o ver tu balance?", reply_markup=reply_markup)

async def mostrar_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ingresos, egresos, saldo = sheets.get_balance()

    mensaje = (
        f"💰 <b>Balance actual:</b>\n\n"
        f"<b>Ingresos:</b> {ingresos}\n"
        f"<b>Egresos:</b> {egresos}\n"
        f"<b>Saldo:</b> {saldo}"
    )

    await update.message.reply_text(mensaje, parse_mode="HTML")

def main():
    app = ApplicationBuilder().token(TOKEN_TELEGRAM).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
