import os
import json
from datetime import datetime

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import tornado.ioloop
import tornado.web
from dotenv import load_dotenv

# ----------------------------
# Load environment variables
# ----------------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8443))
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "0"))

if not BOT_TOKEN or not WEBHOOK_URL or not SUPER_ADMIN_ID:
    raise ValueError("Please set BOT_TOKEN, WEBHOOK_URL, SUPER_ADMIN_ID in .env")

# ----------------------------
# Simple persistence for admins
# ----------------------------
ADMINS_FILE = "admins.json"

def load_admins() -> set:
    """
    Load admins from a JSON file. If not present, create with SuperAdmin only.
    """
    if not os.path.exists(ADMINS_FILE):
        data = {"admins": [SUPER_ADMIN_ID]}
        with open(ADMINS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return {SUPER_ADMIN_ID}

    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("admins", [SUPER_ADMIN_ID]))
    except Exception:
        # fallback to super admin only if file is corrupted
        return {SUPER_ADMIN_ID}

def save_admins(admins: set) -> None:
    data = {"admins": sorted(list(admins))}
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)

admins = load_admins()

# Maps forwarded ADMIN message_id -> original user_id (for replies)
message_user_map = {}

# For button-driven add/remove admin (simple flow)
# awaited_actions[user_id] = "add" | "remove"
awaited_actions = {}

# ----------------------------
# Keyboard (menu)
# ----------------------------
main_menu = ReplyKeyboardMarkup(
    [
        [KeyboardButton("👑 List Admins")],
        [KeyboardButton("➕ Add Admin"), KeyboardButton("➖ Remove Admin")],
    ],
    resize_keyboard=True,
)

# ----------------------------
# Helpers
# ----------------------------
def is_admin(user_id: int) -> bool:
    return user_id in admins

def is_super_admin(user_id: int) -> bool:
    return user_id == SUPER_ADMIN_ID

# ----------------------------
# Commands
# ----------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_super_admin(uid):
        await update.message.reply_text("👑 SuperAdmin panelga xush kelibsiz.", reply_markup=main_menu)
    elif is_admin(uid):
        await update.message.reply_text("👤 Admin panelga xush kelibsiz.", reply_markup=main_menu)
    else:
        await update.message.reply_text("🤖 Assalomu aleykum! Botga xush kelibsiz! Murojatlaringizni yuboring.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "ℹ️ Yordam:\n"
        "/start — Boshlash\n"
        "/myid — Sizning Telegram ID\n"
        "/listadmins — Adminlar ro'yxati\n"
        "/addadmin <user_id> — Admin qo'shish (faqat SuperAdmin)\n"
        "/removeadmin <user_id> — Admin o'chirish (faqat SuperAdmin)\n\n"
        "Yoki tugmalardan foydalaning 👇"
    )
    await update.message.reply_text(text, reply_markup=main_menu)

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Sizning ID: {update.effective_user.id}")

async def list_admins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Sizda ruxsat yo'q!")
    lines = ["📋 Adminlar ro'yxati:"]
    for idx, aid in enumerate(sorted(admins), start=1):
        crown = "👑 " if aid == SUPER_ADMIN_ID else "👤 "
        lines.append(f"{idx}. {crown}{aid}")
    await update.message.reply_text("\n".join(lines))

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_super_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Faqat SuperAdmin admin qo‘sha oladi.")
    if not context.args:
        return await update.message.reply_text("⚠️ Foydalanish: /addadmin <user_id>")
    try:
        new_id = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Noto‘g‘ri ID format!")

    if new_id in admins:
        return await update.message.reply_text("⚠️ Bu foydalanuvchi allaqachon admin.")
    admins.add(new_id)
    save_admins(admins)
    await update.message.reply_text(f"✅ {new_id} admin qilib qo'shildi.")

async def remove_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_super_admin(update.effective_user.id):
        return await update.message.reply_text("❌ Faqat SuperAdmin admin o‘chira oladi.")
    if not context.args:
        return await update.message.reply_text("⚠️ Foydalanish: /removeadmin <user_id>")
    try:
        target = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("❌ Noto‘g‘ri ID format!")

    if target == SUPER_ADMIN_ID:
        return await update.message.reply_text("❌ SuperAdmin o‘chirib bo‘lmaydi!")
    if target not in admins:
        return await update.message.reply_text("⚠️ Bu foydalanuvchi admin emas.")
    admins.remove(target)
    save_admins(admins)
    await update.message.reply_text(f"🗑️ {target} adminlikdan olib tashlandi.")

