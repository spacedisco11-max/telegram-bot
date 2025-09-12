from dotenv import load_dotenv
import os
from typing import Final
from openai import OpenAI
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# --- Load secrets from .env locally ---
load_dotenv()  # Only needed for local testing

# --- Environment variables ---
TOKEN: Final = os.getenv("TELEGRAM_TOKEN")       # Use exactly this name on Render
OPENAI_KEY: Final = os.getenv("OPENAI_API_KEY")  # Use exactly this name on Render
BOT_USERNAME: Final = "gold_fitness_bot"

# --- OpenAI client ---
client = OpenAI(api_key=OPENAI_KEY)




# --- FAQ dictionary (Gym) ---
FAQS = {
    "opening hours": "⏰ We're open Monday–Saturday 6:00 AM – 10:00 PM, and Sundays 7:00 AM – 5:00 PM.",
    "membership fee": "💰 Standard membership is ₹1,499/month. We also offer 3-month and yearly plans with discounts (ask for details).",
    "personal training": "🏋️ Yes — certified personal trainers available. Personal training packages start at ₹4,999/month.",
    "facilities": "🏟️ We have a fully equipped cardio & weight area, functional training zone, yoga studio, and steam/sauna.",
    "trial": "🎯 We offer a 1-day free trial session. Book a trial by messaging us your preferred day and time.",
    "classes": "📚 Group classes include HIIT, Yoga, Strength Training, and Functional Fitness. Check schedule for class times.",
    "trainers": "👨‍🏫 Our trainers are certified professionals with experience in strength, conditioning, and weight loss coaching.",
    "payment": "💳 We accept UPI, Google Pay, PhonePe, and cash. Monthly auto-renewal can be enabled on request.",
    "lockers": "🔐 Lockers and towel service are available. Monthly locker rental is optional and affordable.",
    "cancel membership": "❗ Memberships can be cancelled with 30 days' notice. Refunds follow our cancellation policy—we'll guide you through it.",
    "diet support": "🥗 We provide basic diet guidance and meal-plan templates. For personalized nutrition plans, ask about our coaching packages.",
    "contact": "📞 For more info or bookings, call/WhatsApp: +91-XXXXXXXXXX or email: info@gymcenter.com"
}



# --- Commands ---
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Thanks for chatting with me. I am the official bot for GOLD's GYM")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ I am here to answer your questions about GOLD's GYM. Type /faq to see common questions.")

async def custom_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ This is a custom command!")

# --- FAQ Command ---
async def faq_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faqs = (
        "📌 *Frequently Asked Questions*\n\n"
        "Q: What are your opening hours?\n"
        "A: We're open Monday to Saturday , 6AM-10PM, and Sundays from 7AM-5PM.\n\n"
        "Q: What's the monthly membership fee?\n"
        "A: Our standard membership is ₹1,499/month. We also offer quarterly and yearly packages at discounted rates!\n\n"
        "Q: Do you offer personal training?\n"
        "A: Yes, We have certified trainers available for one-on-one sessions. Personal training packages start from ₹4,999/month!.\n\n"
        "Q: What are the facilities available?\n"
        "A: We provide a fully equipped Cardio and weights section, yoga studio, functional training area, and a steam/sauna facility."
    )
    await update.message.reply_text(faqs, parse_mode="Markdown")

# --- GPT response ---
def chat_with_gpt(prompt: str) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant and bot for GOLD's GYM. Always prefer FAQ knowledge first, and if unsure, politely redirect users to contact details."},
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





