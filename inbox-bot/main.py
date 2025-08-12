from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

BOT_TOKEN = "8354684447:AAGjT-x5jooGquGaSvCs3mTZkhnu3nW7RUA"

# Replace with your own Telegram numeric user ID (not username)
ADMIN_ID = 1922538466  # theshadowmonarch1

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text("✅ Admin panelga xush kelibsiz.")
    else:
        await update.message.reply_text(
            "Assalomu aleykum! Botga xush kelibsiz! Murojatlaringizni yuboring."
        )

# Handle user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id != ADMIN_ID:
        # Reply to user
        await update.message.reply_text("Yaqin orada javob qaytaramiz!!!")

        # Send log to admin
        username = f"@{user.username}" if user.username else user.full_name
        time_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"{username} : {update.message.text} : {time_sent}"

        await context.bot.send_message(chat_id=ADMIN_ID, text=log_message)
    else:
        # Admin sends a message — you can add admin commands here if needed
        await update.message.reply_text("📩 Admin xabaringiz qabul qilindi.")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot is running...")
app.run_polling()
