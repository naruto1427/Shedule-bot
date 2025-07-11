import os
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, filters
)

# === Configuration ===
ADMINS = [123456789]  # Replace with your Telegram user ID(s)
ALLOWED_GROUP_IDS = [-1002172782993]  # Optional: group chat IDs (or leave empty)
BOT_TOKEN = os.getenv("BOT_TOKEN")

DATA_FILE = "messages.json"
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

# === Logging Configuration ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def load_messages():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_messages(messages):
    with open(DATA_FILE, "w") as f:
        json.dump(messages, f, indent=2)


# === View Day Command ===
async def day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    day = update.message.text.strip("/").split("@")[0].lower()
    messages = load_messages()

    if day in messages:
        msg = messages[day]
        text = msg.get("text", "No content.")
        buttons = msg.get("buttons", [])
        keyboard = [[InlineKeyboardButton(btn["text"], url=btn["url"])] for btn in buttons]

        await update.message.reply_text(
            text=text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard) if keyboard else None
        )
    else:
        await update.message.reply_text("❌ No message saved for this day yet.")


# === Add Day Command ===
async def add_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return await update.message.reply_text("🚫 You are not authorized to use this command.")

    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ Please reply to the message you want to save.")

    command = update.message.text.strip("/").split("@")[0].lower()
    day_map = {
        "addmon": "monday", "addtue": "tuesday", "addwed": "wednesday",
        "addthu": "thursday", "addfri": "friday", "addsat": "saturday", "addsun": "sunday"
    }
    day = day_map.get(command)
    if not day:
        return await update.message.reply_text("❌ Invalid add command.")

    content = update.message.reply_to_message.text or ""
    if not content:
        return await update.message.reply_text("⚠️ Replied message has no text.")

    message_data = {
        "text": content,
        "buttons": [
            {"text": "🔗 Open Link", "url": "https://example.com"}
        ]
    }

    messages = load_messages()
    messages[day] = message_data
    save_messages(messages)

    await update.message.reply_text(f"✅ Message for *{day.capitalize()}* saved!", parse_mode="Markdown")


# === Delete Day Command ===
async def delete_day_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return await update.message.reply_text("🚫 You are not authorized.")

    if not context.args:
        return await update.message.reply_text("❌ Usage: /delete monday")

    day = context.args[0].lower()
    if day not in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        return await update.message.reply_text("❌ Invalid day name.")

    messages = load_messages()
    if day in messages:
        del messages[day]
        save_messages(messages)
        await update.message.reply_text(f"🗑 Message for *{day.capitalize()}* deleted.", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"ℹ️ No saved message for *{day.capitalize()}*.")


# === Clear All Command ===
async def clear_all_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMINS:
        return await update.message.reply_text("🚫 You are not authorized.")
    save_messages({})
    await update.message.reply_text("🧹 All messages cleared.")


# === Admin Check Command ===
async def admin_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_admin = user_id in ADMINS
    await update.message.reply_text(f"👤 Your ID: `{user_id}`\n🛡 Admin: {'Yes' if is_admin else 'No'}", parse_mode="Markdown")


# === Main App ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # View handlers
    for day in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]:
        app.add_handler(CommandHandler(day, day_handler))

    # Add handlers
    for cmd in ["addmon", "addtue", "addwed", "addthu", "addfri", "addsat", "addsun"]:
        app.add_handler(CommandHandler(cmd, add_handler, filters=filters.REPLY))

    # Admin-only handlers
    app.add_handler(CommandHandler("delete", delete_day_handler))
    app.add_handler(CommandHandler("clear", clear_all_handler))
    app.add_handler(CommandHandler("admin", admin_check))

    logger.info("🤖 Bot started.")
    await app.run_polling()


# === Entry Point ===
if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    
