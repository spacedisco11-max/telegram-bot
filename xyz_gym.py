from dotenv import load_dotenv
import os
import sys
from typing import Final
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Load local .env for local testing
load_dotenv()

# ---- Resolve environment variables ----
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
    print("ERROR: Telegram token not set.")
    sys.exit(1)

if not OPENAI_KEY:
    print("ERROR: OpenAI key not set.")
    sys.exit(1)

BOT_USERNAME: Final = "gold_fitness_bot"

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# FAQ dictionary
FAQS = {
    "opening hours": "We're open Monday–Saturday 6:00 AM – 10:00 PM, and Sundays 7:00 AM – 5:00 PM.",
    "membership fee": "Standard membership is ₹1,499/month. Discounts available for 3-month and yearly plans.",
    "personal training": "Certified personal trainers available. Packages start at ₹4,999/month.",
    "facilities": "Cardio & weight area, functional training zone, yoga studio, steam/sauna.",
    "trial": "1-day free trial session available. Send your preferred day/time to book.",
    "classes": "Group classes: HIIT, Yoga, Strength Training, Functional Fitness.",
    "contact": "Call/WhatsApp: +91-XXXXXXXXXX or email: info@gymcenter.com"
}

# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am GOLD's GYM bot. Type /faq for common questions.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Type /faq to see frequently asked questions.")

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faqs = "\n\n".join([f"Q: {k.title()}?\nA: {v}" for k, v in FAQS.items()])
    await update.message.reply_text(f"Frequently Asked Questions\n\n{faqs}")

# --- OpenAI wrapper ---
def chat_with_gpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a gym."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "⚡ Sorry, I can't answer right now. Please contact +91-XXXXXXXXXX."

# --- Message handling ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()
    chat_type = update.message.chat.type

    # FAQ direct match
    for keyword, answer in FAQS.items():
        if keyword in text:
            await update.message.reply_text(answer)
            return

    # Show "thinking" placeholder
    placeholder = await update.message.reply_text("⚡ Thinking...")

    # Group mention handling
    if chat_type == "group" and BOT_USERNAME in text:
        text = text.replace(BOT_USERNAME, "").strip()

    response = chat_with_gpt(text)

    if not response.strip():
        response = "⚡ For more info, contact +91-XXXXXXXXXX."

    try:
        await placeholder.edit_text(response)
    except Exception:
        await update.message.reply_text(response)

# --- Error handler ---
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# --- Main ---
if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("faq", faq_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("Bot starting...")
    app.run_polling()
