import os
import logging
import threading
from flask import Flask, jsonify, request, render_template
from supabase import create_client, Client
from flask_cors import CORS
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

# --- Initialize Flask App ---
app = Flask(__name__)
CORS(app)

# --- Credentials and Constants ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
STORAGE_CHANNEL_ID = "@chanfilestore"

# --- Setup ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Flask Web Routes (for the Mini App) ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/get_files')
def get_files():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error": "User ID is required"}), 400
    try:
        response = supabase.table("files").select("file_link", "file_name", "created_at").eq("user_id", user_id).order("created_at", desc=True).execute()
        return jsonify(response.data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Telegram Bot Logic ---
async def start_bot_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your file storing bot. Send me a file to save it.")

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    original_message = update.message
    if not original_message.document:
        await original_message.reply_text("Please send me a file (as a document).")
        return
    try:
        forwarded_message = await context.bot.forward_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=original_message.chat_id,
            message_id=original_message.message_id
        )
        if not forwarded_message:
            await original_message.reply_text("❌ Error: Could not forward the file.")
            return
        
        channel_username = STORAGE_CHANNEL_ID.lstrip('@')
        file_link = f"https://t.me/{channel_username}/{forwarded_message.message_id}"
        file_name = original_message.document.file_name

        supabase.table('files').insert({
            'user_id': user.id,
            'file_link': file_link,
            'file_name': file_name
        }).execute()
        await original_message.reply_text(f"✅ File saved!")
    except Exception as e:
        logging.error(f"Error in file_handler: {e}")
        await original_message.reply_text("❌ Sorry, a critical error occurred.")

def run_bot():
    """This function runs the Telegram bot in a background thread."""
    logging.info("Starting bot polling in background thread...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start_bot_command))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    application.run_polling()

# --- Main Execution ---
logging.info("Starting web server and bot thread...")
# Start the bot in a background thread
bot_thread = threading.Thread(target=run_bot)
bot_thread.daemon = True
bot_thread.start()

# The Flask app is run by Gunicorn from the Start Command
