import os
from datetime import datetime

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, ContextTypes, filters)

TOKEN = "ВАШ_ТОКЕН"
ADMIN_ID = 123456789  # ваш Id из @userinfobot, без кавычек
REQUESTS_FILE = "requests.xlsx"

TEXTS = {
    "services": "Что я делаю:\n- Telegram-боты\n- Автоматизация Excel-отчётов\n- Скрипты для обработки данных",
    "prices": "Цены (пример):\n- Простой бот: от 3000 руб.\n- Excel-отчёт: от 2000 руб.",
    "contacts": "Связаться со мной: напишите заявку через кнопку ниже.",
}

MAIN_TEXT = "Здравствуйте! Я бот-визитка. Выберите раздел:"

MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("Услуги", callback_data="services")],
    [InlineKeyboardButton("Цены", callback_data="prices")],
    [InlineKeyboardButton("Контакты", callback_data="contacts")],
    [InlineKeyboardButton("Оставить заявку", callback_data="request")],
])

MENU_BACK = InlineKeyboardMarkup([
    [InlineKeyboardButton("Услуги", callback_data="services")],
    [InlineKeyboardButton("Цены", callback_data="prices")],
    [InlineKeyboardButton("Контакты", callback_data="contacts")],
    [InlineKeyboardButton("Оставить заявку", callback_data="request")],
    [InlineKeyboardButton("⬅ Назад", callback_data="back")],
])


def save_request(user, text):
    if os.path.exists(REQUESTS_FILE):
        wb = load_workbook(REQUESTS_FILE)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Заявки"
        ws.append(["Дата", "Имя", "Username", "ID", "Текст заявки"])
        for cell in ws[1]:
            cell.font = Font(bold=True)
        ws.column_dimensions["A"].width = 20
        ws.column_dimensions["B"].width = 25
        ws.column_dimensions["C"].width = 20
        ws.column_dimensions["D"].width = 15
        ws.column_dimensions["E"].width = 60

    username = f"@{user.username}" if user.username else "—"
    ws.append([
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        user.full_name,
        username,
        user.id,
        text,
    ])
    wb.save(REQUESTS_FILE)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(MAIN_TEXT, reply_markup=MENU)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "back":
        context.user_data["waiting"] = False
        await query.message.reply_text(MAIN_TEXT, reply_markup=MENU)
        return

    if query.data == "request":
        context.user_data["waiting"] = True
        await query.message.reply_text(
            "Опишите задачу и оставьте контакт, я передам заявку.",
            reply_markup=MENU_BACK,
        )
        return

    await query.message.reply_text(TEXTS[query.data], reply_markup=MENU_BACK)


async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting"):
        context.user_data["waiting"] = False
        user = update.effective_user

        save_request(user, update.message.text)

        msg = f"Новая заявка от {user.full_name} (@{user.username}):\n{update.message.text}"
        await context.bot.send_message(chat_id=ADMIN_ID, text=msg)
        await update.message.reply_text("Спасибо! Заявка отправлена.", reply_markup=MENU)
    else:
        await update.message.reply_text("Выберите раздел в меню:", reply_markup=MENU)


app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text))

print("Бот запущен. Остановить: Ctrl+C")
app.run_polling()