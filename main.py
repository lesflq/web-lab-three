import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai


BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", "8080"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

STUDENT_SURNAME = "Севастьянов"
STUDENT_GROUP = "ІО-24"
CONTACT_PHONE = "+380506191320"
CONTACT_EMAIL = "max.09seva@gmail.com"

IT_TECH = [
    "Python", "JavaScript", "Docker", "Git", "Linux", "REST API", "SQL", "AI/ML"
]

# Кнопки головного меню
MAIN_MENU = ReplyKeyboardMarkup([
    [KeyboardButton("Студент"), KeyboardButton("IT-технології")],
    [KeyboardButton("Контакти"), KeyboardButton("Prompt Gemini")],
], resize_keyboard=True)


def format_student_block() -> str:
    return (
        f"\u270D\ufe0f *Студент*\n"
        f"Прізвище: *{STUDENT_SURNAME}*\n"
        f"Група: *{STUDENT_GROUP}*"
    )


def format_it_block() -> str:
    items = "\n".join([f"• {t}" for t in IT_TECH])
    return f"*IT-технології*\n{items}"


def format_contacts_block() -> str:
    return (
        f" *Контакти*\n"
        f"Телефон: *{CONTACT_PHONE}*\n"
        f"E-mail: *{CONTACT_EMAIL}*"
    )

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

async def ask_gemini(prompt: str) -> str:
# """Повертає відповідь від Gemini"""
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Помилка при зверненні до Gemini: {e}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    hello = (
            "Вітаю, " + (user.first_name or "студенте") + "!\n\n"
                                                          "Це бот для лабораторної: виберіть розділ з меню нижче."
    )
    await update.message.reply_text(hello, reply_markup=MAIN_MENU)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Доступні розділи: Студент, IT-технології, Контакти, Prompt Gemini",
        reply_markup=MAIN_MENU,
    )
async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_prompt"] = False
    await update.message.reply_text("Скасовано. Оберіть пункт з меню нижче.", reply_markup=MAIN_MENU)

from telegram.constants import ParseMode

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    low = text.lower()

    if context.user_data.get("awaiting_prompt"):
        if low in {"студент", "it-технології", "контакти", "prompt Gemini", "/cancel", "скасувати", "назад"}:
            context.user_data["awaiting_prompt"] = False
        else:
            await update.message.reply_text("Думаю над відповіддю…")
            answer = await ask_gemini(text)
            context.user_data["awaiting_prompt"] = False
            await update.message.reply_text(answer, reply_markup=MAIN_MENU)
            return

    if low == "студент":
        await update.message.reply_text(format_student_block(), parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_MENU)
    elif low == "it-технології":
        await update.message.reply_text(format_it_block(), parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_MENU)
    elif low == "контакти":
        await update.message.reply_text(format_contacts_block(), parse_mode=ParseMode.MARKDOWN, reply_markup=MAIN_MENU)
    elif low == "prompt gemini":
        context.user_data["awaiting_prompt"] = True
        await update.message.reply_text(
    "Введіть свій промпт повідомленням (у наступному рядку).")

    else:
        await update.message.reply_text("Оберіть пункт з меню нижче.", reply_markup=MAIN_MENU)


async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"pong {datetime.utcnow().isoformat()}Z")


def build_app():
    if not BOT_TOKEN:
        raise RuntimeError("Не задано BOT_TOKEN (змінна середовища)")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu))
    return app

if __name__ == "__main__":
    application = build_app()

    if WEBHOOK_URL:
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
    )
    else:
        application.run_polling()
