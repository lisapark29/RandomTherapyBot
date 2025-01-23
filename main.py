from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
from deep_translator import GoogleTranslator
import sqlite3
import csv

TOKEN = '7931784043:AAHmsZ9pQ8a-HYzCkLF0xXjOdlJrYBWsx_s'

bot = Bot(token=TOKEN)
dp = Dispatcher()


def init_db():
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS jokes (id INTEGER PRIMARY KEY, content TEXT, type TEXT)")
    cursor.execute("PRAGMA table_info(jokes)")
    columns = [column[1] for column in cursor.fetchall()]
    if "content" not in columns:
        cursor.execute("ALTER TABLE jokes ADD COLUMN content TEXT")
    if "type" not in columns:
        cursor.execute("ALTER TABLE jokes ADD COLUMN type TEXT")
    conn.commit()
    conn.close()


def add_content_to_db(content, content_type):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO jokes (content, type) VALUES (?, ?)", (content, content_type))
    conn.commit()
    conn.close()

def get_content_from_db(content_type):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT content FROM jokes WHERE type = ?", (content_type,))
    contents = cursor.fetchall()
    conn.close()
    return [content[0] for content in contents]

def export_db_to_csv(file_path):
    conn = sqlite3.connect("bot_data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jokes")
    rows = cursor.fetchall()
    conn.close()

    with open(file_path, mode='a+', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["id", "content", "type"])
        writer.writerows(rows)

def get_random_cat_fact():
    url = "https://catfact.ninja/fact"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        fact = data['fact']
        add_content_to_db(fact, "cat_fact")
        return fact
    except requests.exceptions.RequestException as e:
        return f"Ошибка при запросе: {e}"

def translate_text_to_russian(text: str) -> str:
    try:
        translated = GoogleTranslator(source='en', target='ru').translate(text)
        return translated
    except Exception as e:
        return f"Ошибка перевода: {e}"

def get_random_advice():
    url = "https://api.adviceslip.com/advice"
    try:
        response = requests.get(url, headers={"Accept": "application/json"})
        response.raise_for_status()
        data = response.json()
        advice = data['slip']['advice']
        add_content_to_db(advice, "advice")
        return advice
    except requests.exceptions.RequestException as e:
        return f"Ошибка при запросе: {e}"

def get_random_joke():
    url = "https://official-joke-api.appspot.com/random_joke"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        joke = f"{data['setup']} - {data['punchline']}"
        add_content_to_db(joke, "joke")
        return joke
    except requests.exceptions.RequestException as e:
        return f"Ошибка при запросе: {e}"

async def get_inline_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Советы", callback_data="advice")],
            [InlineKeyboardButton(text="Анекдоты", callback_data="joke")],
            [InlineKeyboardButton(text="Факты о котах", callback_data="cat_fact")],
            [InlineKeyboardButton(text="Мои записи", callback_data="my_content")],
            [InlineKeyboardButton(text="Экспорт базы", callback_data="export_db")]
        ]
    )

async def send_my_content(callback: CallbackQuery):
    jokes = get_content_from_db("joke")
    advices = get_content_from_db("advice")
    cat_facts = get_content_from_db("cat_fact")

    response = "Твои записи:\n\n"
    if jokes:
        response += "Анекдоты:\n" + "\n".join(jokes) + "\n\n"
    if advices:
        response += "Советы:\n" + "\n".join(advices) + "\n\n"
    if cat_facts:
        response += "Факты о котах:\n" + "\n".join(cat_facts) + "\n\n"

    if response == "Твои записи:\n\n":
        response = "У тебя еще нет сохраненных записей."

    await callback.message.answer(response)
    await callback.answer()

async def export_database(callback: CallbackQuery):
    file_path = "jokes_export.csv"
    export_db_to_csv(file_path)
    await callback.message.answer(f"База данных успешно экспортирована в файл {file_path}.")
    await callback.answer()

async def send_advice(callback: CallbackQuery):
    advice = get_random_advice()
    advice_in_russian = translate_text_to_russian(advice)
    await callback.message.answer(f"Интернет советует: {advice_in_russian}")
    await callback.answer()

async def send_joke(callback: CallbackQuery):
    joke = get_random_joke()
    joke_in_russian = translate_text_to_russian(joke)
    await callback.message.answer(f"Анекдот дня: {joke_in_russian}")
    await callback.answer()

async def send_cat_fact(callback: CallbackQuery):
    fact = get_random_cat_fact()
    fact_in_russian = translate_text_to_russian(fact)
    await callback.message.answer(f"Факт дня о котах: {fact_in_russian}")
    await callback.answer()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет!\nНам хочется тебя поддержать! Выбери вещь, которую хочешь услышать: ",
                         reply_markup=await get_inline_keyboard())

@dp.callback_query()
async def callback_handler(callback: CallbackQuery):
    if callback.data == "advice":
        await send_advice(callback)
    elif callback.data == "joke":
        await send_joke(callback)
    elif callback.data == "cat_fact":
        await send_cat_fact(callback)
    elif callback.data == "my_content":
        await send_my_content(callback)
    elif callback.data == "export_db":
        await export_database(callback)

@dp.message(Command("help"))
async def process_help_command(message: Message):
    await message.reply("Чтобы начать общение с ботом, напиши /start!")

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())