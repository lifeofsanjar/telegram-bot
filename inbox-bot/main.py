import os
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN", "8354684447:AAGjT-x5jooGquGaSvCs3mTZkhnu3nW7RUA")
ADMIN_ID = 1922538466

message_user_map = {}

# 🔹 1. Reset any old webhook/polling connection
def reset_webhook():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/deleteWebhook?drop_pending_updates=true"
    r = requests.get(url)
    print(f"🔄 Webhook reset: {r.json()}")

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id == ADMIN_ID:
        await update.message.reply_text("👤 Admin panelga xush kelibsiz.")
    else:
        await update.message.reply_text("🤖 Assalomu aleykum! Botga xush kelibsiz! Murojatlaringizni yuboring.")

# Handle normal user messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user

    if user.id != ADMIN_ID:
        await update.message.reply_text("🤖 Yaqin orada javob qaytaramiz!!!")

        username = f"@{user.username}" if user.username else user.full_name
        time_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"👤 {username} : {update.message.text} : {time_sent}\nUser ID: {user.id}"

        sent_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=log_message)
        message_user_map[sent_msg.message_id] = user.id
    else:
        await update.message.reply_text("👤 Admin xabaringiz qabul qilindi.")

# Handle admin replies
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        return

    if update.message.reply_to_message and update.message.reply_to_message.message_id in message_user_map:
        user_id = message_user_map[update.message.reply_to_message.message_id]
        await context.bot.send_message(chat_id=user_id, text=f"👤 {update.message.text}")
        await update.message.reply_text("👤 Xabar foydalanuvchiga yuborildi.")
    else:
        await update.message.reply_text("👤 Iltimos, foydalanuvchi xabariga reply qiling.")

if __name__ == "__main__":
    reset_webhook()  # ✅ Clears any old connections before bot starts

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    PORT = int(os.environ.get("PORT", 8443))
    WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_URL', '').replace('https://', '')}/webhook"

    print(f"🚀 Starting bot with webhook at {WEBHOOK_URL}")
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}"
    )
