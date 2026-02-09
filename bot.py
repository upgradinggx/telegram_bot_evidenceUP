import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from google.oauth2.service_account import Credentials
import gspread

# Setup Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_JSON = json.loads(os.environ['SERVICE_ACCOUNT_JSON'])
creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
spreadsheet = gc.open_by_key(SPREADSHEET_ID)
TOKEN = os.environ.get("BOT_TOKEN")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Parse pesan jadi dictionary
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()

    peristiwa = data.get("peristiwa", "-")
    sub_divisi = data.get("sub divisi", "Project").capitalize()
    if sub_divisi not in ["Patrol", "Operational", "Project"]:
        sub_divisi = "Project"
    area = data.get("area", "-")
    tikor = data.get("tikor", "-")
    catatan = data.get("catatan", "-")
    nama_pengirim = data.get("nama pengirim", update.message.from_user.full_name)
    username = update.message.from_user.username or "-"
    tanggal = update.message.date.strftime("%d/%m/%Y")

    # Ambil worksheet sesuai Sub Divisi
    try:
        worksheet = spreadsheet.worksheet(sub_divisi)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(title=sub_divisi, rows="100", cols="20")

    # Row data
    row = [peristiwa, sub_divisi, area, tikor, catatan, nama_pengirim, username, tanggal]

    worksheet.append_row(row)

    reply = (
        "📌 LAPORAN DITERIMA\n\n"
        f"Peristiwa: {peristiwa}\n"
        f"Sub Divisi: {sub_divisi}\n"
        f"Area: {area}\n"
        f"Tikor: {tikor}\n"
        f"Catatan: {catatan}\n"
        f"Nama Pengirim: {nama_pengirim}\n"
        f"Username: {username}\n"
        f"Tanggal: {tanggal}\n\n"
        "Tercatat di Google Sheet."
    )

    await update.message.reply_text(reply)

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()
