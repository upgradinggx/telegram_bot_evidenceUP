import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import gspread
from google.oauth2.service_account import Credentials

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_JSON = json.loads(os.environ['SERVICE_ACCOUNT_JSON'])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)

# Spreadsheet ID from env variable
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# Telegram bot token from env variable
TOKEN = os.environ.get("BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()

    peristiwa = data.get("peristiwa", "-")
    sub_divisi = data.get("sub divisi", "Project").capitalize()
    area = data.get("area", "-")
    catatan = data.get("catatan", "-")

    if sub_divisi not in ["Patrol", "Operational", "Project"]:
        sub_divisi = "Project"

    try:
        worksheet = spreadsheet.worksheet(sub_divisi)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sub_divisi, rows="100", cols="10")

    tanggal = update.message.date.strftime("%d/%m/%Y")
    row = [peristiwa, area, catatan, tanggal]
    worksheet.append_row(row)

    reply = (
        "📌 LAPORAN DITERIMA\n\n"
        f"Peristiwa: {peristiwa}\n"
        f"Sub Divisi: {sub_divisi}\n"
        f"Area: {area}\n"
        f"Catatan: {catatan}\n"
        f"Tanggal: {tanggal}\n\n"
        "Status & File bisa diisi manual di Google Sheet."
    )
    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
