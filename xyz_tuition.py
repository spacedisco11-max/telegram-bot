from dotenv import load_dotenv
import os
import sys
from typing import Final
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Load local .env ---
load_dotenv()

# --- Resolve environment variables ---
def get_env_prefer(primary: str, alternates: list[str]) -> str | None:
    value = os.getenv(primary)
    if value:
        return value
    for alt in alternates:
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

BOT_USERNAME: Final = "ram_sir_tution_bot"

# --- OpenAI Client ---
client = OpenAI(api_key=OPENAI_KEY)

# --- FAQ dictionary ---
FAQS = {
    "subjects": "📘 We cover Mathematics, Science, and English for Classes 6–12 (CBSE & State syllabus).",
    "class timings": "⏰ Weekdays 5PM–9PM, weekends 9AM–1PM. Flexible online sessions also available.",
    "monthly fee": "💰 Fees start from ₹2,000/month depending on grade & subject. Discounts for group enrollments.",
    "online classes": "💻 Yes! We provide live interactive online classes, recorded lessons, and digital notes."
}

# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I am Ram Sir Tuition Bot. Type /faq for common questions.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Type /faq to see frequently asked questions.")

async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faqs = "\n\n".join([f"Q: {k.title()}?\nA: {v}" for k, v in FAQS.items()])
    await update.message.reply_text(f"📌 Frequently Asked Questions\n\n{faqs}")

# --- GPT fallback ---
def chat_with_gpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a tuition center."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "⚠️ Sorry, I can't answer right now. Contact +91-XXXXXXXXXX."

# --- Message handling ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()
    chat_type = update.message.chat.type
    print(f"User({update.message.chat.id}) in {chat_type}: '{text}'")

    # FAQ direct match
    for keyword, answer in FAQS.items():
        if keyword in text:
            await update.message.reply_text(answer)
            return

    # Show "thinking" placeholder
    placeholder = await update.message.reply_text("⚡ Thinking...")

    if chat_type == "group" and BOT_USERNAME in text:
        text = text.replace(BOT_USERNAME, "").strip()

    response = chat_with_gpt(text)

    if not response.strip():
        response = "📞 For more information, contact +91-XXXXXXXXXX."

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
