from dotenv import load_dotenv
import os
from typing import Final
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Load secrets from .env ---
load_dotenv()
TOKEN: Final = os.getenv("TELEGRAM_TOKEN_BOT1")
OPENAI_KEY: Final = os.getenv("OPENAI_API_KEY_BOT1")
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
    await update.message.reply_text("👋 Hello! Thanks for chatting with me. I am the official bot for Ram sir Tution center!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ I am here to answer your questions about Ram sir Tution center. Type /faq to see common questions.")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ This is a custom command!")

# --- FAQ Command ---
async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faqs = (
        "📌 *Frequently Asked Questions*\n\n"
        "Q: What subjects do you teach?\n"
        "A: We cover Mathematics, Science, and English for Classes 6–12 both CBSE and State Syllabus.\n\n"
        "Q: What are the class timings?\n"
        "A: Classes run weekdays from 5PM–9PM and weekends from 9AM–1PM. Online sessions are also available.\n\n"
        "Q: How much is the monthly fee?\n"
        "A: Fees start from ₹2,000/month depending on grade and subject. Discounts for group enrollments.\n\n"
        "Q: Do you offer online classes?\n"
        "A: Yes, we provide live interactive online classes, recorded lessons, and digital notes."
    )
    await update.message.reply_text(faqs, parse_mode="Markdown")

# --- GPT response ---
def chat_with_gpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant and bot for Ram sir Tution center. Always prefer FAQ knowledge first, and if unsure, politely redirect users to contact details."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print("OpenAI Error:", e)
        return "⚠️ Oops! My brain is tired, try again later 😅"

# --- Handle all messages ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text.lower()
    print(f"User({update.message.chat.id}) in {message_type}: '{text}' ")

    # Send typing action to avoid timeout
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    # --- FAQ matching ---
    for keyword, answer in FAQS.items():
        if keyword in text:
            await update.message.reply_text(answer)
            return

    # Quick placeholder reply
    placeholder = await update.message.reply_text("⚡ Thinking...")

    # --- GPT fallback ---
    if message_type == "group":
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, "").strip()
            response: str = chat_with_gpt(new_text)
        else:
            return
    else:
        response: str = chat_with_gpt(text)

    # --- Final fallback if GPT is too vague ---
    if not response or response.strip() == "":
        response = "📞 For more information, please contact us directly at +91-XXXXXXXXXX."

    print("Bot:", response)

    # Edit the placeholder message with GPT's response
    try:
        await placeholder.edit_text(response)
    except Exception:
        # if edit fails, just send a new message
        await update.message.reply_text(response)

# --- Error handler ---
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Update {update} caused error {context.error}")

# --- Main ---
if __name__ == "__main__":
    print("Starting bot...")
    app = Application.builder().token(TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("custom", custom_command))
    app.add_handler(CommandHandler("faq", faq_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))

    # Errors
    app.add_error_handler(error)

    print("Polling...")
    app.run_polling(poll_interval=3)


