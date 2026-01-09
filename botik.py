import os
import asyncio
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.enums import ParseMode
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Токен бота
TOKEN = "8476736003:AAEgnoPZZ6mPkvq79BVsPEI7p6taccIZv40"

# Настройки Google Sheets
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "C:\\Users\\User\\Downloads\\bot_sto_kai\\service_account.json"
SPREADSHEET_ID = "189NwGYIKqNFaBRjnbPnOGVDqAnQv4Hrc008AP3asGYI"

# ID кураторов
CURATOR_IDS = {
    "Проводники": 1697354206,
    "Вожатые": 1487811188,
    "Строители": 841168856
}

# Авторизация в Google Sheets
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Создание состояний
class Form(StatesGroup):
    fio = State()
    squad = State()
    source = State()
    other_source = State()

# Функция для проверки, подавал ли пользователь уже заявку
async def has_user_applied(user_id: int) -> bool:
    try:
        # Получаем все данные из таблицы
        all_records = sheet.get_all_values()
        
        # Проверяем каждый ряд (пропускаем заголовки если они есть)
        for row in all_records:
            # ID пользователя находится в 4-й колонке (индекс 3)
            if len(row) > 3 and row[3] == str(user_id):
                return True
        return False
    except Exception as e:
        logging.error(f"Ошибка при проверке заявки пользователя: {e}")
        return False

# Главное меню
def get_main_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Подать заявку"))
    return keyboard.as_markup(resize_keyboard=True)

# Клавиатура выбора отряда
def get_squad_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Строители"))
    keyboard.add(KeyboardButton(text="Вожатые"))
    keyboard.add(KeyboardButton(text="Проводники"))
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

# Клавиатура выбора источника информации
def get_source_keyboard():
    keyboard = ReplyKeyboardBuilder()
    keyboard.add(KeyboardButton(text="Посоветовали"))
    keyboard.add(KeyboardButton(text="Увидел(а) плакат"))
    keyboard.add(KeyboardButton(text="На агитации"))
    keyboard.add(KeyboardButton(text="Иначе"))
    keyboard.adjust(1)
    return keyboard.as_markup(resize_keyboard=True)

# Обработчик команды /start
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    welcome_text = (
        "<b>Привет! 👋</b>\n\n"
        "Это бот <a href='https://t.me/knitu_kai_sto'>Штаба СТО КНИТУ‑КАИ</a> — "
        "места, где рождаются яркие события и крепкие дружеские связи.\n\n"
        "Хочешь стать частью нашей команды? Нажми <b>«Подать заявку»</b>, "
        "и мы расскажем, как присоединиться."
    )
    await message.answer(welcome_text, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_main_keyboard())

# Обработчик кнопки "Подать заявку"
@dp.message(F.text == "Подать заявку")
async def start_application(message: types.Message, state: FSMContext):
    # Проверяем, не подавал ли пользователь уже заявку
    has_applied = await has_user_applied(message.from_user.id)
    
    if has_applied:
        # Пользователь уже подавал заявку
        already_applied_text = (
            "🚫 <b>Вы уже подавали заявку!</b>\n\n"
            "Мы получили вашу заявку и уже обрабатываем её. "
            "В ближайшее время с вами свяжется представитель отряда.\n\n"
            "Если у вас есть вопросы, напишите нам в телеграм: "
            "<a href='https://t.me/knitu_kai_sto'>@knitu_kai_sto</a>"
        )
        await message.answer(already_applied_text, 
                           parse_mode=ParseMode.HTML)
        return
    
    # Если заявки нет, начинаем процесс
    intro_text = (
        "<b>Отлично, что ты с нами! ✨</b>\n\n"
        "Давай начнём твоё приключение в Штабе СТО КНИТУ‑КАИ. Для заявки "
        "нам нужно узнать твоё полное имя\n\n"
        "<i>Например: Васильева Анна.</i>\n\n"
        "Ждём с нетерпением! 😊"
    )
    await state.set_state(Form.fio)
    await message.answer(intro_text, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=ReplyKeyboardRemove())

