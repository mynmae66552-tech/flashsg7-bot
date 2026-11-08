import os
import json
import logging
import requests

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")

API_URL = "https://draw.ar-lottery01.com/TrxWinGo/TrxWinGo_1M/GetHistoryIssuePage.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://draw.ar-lottery01.com/",
    "Origin": "https://draw.ar-lottery01.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("trxbot")

# In-memory user state
user_state = {}


# ---------- API ----------
def fetch_history():
    """History API ကို ခေါ်ပြီး list ပြန်ပေး"""
    try:
        r = requests.get(API_URL, headers=HEADERS, timeout=15)
        log.info(f"API status: {r.status_code}")

        if r.status_code != 200:
            log.error(f"API body: {r.text[:300]}")
            return []

        data = r.json()

        if isinstance(data, list):
            return data

        if isinstance(data, dict):
            for path in [
                ("data", "list"),
                ("data", "data"),
                ("data",),
                ("list",),
                ("result", "list"),
            ]:
                cur, ok = data, True
                for k in path:
                    if isinstance(cur, dict) and k in cur:
                        cur = cur[k]
                    else:
                        ok = False
                        break
                if ok and isinstance(cur, list):
                    return cur

        log.warning(f"Unknown JSON: {json.dumps(data)[:300]}")
        return []

    except Exception as e:
        log.exception(f"fetch_history error: {e}")
        return []


def field(item, *names, default=None):
    """API field နာမည် အမျိုးမျိုး ဖြစ်နိုင်တာမို့ helper"""
    for n in names:
        if isinstance(item, dict) and n in item and item[n] not in (None, ""):
            return item[n]
    return default


def classify(num):
    """နောက်ဆုံးဂဏန်း 0-4 → SMALL, 5-9 → BIG"""
    try:
        last = int(str(num).strip()[-1])
    except (ValueError, IndexError, TypeError):
        return None
    return "BIG" if last >= 5 else "SMALL"


def predict(history):
    """Contrarian logic (ဥပမာ) — နောက်ဆုံး ၅ ပွဲ ကြည့်"""
    if not history:
        return None, "History မရပါ"

    big = small = 0
    for item in history[:5]:
        c = classify(field(item, "number", "num", "result", "code"))
        if c == "BIG":
            big += 1
        elif c == "SMALL":
            small += 1

    if big == 0 and small == 0:
        return None, "History format မမှန် (field နာမည် စစ်ပါ)"

    pred = "SMALL" if big > small else "BIG"
    reason = f"BIG:{big} / SMALL:{small} → contrarian"
    return pred, reason


def get_issue(item):
    return str(field(item, "issueNumber", "issue", "period", "expect", default=""))


# ---------- Handlers ----------
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **TRX WinGo Bot**\n\n`TRX` ရိုက်ပါ။",
        parse_mode="Markdown",
    )


async def handle_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = (update.message.text or "").strip().upper()

    if text != "TRX":
        await update.message.reply_text(
            "❌ `TRX` ပဲ ရိုက်ပါ။", parse_mode="Markdown"
        )
        return

    m = await update.message.reply_text("⏳ History ဆွဲနေတယ်...")
    hist = fetch_history()

    if not hist:
        await m.edit_text(
            "⚠️ API မရပါ။\n"
            "• 403 (bot block) ဖြစ်နိုင်တယ်\n"
            "• Console log စစ်ပါ။"
        )
        return

    pred, reason = predict(hist)
    if not pred:
        await m.edit_text(f"⚠️ {reason}")
        return

    user_state[chat_id] = {
        "pred": pred,
        "issue": get_issue(hist[0]),
        "hist": hist,
        "w": 0,
        "l": 0,
    }

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔮 Next", callback_data="next")]]
    )
    await m.edit_text(
        f"🎯 **TRX**\n"
        f"📊 **Prediction:** `{pred}`\n"
        f"📝 {reason}\n"
        f"🕒 Issue: `{user_state[chat_id]['issue']}`",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def on_next(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    chat_id = q.message.chat.id
    st = user_state.get(chat_id)

    if not st:
        await q.edit_message_text("⚠️ /start → `TRX` ရိုက်ပါ။",
                                  parse_mode="Markdown")
        return

    hist = fetch_history()
    txt = ""

    if not hist:
        txt = "⚠️ API မရလို့ result မစစ်နိုင်ပါ\n\n"
    else:
        latest = hist[0]
        li = get_issue(latest)
        if li and li != st["issue"]:
            actual = classify(field(latest, "number", "num", "result", "code"))
            if actual == st["pred"]:
                st["w"] += 1
                txt = f"✅ **WIN**  {st['pred']} → {actual}\n\n"
            else:
                st["l"] += 1
                txt = f"❌ **LOSS**  {st['pred']} → {actual}\n\n"
            st["hist"] = hist
            st["issue"] = li
        else:
            txt = "⏳ ပွဲအသစ် မရောက်သေးပါ\n\n"

    pred, reason = predict(st["hist"])
    st["pred"] = pred

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔮 Next", callback_data="next")]]
    )
    await q.edit_message_text(
        f"{txt}"
        f"🎯 **Next:** `{pred}`\n"
        f"📝 {reason}\n\n"
        f"📈 W: {st['w']} | L: {st['l']}",
        parse_mode="Markdown",
        reply_markup=kb,
    )


# ---------- Main ----------
def main():
    if not BOT_TOKEN:
        raise SystemExit("❌ BOT_TOKEN env မရှိပါ။ `export BOT_TOKEN=...` လုပ်ပါ။")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))
    app.add_handler(CallbackQueryHandler(on_next, pattern="^next$"))

    log.info("🤖 Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
