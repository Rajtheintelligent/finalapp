import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import gspread
from google.oauth2.service_account import Credentials

# --- Setup Google Sheets ---
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]

creds = Credentials.from_service_account_file("service_account.json", scopes=scope)
client = gspread.authorize(creds)

# Open your Register sheet
register_url = "YOUR_REGISTER_SHEET_URL"
reg_book = client.open_by_url(register_url)
reg_ws = reg_book.worksheet("Register")

# --- Logging ---
logging.basicConfig(level=logging.INFO)

# --- Telegram Bot ---
BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    first_name = update.effective_user.first_name
    message = f"👋 Hello {first_name}! Your Telegram ID is: {chat_id}"

    # Tell parent their ID
    await update.message.reply_text(message)

    # (Optional) log into Register sheet automatically
    reg_ws.append_row([chat_id, first_name, ""])  # you can also ask for Student_ID later

    logging.info(f"Registered chat_id: {chat_id}")

if __name__ == "__main__":
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