# ----------------------------
# Menu button handlers
# ----------------------------
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    if text == "👑 List Admins":
        return await list_admins(update, context)

    if text == "➕ Add Admin":
        if not is_super_admin(uid):
            return await update.message.reply_text("❌ Faqat SuperAdmin admin qo'sha oladi.")
        awaited_actions[uid] = "add"
        return await update.message.reply_text("➕ Yangi admin ID sini yuboring (faqat raqam).")

    if text == "➖ Remove Admin":
        if not is_super_admin(uid):
            return await update.message.reply_text("❌ Faqat SuperAdmin admin o‘chira oladi.")
        awaited_actions[uid] = "remove"
        return await update.message.reply_text("➖ O‘chiriladigan admin ID sini yuboring (faqat raqam).")

# This catches numeric replies for add/remove
async def handle_superadmin_id_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text.strip()

    # Only act if SuperAdmin is in an awaited flow
    if not is_super_admin(uid) or uid not in awaited_actions:
        return

    action = awaited_actions.pop(uid)  # consume the action
    # Validate ID
    if not text.isdigit():
        return await update.message.reply_text("❌ Iltimos, faqat raqam yuboring.")
    target_id = int(text)

    if action == "add":
        if target_id in admins:
            return await update.message.reply_text("⚠️ Bu foydalanuvchi allaqachon admin.")
        admins.add(target_id)
        save_admins(admins)
        return await update.message.reply_text(f"✅ {target_id} admin qilib qo'shildi.")

    if action == "remove":
        if target_id == SUPER_ADMIN_ID:
            return await update.message.reply_text("❌ SuperAdmin o‘chirib bo‘lmaydi!")
        if target_id not in admins:
            return await update.message.reply_text("⚠️ Bu foydalanuvchi admin emas.")
        admins.remove(target_id)
        save_admins(admins)
        return await update.message.reply_text(f"🗑️ {target_id} adminlikdan olib tashlandi.")

# ----------------------------
# Main text handler (user/admin messaging)
# ----------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Admin replying to a forwarded user message
    if is_admin(user.id) and update.message.reply_to_message:
        original_msg_id = update.message.reply_to_message.message_id
        if original_msg_id in message_user_map:
            end_user_id = message_user_map[original_msg_id]
            await context.bot.send_message(chat_id=end_user_id, text=f"👤 {update.message.text}")
            return await update.message.reply_text("👤 Xabar foydalanuvchiga yuborildi.")
        else:
            return await update.message.reply_text("👤 Iltimos, foydalanuvchi xabariga reply qiling.")

    # Normal user message → forward to all admins
    if not is_admin(user.id):
        await update.message.reply_text("🤖 Yaqin orada javob qaytaramiz!!!")
        username = f"@{user.username}" if user.username else user.full_name
        time_sent = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"👤 {username} : {update.message.text} : {time_sent}\nUser ID: {user.id}"

        for admin_id in admins:
            sent_msg = await context.bot.send_message(chat_id=admin_id, text=log_message)
            message_user_map[sent_msg.message_id] = user.id
        return

    # If admin sends a text not replying to a user
    await update.message.reply_text("👤 Admin xabaringiz qabul qilindi.")

# ----------------------------
# Tornado webhook
# ----------------------------
class WebhookHandler(tornado.web.RequestHandler):
    def initialize(self, application):
        self.application = application

    async def post(self):
        update = Update.de_json(self.request.body.decode("utf-8"), self.application.bot)
        await self.application.process_update(update)
        self.set_status(200)
        self.finish()

def make_app(application):
    return tornado.web.Application([
        (r"/webhook", WebhookHandler, dict(application=application)),
    ])

# ----------------------------
# Boot
# ----------------------------
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "Boshlash"),
        BotCommand("help", "Yordam"),
        BotCommand("myid", "Sizning Telegram ID"),
        BotCommand("listadmins", "Adminlar ro'yxati"),
        BotCommand("addadmin", "Admin qo'shish (faqat SuperAdmin)"),
        BotCommand("removeadmin", "Admin o'chirish (faqat SuperAdmin)"),
    ]
    await application.bot.set_my_commands(commands)

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("listadmins", list_admins))
    app.add_handler(CommandHandler("addadmin", add_admin))
    app.add_handler(CommandHandler("removeadmin", remove_admin))

    # Menu button clicks
    app.add_handler(MessageHandler(
        filters.Regex(r"^(👑 List Admins|➕ Add Admin|➖ Remove Admin)$"),
        handle_menu
    ))

    # SuperAdmin numeric input for add/remove (must be BEFORE general text)
    app.add_handler(MessageHandler(filters.Regex(r"^\d{3,}$"), handle_superadmin_id_input))

    # General text handler (users & admin replies)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Set webhook & bot commands
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(app.bot.set_webhook(WEBHOOK_URL))
    loop.run_until_complete(set_bot_commands(app))

    # Start Tornado
    tornado_app = make_app(app)
    tornado_app.listen(PORT)
    print(f"🚀 Bot started on port {PORT} with webhook {WEBHOOK_URL}")
    tornado.ioloop.IOLoop.current().start()
