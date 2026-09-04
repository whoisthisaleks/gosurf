import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command

from config import TELEGRAM_TOKEN
from weather import get_spots_data
from decision_engine import pick_best_spots

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- STATE ---
user_level = {}

# --- KEYBOARDS ---

level_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner")],
        [KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")]
    ],
    resize_keyboard=True
)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Update")],
        [KeyboardButton(text="Change level")],
        [KeyboardButton(text="Restart")]
    ],
    resize_keyboard=True
)

# --- TEXT TEMPLATES ---

def format_best_spot(spot, level):
    return (
        f"Best spot: {spot['name']}\n\n"
        f"Conditions:\n"
        f"- Wave: {spot['wave']} m\n"
        f"- Period: {spot['period']} s\n"
        f"- Wind: {spot['wind']}\n\n"
        f"Recommended for: {level}"
    )


def format_alt_spot(spot):
    return (
        f"{spot['name']}\n"
        f"Wave: {spot['wave']} m | "
        f"Period: {spot['period']} s | "
        f"Wind: {spot['wind']}"
    )


# --- HANDLERS ---

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer_photo(
        photo=FSInputFile("assets/start.png"),
        caption="GoSurf\n\nSelect your level:",
        reply_markup=level_kb
    )


@dp.message(lambda message: message.text in ["Beginner", "Intermediate", "Advanced"])
async def set_level(message: types.Message):
    user_level[message.from_user.id] = message.text

    await message.answer("Level saved. Fetching forecast...")

    await send_recommendation(message)


@dp.message(lambda message: message.text == "Update")
async def update(message: types.Message):
    await message.answer("Updating forecast...")
    await send_recommendation(message)


@dp.message(lambda message: message.text == "Change level")
async def change_level(message: types.Message):
    await message.answer("Select your level:", reply_markup=level_kb)


@dp.message(lambda message: message.text == "Restart")
async def restart(message: types.Message):
    user_level.pop(message.from_user.id, None)
    await start(message)


# --- CORE LOGIC ---

async def send_recommendation(message: types.Message):
    level = user_level.get(message.from_user.id)

    if not level:
        await message.answer("Please select your level first.", reply_markup=level_kb)
        return

    spots = get_spots_data()
    best, alternatives = pick_best_spots(spots, level)

    # --- BEST SPOT ---
    await message.answer_photo(
        photo=FSInputFile("assets/best.png"),
        caption=format_best_spot(best, level),
        reply_markup=main_kb
    )

    # --- ALTERNATIVES ---
    if alternatives:
        first = True

        for alt in alternatives:
            if first:
                await message.answer_photo(
                    photo=FSInputFile("assets/alt.png"),
                    caption="Alternative spots:\n\n" + format_alt_spot(alt)
                )
                first = False
            else:
                await message.answer(format_alt_spot(alt))


# --- RUN ---

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())