# main.py  (replace your old file contents with this)
from dotenv import load_dotenv
import os
import sys
from typing import Final
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load local .env for local testing only
load_dotenv()

# ---- Resolve environment variables (priority order) ----
# Prefer generic names (what Render expects). If missing, fall back to BOT1/BOT2 local names.
def get_env_prefer(render_name: str, alt_names: list[str]) -> str | None:
    value = os.getenv(render_name)
    if value:
        return value
    for alt in alt_names:
        val = os.getenv(alt)
        if val:
            return val
    return None

TOKEN = get_env_prefer("TELEGRAM_TOKEN", ["TELEGRAM_TOKEN_BOT2", "TELEGRAM_TOKEN_BOT1"])
OPENAI_KEY = get_env_prefer("OPENAI_API_KEY", ["OPENAI_API_KEY_BOT2", "OPENAI_API_KEY_BOT1"])

if not TOKEN:
    print("ERROR: Telegram token not set. Add TELEGRAM_TOKEN (or TELEGRAM_TOKEN_BOT2) to env.")
    sys.exit(1)

if not OPENAI_KEY:
    print("ERROR: OpenAI key not set. Add OPENAI_API_KEY (or OPENAI_API_KEY_BOT2) to env.")
    sys.exit(1)

# Bot username for group mentions
BOT_USERNAME: Final = "gold_fitness_bot"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# --- FAQ dictionary (Gym) ---
FAQS = {
    "opening hours": "We're open Monday–Saturday 6:00 AM – 10:00 PM, and Sundays 7:00 AM – 5:00 PM.",
    "membership fee": "Standard membership is ₹1,499/month. We also offer 3-month and yearly plans with discounts.",
    "personal training": "Yes — certified personal trainers available. Personal training packages start at ₹4,999/month.",
    "facilities": "We have a fully equipped cardio & weight area, functional training zone, yoga studio, and steam/sauna.",
    "trial": "We offer a 1-day free trial session. Send your preferred day and time to book.",
    "classes": "Group classes include HIIT, Yoga, Strength Training, and Functional Fitness.",
    "contact": "For bookings, call/WhatsApp: +91-XXXXXXXXXX or email: info@gymcenter.com"
}

# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am the official bot for GOLD's GYM. Type /faq for common questions.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Type /faq to see frequently asked questions.")

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faqs = (
        "Frequently Asked Questions\n\n"
        "Q: What are your opening hours?\n"
        "A: " + FAQS["opening hours"] + "\n\n"
        "Q: What's the monthly membership fee?\n"
        "A: " + FAQS["membership fee"] + "\n\n"
        "Q: Do you offer personal training?\n"
        "A: " + FAQS["personal training"] + "\n\n"
        "Q: What facilities are available?\n"
        "A: " + FAQS["facilities"]
    )
    await update.message.reply_text(faqs)

# --- OpenAI wrapper ---
def chat_with_gpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a gym. Prefer FAQ answers when possible."},
                {"role": "user", "content": prompt}
            ]
        )
        # older SDK returns response.choices[0].message.content
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "Sorry, I can't answer right now. Please contact +91-XXXXXXXXXX."

# --- Message handling ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type = update.message.chat.type
    text = (update.message.text or "").lower()
    print(f"User({update.message.chat.id}) in {message_type}: '{text}'")

    # show typing
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # FAQ direct match
    for keyword, answer in FAQS.items():
        if keyword in text:
            await update.message.reply_text(answer)
            return

    # placeholder
    placeholder = await update.message.reply_text("Thinking...")

    # group mention handling
    if message_type == "group":
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = chat_with_gpt(new_text)
        else:
            return
    else:
        response = chat_with_gpt(text)

    if not response or response.strip() == "":
        response = "For more info, contact +91-XXXXXXXXXX."

    try:
        await placeholder.edit_text(response)
    except Exception:
        await update.message.reply_text(response)

async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# --- Main ---
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error)

    print("Bot starting...")
    app.run_polling(poll_interval=3)






