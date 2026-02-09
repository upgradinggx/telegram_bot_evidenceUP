import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from google.oauth2.service_account import Credentials
import gspread

# Setup Google Sheets API
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SERVICE_ACCOUNT_FILE = 'service_account.json'  # nanti file ini harus di-upload ke Render

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
gc = gspread.authorize(creds)

# Spreadsheet ID: dapat dari URL Google Sheet kamu
SPREADSHEET_ID = os.environ.get("1_0ulnjGWv6EiqZA1qxwzJTvrtWhP-dtM6HMo4bvCPtY")
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
    sub_divisi = data.get("sub divisi", "Project").capitalize()  # default ke Project kalau kosong
    area = data.get("area", "-")
    catatan = data.get("catatan", "-")

    # Tentukan sheet berdasarkan Sub Divisi
    if sub_divisi not in ["Patrol", "Operational", "Project"]:
        sub_divisi = "Project"

    try:
        worksheet = spreadsheet.worksheet(sub_divisi)
    except gspread.WorksheetNotFound:
        # Kalau sheet belum ada, buat baru
        worksheet = spreadsheet.add_worksheet(title=sub_divisi, rows="100", cols="10")

    # Ambil tanggal pesan diterima, format dd/mm/yyyy
    tanggal = update.message.date.strftime("%d/%m/%Y")

    # Data yang akan ditambahkan (Peristiwa, Area, Catatan, Tanggal)
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
