import os
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
import gspread
from google.oauth2.service_account import Credentials

# ===== Setup Google Sheets API =====
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

try:
    SERVICE_ACCOUNT_JSON = json.loads(os.environ['SERVICE_ACCOUNT_JSON'])
except Exception as e:
    print("❌ Error membaca SERVICE_ACCOUNT_JSON:", e)
    SERVICE_ACCOUNT_JSON = None

creds = None
gc = None
if SERVICE_ACCOUNT_JSON:
    try:
        creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_JSON, scopes=SCOPES)
        gc = gspread.authorize(creds)
    except Exception as e:
        print("❌ Error authorize gspread:", e)

# ===== Spreadsheet ID =====
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")
if not SPREADSHEET_ID:
    print("❌ SPREADSHEET_ID environment variable tidak ditemukan")

spreadsheet = None
if gc and SPREADSHEET_ID:
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
    except Exception as e:
        print("❌ Error membuka spreadsheet:", e)

# ===== Telegram Bot Token =====
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    print("❌ BOT_TOKEN environment variable tidak ditemukan")

# ===== Handler Pesan =====
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
    area = data.get("area", "-")
    catatan = data.get("catatan", "-")

    # Debug info
    print("💬 Pesan diterima:", text)
    print("📂 Sub Divisi:", sub_divisi)
    print("🗂 Target spreadsheet:", SPREADSHEET_ID)

    reply = f"📌 LAPORAN DITERIMA\nPeristiwa: {peristiwa}\nSub Divisi: {sub_divisi}\nArea: {area}\nCatatan: {catatan}"

    if spreadsheet:
        try:
            # Pastikan worksheet/tab ada
            try:
                worksheet = spreadsheet.worksheet(sub_divisi)
            except gspread.WorksheetNotFound:
                print(f"ℹ️ Worksheet '{sub_divisi}' tidak ditemukan, membuat baru")
                worksheet = spreadsheet.add_worksheet(title=sub_divisi, rows="100", cols="10")

            # Ambil tanggal
            tanggal = update.message.date.strftime("%d/%m/%Y")

            # Row data
            row = [peristiwa, area, catatan, tanggal]
            print("📊 Row akan ditulis:", row)

            worksheet.append_row(row)
            reply += f"\nTanggal: {tanggal}\nStatus & File bisa diisi manual di Sheet."

        except Exception as e:
            print("❌ Error append row:", e)
            reply += f"\n❌ Gagal menulis ke Sheet: {e}"

    else:
        reply += "\n❌ Spreadsheet tidak tersedia atau belum terhubung."

    await update.message.reply_text(reply)

# ===== Jalankan bot =====
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
print("✅ Bot dijalankan...")
app.run_polling()
