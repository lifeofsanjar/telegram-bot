import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import tornado.ioloop
import tornado.web

BOT_TOKEN = os.getenv("BOT_TOKEN", "8354684447:AAGjT-x5jooGquGaSvCs3mTZkhnu3nW7RUA")
ADMIN_ID = 1922538466
message_user_map = {}
PORT = int(os.getenv("PORT", 8443))  # Render provides PORT, default to 8443 for Telegram

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👤 Admin panelga xush kelibsiz.")
    else:
        await update.message.reply_text("🤖 Assalomu aleykum! Botga xush kelibsiz! Murojatlaringizni yuboring.")

# Handle text messages
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Admin reply to a user's message
    if user.id == ADMIN_ID and update.message.reply_to_message:
        original_msg_id = update.message.reply_to_message.message_id
        if original_msg_id in message_user_map:
            user_id = message_user_map[original_msg_id]
            await context.bot.send_message(chat_id=user_id, text=f"👤 {update.message.text}")
            await update.message.reply_text("👤 Xabar foydalanuvchiga yuborildi.")
        else:
            await update.message.reply_text("👤 Iltimos, foydalanuvchi xabariga reply qiling.")
        return

    # Normal user message
    if user.id != ADMIN_ID:
        await update.message.reply_text("🤖 Yaqin orada javob qaytaramiz!!!")

        username = f"@{user.username}" if user.username else user.full_name
        time_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"👤 {username} : {update.message.text} : {time_sent}\nUser ID: {user.id}"

        sent_msg = await context.bot.send_message(chat_id=ADMIN_ID, text=log_message)
        message_user_map[sent_msg.message_id] = user.id
    else:
        await update.message.reply_text("👤 Admin xabaringiz qabul qilindi.")

# Tornado webhook handler
class WebhookHandler(tornado.web.RequestHandler):
    def initialize(self, application):
        self.application = application

    async def post(self):
        update = Update.de_json(self.request.body.decode('utf-8'), self.application.bot)
        await self.application.process_update(update)
        self.write_response(200)

# Create Tornado application
def make_app(application):
    return tornado.web.Application([
        (r"/webhook", WebhookHandler, dict(application=application)),
    ])

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Get webhook URL from environment variable
    webhook_url = os.getenv("WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("WEBHOOK_URL environment variable not set")

    # Set up webhook
    app.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        url_path="/webhook",
        webhook_url=webhook_url
    )

    # Start Tornado server
    tornado_app = make_app(app)
    tornado_app.listen(PORT)
    print(f"🚀 Bot webhook mode started on port {PORT}...")
    tornado.ioloop.IOLoop.current().start()
