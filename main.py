import os
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv


# === CONFIG ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
REACTION_EMOJI = "💊"
USER_DATA_FILE = "user_ids.json"
TARGET_USER_IDS = {887099850, 92451378, 539630621}

KEYWORDS = ["мю", "юнайтед", "манчестер юнайтед", 'mu', 'united', 'manchester united']


# === Load/save user IDs ===


def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}


def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


user_data = load_user_data()

# === Bot message handler ===


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    user = message.from_user
    username = user.username or ""
    message_text = (message.text or "").lower()

    # Store user ID
    if username not in user_data or user_data[username] != user.id:
        user_data[username] = user.id
        save_user_data(user_data)
        print(f"🔹 Saved user: {username} → {user.id}")

    # React if user_id matches
    if user.id in TARGET_USER_IDS and any(keyword in message_text for keyword in KEYWORDS):
        try:
            await message.reply_text(REACTION_EMOJI)
            print(f"✅ Reacted to message from @{username}")
        except Exception as e:
            print("❌ Failed to react:", e)


# === Fake HTTP server for Render health check ===
def run_fake_server():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Bot is running")

    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    server.serve_forever()


# === Main app ===
if __name__ == '__main__':

    # Start HTTP server in a background thread
    threading.Thread(target=run_fake_server, daemon=True).start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()
