import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from supabase import create_client, Client

# --- Your Credentials ---
# NEVER share these keys publicly!
TELEGRAM_BOT_TOKEN = "7740341054:AAEE5ZnMC6ZADDNpWOLZmZrlkJnYw1m6m1I"  # Get this from BotFather
SUPABASE_URL = "https://spztdgowiccsdcfnevwd.supabase.co"              # Get this from Supabase API Settings
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNwenRkZ293aWNjc2RjZm5ldndkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTEzODM3MCwiZXhwIjoyMDY2NzE0MzcwfQ.IOwYFuiB2ULwgIax_l8XAd2wLGi4SnQCE7YNtgD1dFk"      # Get the 'service_role' key from Supabase

# --- NEW: Your Public Storage Channel ---
# This is the username of the public channel you just created.
STORAGE_CHANNEL_ID = "@chanfilestore"

# --- Setup ---
# Set up Supabase connection
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Set up basic logging to see errors
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- Bot Functions ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message when the /start command is issued."""
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello! I'm your file storing bot. Send me a file and I will generate a permanent link."
    )

# --- THIS ENTIRE FUNCTION IS NEW ---
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles any file/document, forwards it to the storage channel,
    and saves the public link to Supabase.
    """
    user = update.message.from_user
    original_message = update.message

    if not original_message.document:
        await original_message.reply_text("Please send me a file (as a document).")
        return

    try:
        # 1. Forward the message to the storage channel
        logging.info(f"Forwarding file from user {user.id} to {STORAGE_CHANNEL_ID}")
        forwarded_message = await context.bot.forward_message(
            chat_id=STORAGE_CHANNEL_ID,
            from_chat_id=original_message.chat_id,
            message_id=original_message.message_id
        )

        # 2. Check if forwarding was successful
        if not forwarded_message:
            await original_message.reply_text("❌ Error: Could not forward the file. Make sure the bot is an admin in the channel.")
            return

        # 3. Construct the permanent public link
        # It removes the '@' from the channel name for the URL
        channel_username = STORAGE_CHANNEL_ID.lstrip('@')
        file_link = f"https://t.me/{channel_username}/{forwarded_message.message_id}"
        
        # 4. Insert the data into your Supabase table
      logging.info(f"Saving link to Supabase: {file_link}")
      
      # NEW LINE: Get the filename from the original message
      file_name = original_message.document.file_name

      data, count = supabase.table('files').insert({
          'user_id': user.id,
          'file_link': file_link,
          'file_name': file_name  # <-- NEW LINE: Add the filename to the database
      }).execute()

        await original_message.reply_text(
            f"✅ File saved!\n\nHere is your permanent link:\n{file_link}"
        )

    except Exception as e:
        logging.error(f"Error in file_handler: {e}")
        await original_message.reply_text("❌ Sorry, a critical error occurred.")

# --- Main Bot Execution ---

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    print("Bot is running...")
    application.run_polling()
