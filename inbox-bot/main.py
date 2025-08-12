from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

BOT_TOKEN = "8354684447:AAGjT-x5jooGquGaSvCs3mTZkhnu3nW7RUA"

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Assalomu aleykum! Botga xush kelibsiz! Murojatlaringizni yuboring.")

# Handle any text message
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = f"@{user.username}" if user.username else user.full_name
    text = update.message.text
    time_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Custom log message
    log_message = f"{username} : {text} : {time_sent}"

    # Send this custom log back to the chat (the bot itself)
    await update.message.reply_text(log_message)

    # Also send the default reply "123"
    await update.message.reply_text("Yaqin orada javob qaytaramiz!!!")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot is running...")
app.run_polling()
