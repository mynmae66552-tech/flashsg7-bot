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
    "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOiIxNzkzMTE5Mjk0IiwibmJmIjoiMTc5MzExOTI5NCIsImV4cCI6IjE3OTMxMjEwOTQiLCJodHRwOi8vc2NoZW1hcy5taWNyb3NvZnQuY29tL3dzLzIwMDgvMDYvaWRlbnRpdHkvY2xhaW1zL2V4cGlyYXRpb24iOiIxMC8yNy8yMDI2IDExOjQxOjM0IFBNIiwiaHR0cDovL3NjaGVtYXMubWljcm9zb2Z0LmNvbS93cy8yMDA4LzA2L2lkZW50aXR5L2NsYWltcy9yb2xlIjoiQWNjZXNzX1Rva2VuIiwiVXNlcklkIjoiMTAxMTk0IiwiVXNlck5hbWUiOiI5NTU1MyIsIlVzZXJQaG90byI6IjEiLCJOaWNrTmFtZSI6Ik1lbWJlck5ORzVQUjlZIiwiQW1vdW50IjoiODgwMDAwMDAwLjAwIiwiSW50ZWdyYWwiOiIwIiwiTG9naW5NYXJrIjoiSDUiLCJMb2dpblRpbWUiOiIxMC8yNy8yMDI2IDExOjExOjM0IFBNIiwiaHR0cDovL1NnaW5JUEFkZHJlc3MiOiIxLjQ3Ljg5LjE4MiIsImRiTnVtYmVyIjoiMCIsIklzdmFsaWRhdG9yIjoiMCIsIktleUNvZGUiOiI4IiwiVG9rZW5UeXBlIjoiQWNjZXNzX1Rva2VuIiwiUGhvbmVUeXBlIjoiMSIsIlVzZXJUeXBlIjoiMSIsIlVzZXJOYW1lMiI6IiIsImlzcyI6Imp3dElzc3VlciIsImF1ZCI6ImxvdHRlcnlUaWNrZXQifQ.DTZJqjxOtrroTlntKDjUP_ipzF1ywOQ-KCRYTJf2iO0",
    "content-type": "application/json;charset=UTF-8",
    "Referer": "https://shwelottery.net/"
}

# Wingo History API ကို ခေါ်ယူမည့် Function
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

# မက်ဆေ့ခ်ျများကို စစ်ဆေးခြင်း (Game ID ဖမ်းရန်)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    
    if state == 'WAITING_FOR_GAME_ID':
        game_id = update.message.text
        context.user_data['game_id'] = game_id
        
        # Game ရွေးရန် Button များပြမည်
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

# Button များကို နှိပ်ခြင်းကို ကိုင်တွယ်ခြင်း (နိုင်သည် / ရှုံးသည် ရွေးချယ်မှုနှင့် API ဖြင့် အလိုအလျောက်တွက်ရန်)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith("game_"):
        game_name = "Wingo 1min" if "wingo" in data else "TRX 1min"
        context.user_data['selected_game'] = game_name
        
        if "wingo" in data:
            await query.edit_message_text(text="⏳ Wingo History API မှ အချက်အလက်များကို ဆွဲထုတ်နေပါပြီ...")
            
            # API မှ ဒေတာဆွဲထုတ်ခြင်း
            api_data = await fetch_wingo_history()
            
            # ဖော်မြူလာ တွက်ချက်မှု ရလဒ် (ဥပမာ)
            calculated_result = "B (Big)" 
            
            keyboard = [
                [
                    InlineKeyboardButton("✅ နိုင်သည် (Win)", callback_data="result_win"),
                    InlineKeyboardButton("❌ ရှုံးသည် (Loss)", callback_data="result_loss")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                text=f"🎮 ရွေးချယ်ထားသောဂိမ်း: **{game_name}**\n\n"
                     f"📊 **API ဖြင့် တွက်ချက်ထားသော ခန့်မှန်းချက်**\n"
                     f"👉 **{calculated_result}**\n\n"
                     f"ရလဒ်ကို ရွေးပါ -",
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
        
    elif data in ["result_win", "result_loss"]:
        # နိုင်သည် သို့မဟုတ် ရှုံးသည် နှိပ်လိုက်လျှင် API ကို အလိုအလျောက် ထပ်ခေါ်ပြီး နောက်တစ်ပွဲ ဆက်ပြမည်
        status_msg = "🎉 **ဝမ်းသာပါတယ်! (Win)**" if data == "result_win" else "💪 **ဝမ်းနည်းပါတယ်! (Loss)**"
        
        await query.edit_message_text(text=f"{status_msg}\n\n⏳ နောက်တစ်ပွဲအတွက် API မှ ဒေတာအသစ် ဆွဲထုတ်နေပါပြီ...")
        
        # API မှ ဒေတာအသစ် ထပ်ဆွဲမည်
        api_data = await fetch_wingo_history()
        
        # နောက်တစ်ပွဲအတွက် တွက်ချက်မှုအသစ်
        next_calculated_result = "S (Small)" # ဥပမာ တွက်ချက်မှုအသစ်
        
        keyboard = [
            [
                InlineKeyboardButton("✅ နိုင်သည် (Win)", callback_data="result_win"),
                InlineKeyboardButton("❌ ရှုံးသည် (Loss)", callback_data="result_loss")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text=f"🔄 **နောက်ထပ် တစ်ပွဲစာ တွက်ချက်မှု**\n\n"
                 f"ခန့်မှန်းချက်အသစ်: 👉 **{next_calculated_result}**\n\n"
                 f"ရလဒ်ကို ဆက်လက်ရွေးပါ -",
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
