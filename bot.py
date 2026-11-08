import os
import logging
import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Render က ပေးတဲ့ URL ကို အလိုအလျောက် ယူမယ်
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL") 
PORT = int(os.environ.get("PORT", 8000))
API_URL = "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json"

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("trxbot")

user_state = {}
# ... (သင့်ရဲ့ fetch_history, predict, get_issue နဲ့ handler တွေကို ဒီမှာ ဆက်ထည့်ပါ) ...

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 **TRX WinGo Bot**\n\n`TRX` ရိုက်ပါ။", parse_mode="Markdown")

async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # (သင့်ရဲ့ မူရင်း handle_msg code ကို ဒီမှာ ထည့်ပါ)
    pass

async def on_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # (သင့်ရဲ့ မူရင်း on_next code ကို ဒီမှာ ထည့်ပါ)
    pass

# ---------- Webhook Setup ----------
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
application.add_handler(CallbackQueryHandler(on_next, pattern="^next$"))

async def telegram_webhook(request: Request):
    """Telegram ဆီက Update တွေကို လက်ခံမယ်"""
    data = await request.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return Response(status_code=200)

# သင့် Token အတွက် Webhook URL ကို Telegram မှာ သတ်မှတ်မယ်
async def on_startup():
    await application.initialize()
    await application.bot.set_webhook(f"{RENDER_URL}/{BOT_TOKEN}")
    log.info("Webhook set successfully!")

app = Starlette(
    routes=[Route(f"/{BOT_TOKEN}", telegram_webhook, methods=["POST"])],
    on_startup=[on_startup],
)

if __name__ == "__main__":
    log.info("🚀 Starting webhook server...")
    uvicorn.run(app, host="0.0.0.0", port=PORT)
