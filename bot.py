import os
import asyncio
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

# /start နှိပ်လျှင် Game ID တောင်းခြင်း
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ!\n\nကျေးဇူးပြု၍ သင်၏ **Game ID** ကို ထည့်ပေးပါ။", parse_mode="Markdown")
    context.user_data['state'] = 'WAITING_FOR_GAME_ID'

# မက်ဆေ့ခ်ျများကို စစ်ဆေးခြင်း
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
        
    elif state == 'WAITING_FOR_HISTORY':
        history_text = update.message.text
        context.user_data['history'] = history_text
        
        # 👉 ဖော်မြူလာ တွက်ချက်မှု ရလဒ်
        calculated_result = "B (Big)" 
        
        # နိုင်သည် / ရှုံးသည် Button များပြမည်
        keyboard = [
            [
                InlineKeyboardButton("✅ နိုင်သည် (Win)", callback_data="result_win"),
                InlineKeyboardButton("❌ ရှုံးသည် (Loss)", callback_data="result_loss")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"📊 **တွက်ချက်မှု ရလဒ်**\n\n"
            f"ထည့်သွင်းထားသော ၅ ပွဲ: `{history_text}`\n"
            f"ခန့်မှန်းချက်: **{calculated_result}**\n\n"
            f"အောက်ပါရလဒ်ကို နှိပ်ပါ -",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

# Button များကို နှိပ်ခြင်းကို ကိုင်တွယ်ခြင်း
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data.startswith("game_"):
        game_name = "Wingo 1min" if "wingo" in data else "TRX 1min"
        context.user_data['selected_game'] = game_name
        context.user_data['state'] = 'WAITING_FOR_HISTORY'
        
        await query.edit_message_text(
            text=f"🎮 ရွေးချယ်ထားသောဂိမ်း: **{game_name}**\n\n"
                 f"ကျေးဇူးပြု၍ နောက်ဆုံးထွက်ခဲ့သော **ရလဒ် ၅ ခု** ကို ထည့်ပေးပါ။\n"
                 f"*(ဥပမာ - B, S, B, B, S - နောက်ဆုံးထွက်တာကို နောက်ဆုံးမှာထားပါ)*",
            parse_mode="Markdown"
        )
        
    elif data == "result_win":
        await query.edit_message_text(
            text="🎉 **ဝမ်းသာပါတယ်!** နိုင်သွားတဲ့အတွက် ဂုဏ်ယူပါတယ်။\n\n"
                 "ဆက်လက်တွက်ချက်ရန် နောက်ဆုံးထွက်ခဲ့သော **ရလဒ် ၁ လုံး** ကို ထပ်မံပေးပါ။",
            parse_mode="Markdown"
        )
        context.user_data['state'] = 'WAITING_FOR_HISTORY'
        
    elif data == "result_loss":
        await query.edit_message_text(
            text="💪 **ဝမ်းနည်းပါတယ်!** နောက်တစ်ကြိမ်မှာ အမှီလိုက်လို့ရပါတယ်။\n\n"
                 "ဆက်လက်တွက်ချက်ရန် နောက်ဆုံးထွက်ခဲ့သော **ရလဒ် ၁ လုံး** ကို ထပ်မံပေးပါ။",
            parse_mode="Markdown"
        )
        context.user_data['state'] = 'WAITING_FOR_HISTORY'

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
