import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ========== НАСТРОЙКА ==========
# Бот возьмет токен из переменной окружения BOT_TOKEN, которую мы позже зададим в Render
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    logging.error("❌ ОШИБКА: Не найден BOT_TOKEN. Проверьте настройки в Render.")
    exit(1)  # Останавливаем программу, если токена нет

# Включаем логирование, чтобы видеть, что происходит
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# ========== КЛАВИАТУРЫ ==========
def get_main_keyboard():
    """Клавиатура для главного меню"""
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="📝 Подать заявку"))
    return keyboard.as_markup(resize_keyboard=True, one_time_keyboard=False)

def get_squad_keyboard():
    """Клавиатура для выбора отряда"""
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="🏗️ Строители"))
    keyboard.add(KeyboardButton(text="👨‍🏫 Вожатые"))
    keyboard.add(KeyboardButton(text="🧭 Проводники"))
    keyboard.adjust(1)  # Расположить кнопки в один столбец
    return keyboard.as_markup(resize_keyboard=True)

# ========== ХРАНЕНИЕ ДАННЫХ (временное, в памяти) ==========
# Внимание: данные сбросятся при перезапуске бота. Для продакшена нужно БД или Google Sheets.
user_data = {}

# ========== КОМАНДЫ БОТА ==========
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    welcome_text = (
        "<b>👋 Привет, будущий боец штаба!</b>\n\n"
        "Я — бот для записи в отряды СТО КНИТУ-КАИ.\n"
        "Здесь ты можешь подать заявку, чтобы стать частью нашей большой команды.\n\n"
        "Нажми кнопку <b>«Подать заявку»</b> ниже, чтобы начать! ✨"
    )
    await message.answer(welcome_text, reply_markup=get_main_keyboard())

@dp.message(F.text == "📝 Подать заявку")
async def start_application(message: types.Message):
    """Начало подачи заявки"""
    # Сохраняем ID пользователя и создаем для него запись
    user_data[message.from_user.id] = {'step': 'ask_fio'}
    await message.answer(
        "Отлично! Для начала введи своё <b>ФИО</b> (полностью):\n"
        "<i>Например: Иванов Иван Иванович</i>",
        reply_markup=ReplyKeyboardRemove()  # Убираем клавиатуру для ввода текста
    )

@dp.message(F.from_user.id.in_(user_data.keys()))  # Ловим сообщения только от тех, кто начал заявку
async def process_application(message: types.Message):
    """Обработка шагов заявки"""
    user_id = message.from_user.id
    data = user_data[user_id]
    
    if data['step'] == 'ask_fio':
        # Шаг 1: Получили ФИО, переходим к выбору отряда
        data['fio'] = message.text
        data['step'] = 'ask_squad'
        
        await message.answer(
            f"Приятно познакомиться, <b>{message.text}</b>!\n\n"
            "Теперь выбери <b>отряд</b>, в который хочешь вступить:",
            reply_markup=get_squad_keyboard()
        )
        
    elif data['step'] == 'ask_squad':
        # Шаг 2: Получили отряд, завершаем заявку
        # Убираем эмодзи для чистоты данных
        squad = message.text.replace("🏗️ ", "").replace("👨‍🏫 ", "").replace("🧭 ", "")
        data['squad'] = squad
        
        # Сохраняем заявку в файл (временное решение)
        try:
            with open("applications.txt", "a", encoding="utf-8") as f:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] ID: {user_id} | ФИО: {data['fio']} | Отряд: {data['squad']}\n")
        except Exception as e:
            logger.error(f"Не удалось сохранить в файл: {e}")
        
        # Отправляем подтверждение пользователю
        final_text = (
            "✅ <b>Заявка успешно подана!</b>\n\n"
            f"<b>Твои данные:</b>\n"
            f"• ФИО: {data['fio']}\n"
            f"• Отряд: {data['squad']}\n\n"
            "Спасибо за интерес! Ответственный за отряд свяжется с тобой "
            "в Telegram в ближайшее время.\n\n"
            "Хочешь подать ещё одну заявку? Просто нажми /start"
        )
        await message.answer(final_text, reply_markup=get_main_keyboard())
        
        # Удаляем временные данные пользователя
        del user_data[user_id]

@dp.message()
async def other_messages(message: types.Message):
    """Обработка любых других сообщений"""
    await message.answer(
        "Используй кнопки меню или команды!\n"
        "Если хочешь начать заново — отправь /start",
        reply_markup=get_main_keyboard()
    )

# ========== ЗАПУСК БОТА ==========
async def main():
    """Главная функция запуска"""
    logger.info("🤖 Бот СТО КАИ запускается...")
    # Удаляем старые обновления, чтобы начать с чистого листа
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("✅ Бот запущен и готов к работе!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())