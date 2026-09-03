import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from config import TOKEN
from weather import get_spots_data
from decision_engine import pick_best

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_level = {}

# --- keyboards ---
level_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner")],
        [KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")]
    ],
    resize_keyboard=True
)

menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Update"), KeyboardButton(text="Alternative spots")],
        [KeyboardButton(text="Restart bot"), KeyboardButton(text="Change Level")],
        [KeyboardButton(text="About"), KeyboardButton(text="Pro")]
    ],
    resize_keyboard=True
)

# --- start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer_photo(
        photo=types.FSInputFile("assets/start.png"),
        caption="**Hey surfer 🌊**\nWhat's your level?",
        parse_mode="Markdown",
        reply_markup=level_kb
    )

# --- level selected ---
@dp.message(lambda m: m.text in ["Beginner", "Intermediate", "Advanced"])
async def handle_level(message: types.Message):
    level = message.text.lower()
    user_level[message.from_user.id] = level

    spots = get_spots_data()
    best, alternatives = pick_best(spots, level)

    text = (
        f"🏄 **Best spot: {best['name']} (score {best['score']}/100)**\n\n"
        f"**Conditions:**\n"
        f"Wave: {best['wave']}m\n"
        f"Wind: {best['wind']} m/s\n"
        f"Period: {best['period']}s\n\n"
        f"**Alternatives:**\n"
        f"{alternatives[0]['name']}, {alternatives[1]['name']}"
    )

    await message.answer_photo(
        photo=types.FSInputFile("assets/best.png"),
        caption=text,
        parse_mode="Markdown",
        reply_markup=menu_kb
    )

# --- update ---
@dp.message(lambda m: m.text == "Update")
async def update(message: types.Message):
    level = user_level.get(message.from_user.id, "beginner")

    spots = get_spots_data()
    best, alternatives = pick_best(spots, level)

    await message.answer(
        f"🏄 **Best spot: {best['name']} ({best['score']})**",
        parse_mode="Markdown"
    )

# --- alternatives ---
@dp.message(lambda m: m.text == "Alternative spots")
async def alternatives_handler(message: types.Message):
    level = user_level.get(message.from_user.id, "beginner")

    spots = get_spots_data()
    _, alternatives = pick_best(spots, level)

    for spot in alternatives:
        text = (
            f"🏄 **{spot['name']}**\n\n"
            f"**Conditions:**\n"
            f"Wave: {spot['wave']}m\n"
            f"Wind: {spot['wind']} m/s\n"
            f"Period: {spot['period']}s"
        )

        await message.answer_photo(
            photo=types.FSInputFile("assets/alt.png"),
            caption=text,
            parse_mode="Markdown"
        )

# --- run ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())