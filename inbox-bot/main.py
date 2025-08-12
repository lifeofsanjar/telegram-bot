from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

BOT_TOKEN = "8354684447:AAGjT-x5jooGquGaSvCs3mTZkhnu3nW7RUA"
ADMIN_ID = 1922538466

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
        log_message = f"{username} : {update.message.text} : {time_sent}\nUser ID: {user.id}"

        await context.bot.send_message(chat_id=ADMIN_ID, text=log_message)
    else:
        await update.message.reply_text("📩 Admin xabaringiz qabul qilindi.")

# Command for admin to reply to a user
async def reply_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return  # Ignore if not admin

    if len(context.args) < 2:
        await update.message.reply_text("❌ Foydalanish: /reply <user_id> <xabar>")
        return

    try:
        user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])
        await context.bot.send_message(chat_id=user_id, text=reply_text)
        await update.message.reply_text("✅ Xabar foydalanuvchiga yuborildi.")
    except Exception as e:
        await update.message.reply_text(f"❌ Xatolik: {e}")

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("reply", reply_user))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

print("✅ Bot is running...")
app.run_polling()
