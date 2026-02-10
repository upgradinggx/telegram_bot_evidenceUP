import os
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    ContextTypes,
    filters
)
from google.oauth2.service_account import Credentials
import gspread

# =============================
# GOOGLE SHEETS SETUP
# =============================
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

SERVICE_ACCOUNT_JSON = json.loads(os.environ["SERVICE_ACCOUNT_JSON"])
creds = Credentials.from_service_account_info(
    SERVICE_ACCOUNT_JSON,
    scopes=SCOPES
)
gc = gspread.authorize(creds)

SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
spreadsheet = gc.open_by_key(SPREADSHEET_ID)

# =============================
# TELEGRAM BOT TOKEN
# =============================
TOKEN = os.environ.get("BOT_TOKEN")

# =============================
# /START COMMAND
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["/format"]
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    message = (
        "👋 Selamat datang di Bot Laporan!\n\n"
        "Bot ini digunakan untuk mengirim laporan peristiwa atau "
        "aktivitas kerja yang perlu didokumentasikan sebagai evidence.\n\n"
        "📋 Untuk melihat format laporan, silakan klik tombol "
        "atau ketik perintah:\n"
        "/format"
    )

    await update.message.reply_text(
        message,
        reply_markup=reply_markup
    )

# =============================
# /FORMAT COMMAND
# =============================
async def format_laporan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = (
        "📋 FORMAT LAPORAN\n\n"
        "Silakan kirim laporan dengan format berikut:\n\n"
        "Peristiwa:\n"
        "Sub Divisi:\n"
        "Kabupaten:\n"
        "Tikor:\n"
        "Catatan:\n\n"
        "📌 Sub Divisi: pilih satu Patrol / Operational / Project\n"
    )

    await update.message.reply_text(message)

# =============================
# MESSAGE HANDLER
# =============================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    # Parse pesan user ke dictionary
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            data[key.strip().lower()] = value.strip()

    # VALIDASI WAJIB
    if "peristiwa" not in data or "kabupaten" not in data:
        await update.message.reply_text(
            "⚠️ Format laporan belum sesuai.\n\n"
            "Silakan ketik /format untuk melihat contoh pengisian."
        )
        return

    peristiwa = data.get("peristiwa", "-")
    sub_divisi = data.get("sub divisi", "Project").capitalize()

    if sub_divisi not in ["Patrol", "Operational", "Project"]:
        sub_divisi = "Project"

    kabupaten = data.get("kabupaten", "-")
    tikor = data.get("tikor", "-")
    catatan = data.get("catatan", "-")

    # Ambil data Telegram (USERNAME SAJA)
    username = update.message.from_user.username or "-"
    tanggal = update.message.date.strftime("%d/%m/%Y")

    # Ambil / buat worksheet sesuai Sub Divisi
    try:
        worksheet = spreadsheet.worksheet(sub_divisi)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=sub_divisi,
            rows="100",
            cols="20"
        )

    # Simpan ke Google Sheet
    row = [
        peristiwa,
        kabupaten,
        tikor,
        catatan,
        username,
        tanggal
    ]
    worksheet.append_row(row)

    # Reply ke user (BERSIH)
    reply = (
        "📌 LAPORAN DITERIMA\n\n"
        f"Peristiwa: {peristiwa}\n"
        f"Kabupaten: {kabupaten}\n"
        f"Tikor: {tikor}\n"
        f"Catatan: {catatan}\n\n"
        "✅ Laporan sudah tercatat di Google Sheet."
    )

    await update.message.reply_text(reply)

# =============================
# BOT INIT
# =============================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("format", format_laporan))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
