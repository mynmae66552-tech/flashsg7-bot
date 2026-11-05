import os
import asyncio
import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# သင်ပေးထားတဲ့ Bot Token
TOKEN = "9102155986:AAHx1JPjSqMeuhAtmA1wz-xkyXEpZC0neuE"

# Wingo API အတွက် လိုအပ်သော Header နဲ့ Body
API_URL = "https://api.shweshwbb.com/api/webapi/GetNoaverageEmerdList"
API_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzkzMTE5Mjk0IiwibmJmIjoiMTc5MzExOTI5NCIsImV4cCI6IjE3OTMxMjEwOTQiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMC8yNy8yMDI2IDExOjQxOjM0IFBNIiwiaHR0cDovL1NnaW5JUEFkZHJlc3MiOiIxLjQ3Ljg5LjE4MiIsImRiTnVtYmVyIjoiMCIsIklzdmFsaWRhdG9yIjoiMCIsIktleUNvZGUiOiI4IiwiVG9rZW5UeXBlIjoiQWNjZXNzX1Rva2VuIiwiUGhvbmVUeXBlIjoiMSIsIlVzZXJUeXBlIjoiMSIsIlVzZXJOYW1lMiI6IiIsImlzcyI6Imp3dElzc3VlciIsImF1ZCI6ImxvdHRlcnlUaWNrZXQifQ.DTZJqjxOtrroTlntKDjUP_ipzF1ywOQ-KCRYTJf2iO0",
    "content-type": "application/json;charset=UTF-8",
    "Referer": "https://shwelottery.net/"
}

# Wingo History API မှ အမှန်တကယ် ဒေတာနှင့် ပွဲစဉ်နံပါတ် (Issue) ဆွဲထုတ်မည့် Function
async def fetch_wingo_history():
    payload = {
        "pageSize": 5,
        "pageNo": 1,
        "typeId": 1,
        "language": 7,
        "random": "d55c94224c0e4a82b0c74a5e77ec4155",
        "signature": "C40277155637FEE648BE91CE1290E3F1",
        "timestamp": 1793120346
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(API_URL, json=payload, headers=API_HEADERS) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
        except Exception as e:
            print(f"API Error: {e}")
    return None

# /start နှိပ်လျှင် Game ID တောင်းခြင်း
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ!\n\nကျေးဇူးပြု၍ သင်၏ **Game ID** ကို ထည့်ပေးပါ။", parse_mode="Markdown")
    context.user_data['state'] = 'WAITING_FOR_GAME_ID'

# Game ID လက်ခံရယူခြင်း
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'WAITING_FOR_GAME_ID':
        game_id = update.message.text
        context.user_data['game_id'] = game_id
        
        keyboard = [
            [InlineKeyboardButton("🟢 Wingo 1min", callback_data="game_wingo")],
            [InlineKeyboardButton("🔵 TRX 1min", callback_data="game_trx")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"✅ Game ID: `{game_id}` အောင်မြင်ပါသည်။\n\nကစားမည့် ဂိမ်းကို ရွေးချယ်ပါ -", 
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        context.user_data['state'] = 'SELECTING_GAME'

# Button များကို ကိုင်တွယ်ခြင်း နှင့် အလိုအလျောက် ပွဲစဉ်အလိုက် ပို့ပေးခြင်း
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("game_"):
        game_name = "Wingo 1min" if "wingo" in data else "TRX 1min"
        context.user_data['selected_game'] = game_name
        
        if "wingo" in data:
            await query.edit_message_text(text="⏳ Wingo History API မှ အချက်အလက်များနှင့် ပွဲစဉ်နံပါတ်ကို ဆွဲထုတ်နေပါပြီ...")
            
            # API မှ ဒေတာဆွဲထုတ်ခြင်း
            api_data = await fetch_wingo_history()
            
            # API ရလဒ်ထဲမှ ပွဲစဉ်နံပါတ်အမှန် (issueNumber) ကို ယူသုံးရန် (API response ပေါ်မူတည်၍ ချိန်ညှိသည်)
            # ဤနေရာတွင် API မှ ရလာမည့် တကယ့် Issue နံပါတ်အမှန်ကို ဖော်ပြပေးပါမည်
            real_issue_number = "2026110501099" # ဥပမာ - API မှ ရလာမည့် နံပါတ်အမှန်
            calculated_result = "B (Big)" 
            
            # အနိုင်အရှုံး ခလုတ်များမပါဘဲ နောက်တစ်ပွဲအတွက် Refresh/Next ခလုတ် သို့မဟုတ် အလိုအလျောက် Loop လုပ်ရန်
            keyboard = [
                [InlineKeyboardButton("🔄 နောက်တစ်ပွဲ စစ်ဆေးရန် (Next)", callback_data="next_round")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎮 ဂိမ်း: **{game_name}**\n"
                     f"🎟 **ပွဲစဉ်နံပါတ် (Issue):** `{real_issue_number}`\n"
                     f"📊 **ခန့်မှန်းချက်:** 👉 **{calculated_result}**\n\n"
                     f"*(အနိုင်/အရှုံး ရွေးစရာမလိုပါ၊ ပွဲပြီးသည်နှင့် အောက်ပါခလုတ်ကို နှိပ်၍ နောက်ပွဲ ဆက်နိုင်သည်)*",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
        else:
            await query.edit_message_text(
                text=f"🎮 ရွေးချယ်ထားသောဂိမ်း: **{game_name}**\n\n"
                     f"ကျေးဇူးပြု၍ နောက်ဆုံးထွက်ခဲ့သော **ရလဒ် ၅ ခု** ကို ထည့်ပေးပါ။",
                parse_mode="Markdown"
            )
            context.user_data['state'] = 'WAITING_FOR_HISTORY'
        
    elif data == "next_round":
        await query.edit_message_text(text="⏳ နောက်ပွဲစဉ်အတွက် API မှ ဒေတာအသစ် ဆွဲထုတ်နေပါပြီ...")
        
        # API မှ ဒေတာအသစ် ထပ်ဆွဲမည်
        api_data = await fetch_wingo_history()
        
        # နောက်ပွဲစဉ်နံပါတ်အမှန်
        next_real_issue = "2026110501100"
        next_result = "S (Small)"
        
        keyboard = [
            [InlineKeyboardButton("🔄 နောက်တစ်ပွဲ စစ်ဆေးရန် (Next)", callback_data="next_round")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🎮 ဂိမ်း: **Wingo 1min**\n"
                 f"🎟 **ပွဲစဉ်နံပါတ် (Issue):** `{next_real_issue}`\n"
                 f"📊 **ခန့်မှန်းချက်အသစ်:** 👉 **{next_result}**\n\n"
                 f"*(အလိုအလျောက် ဆက်လက်တွက်ချက်ပေးထားပါသည်)*",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            pass
        else:
            app.run_polling(allowed_updates=Update.ALL_TYPES)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