# Обработчик ввода ФИО
@dp.message(Form.fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await state.set_state(Form.squad)
    
    squad_text = (
        "<b>Здорово! Теперь давай решим, где ты будешь раскрываться на полную.</b>\n\n"
        "У нас три пути:\n\n"
        "<b>💙Строительный отряд «Север»</b> — если любишь создавать что‑то "
        "масштабное и работать в команде.\n\n"
        "<b>💙Отряд вожатых «Искра»</b> — если хочешь вдохновлять и вести за собой.\n\n"
        "<b>💙Отряд проводников «Зилант»</b> — если тянет к путешествиям и железной дороге.\n\n"
        "<b>Какой вариант тебе ближе?</b>"
    )
    await message.answer(squad_text, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_squad_keyboard())

# Обработчик выбора отряда
@dp.message(Form.squad)
async def process_squad(message: types.Message, state: FSMContext):
    if message.text not in ["Строители", "Вожатые", "Проводники"]:
        await message.answer("Пожалуйста, выберите отряд, используя кнопки ниже.")
        return
    
    await state.update_data(squad=message.text)
    await state.set_state(Form.source)
    
    source_text = (
        "<b>Принято! ❤️</b>\n\n"
        "Расскажи, пожалуйста, как ты нашёл информацию о нас?\n\n"
        "Нам важно понимать, какие каналы работают лучше всего!"
    )
    await message.answer(source_text, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_source_keyboard())

# Обработчик выбора стандартного источника
@dp.message(Form.source, F.text.in_(["Посоветовали", "Увидел(а) плакат", "На агитации"]))
async def process_standard_source(message: types.Message, state: FSMContext):
    await state.update_data(source=message.text)
    await complete_application(message, state)

# Обработчик выбора "иначе"
@dp.message(Form.source, F.text == "Иначе")
async def process_other_source_option(message: types.Message, state: FSMContext):
    await state.set_state(Form.other_source)
    await message.answer("Пожалуйста, расскажи, как именно ты узнал(а) о Штабе:", 
                        parse_mode=ParseMode.HTML,
                        reply_markup=ReplyKeyboardRemove())

# Обработчик ввода другого источника
@dp.message(Form.other_source)
async def process_other_source_text(message: types.Message, state: FSMContext):
    # Проверяем, что пользователь что-то ввел
    if not message.text or message.text.strip() == "":
        await message.answer("Пожалуйста, расскажи, как именно ты узнал(а) о Штабе:")
        return
    
    await state.update_data(source=f"Иначе: {message.text}")
    await complete_application(message, state)

# Завершение заявки и отправка уведомлений
async def complete_application(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    
    # Отладка: проверяем, что данные получены
    logging.info(f"Данные пользователя: {user_data}")
    
    # Проверяем наличие всех необходимых данных
    if not user_data.get('fio') or not user_data.get('squad') or not user_data.get('source'):
        await message.answer("Произошла ошибка при обработке данных. Пожалуйста, начните заново.", 
                           reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    # Еще раз проверяем, не подавал ли пользователь заявку (на случай параллельных запросов)
    has_applied = await has_user_applied(message.from_user.id)
    
    if has_applied:
        already_applied_text = (
            "🚫 <b>Ты уже подавал заявку!</b>\n\n"
            "Мы уже обрабатываем её, в ближайшее время с тобой свяжется представитель отряда. "
            "Если у тебя остались вопросы, напиши телеграм командиру Штаба СТО КНИТУ0КАИ: @ThrustMedia "
        )
        await message.answer(already_applied_text, 
                           parse_mode=ParseMode.HTML,
                           reply_markup=get_main_keyboard())
        await state.clear()
        return
    
    # Сохранение в Google Sheets
    try:
        # Добавляем дату подачи заявки
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        row = [
            user_data.get('fio'),
            user_data.get('squad'),
            user_data.get('source'),
            str(message.from_user.id),
            f"@{message.from_user.username}" if message.from_user.username else "Нет username",
            current_time  # Добавляем дату подачи
        ]
        sheet.append_row(row)
        logging.info("Данные успешно сохранены в Google Sheets")
    except Exception as e:
        logging.error(f"Ошибка при сохранении в Google Sheets: {e}")
        # Не прерываем процесс, просто логируем ошибку
    
    # Отправка финального сообщения пользователю
    final_text = (
        "<b>Спасибо за заявку! ✨</b>\n\n"
        "Мы получили твои данные и уже обрабатываем их. В ближайшее время с тобой свяжется "
        "представитель отряда — расскажет о дальнейших шагах и ответит на вопросы.\n\n"
        "Оставайся на связи и следи за уведомлениями!\n\n"
        "До встречи в Штабе СТО КНИТУ‑КАИ! 🚀"
    )
    await message.answer(final_text, 
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_main_keyboard())
    
    # Отправка уведомления куратору
    try:
        squad = user_data.get('squad')
        curator_id = CURATOR_IDS.get(squad)
        
        if curator_id:
            notification_text = (
                "📢 <b>Новая заявка в боте Штаба СТО КНИТУ‑КАИ!</b>\n\n"
                f"<b>ФИО:</b> {user_data.get('fio')}\n"
                f"<b>Отряд:</b> {squad}\n"
                f"<b>Источник:</b> {user_data.get('source')}\n"
                f"<b>Ник в Telegram:</b> @{message.from_user.username if message.from_user.username else 'нет'}\n"
                f"<b>ID:</b> {message.from_user.id}\n"
                f"<b>Дата:</b> {current_time}"
            )
            await bot.send_message(curator_id, 
                                 notification_text, 
                                 parse_mode=ParseMode.HTML)
            logging.info(f"Уведомление отправлено куратору отряда {squad} (ID: {curator_id})")
    except Exception as e:
        logging.error(f"Ошибка при отправке уведомления куратору: {e}")
    
    await state.clear()
    logging.info("Состояние пользователя очищено")

# Добавляем обработчик для сообщений, которые не соответствуют текущему состоянию
@dp.message()
async def handle_other_messages(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    # Если пользователь в процессе заполнения заявки
    if current_state:
        state_name = current_state.split(':')[1] if ':' in current_state else current_state
        
        if state_name == "fio":
            await message.answer("Пожалуйста, введите ваше ФИО (например: Иванов Иван)")
        elif state_name == "squad":
            await message.answer("Пожалуйста, выберите отряд, используя кнопки ниже.", 
                               reply_markup=get_squad_keyboard())
        elif state_name == "source":
            await message.answer("Пожалуйста, выберите источник информации, используя кнопки ниже.", 
                               reply_markup=get_source_keyboard())
        elif state_name == "other_source":
            await message.answer("Пожалуйста, расскажи, как именно ты узнал(а) о Штабе:")
    else:
        # Если пользователь не в процессе заполнения
        await message.answer("Нажми «Подать заявку», чтобы заполнить заявку в ряды Штаба СТО КНИТУ-КАИ.", 
                           reply_markup=get_main_keyboard())

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())