import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from weather import build_forecast
from decision_engine import get_best_spot

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# -------------------------
# UI
# -------------------------
level_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner"), KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")],
        [KeyboardButton(text="Update"), KeyboardButton(text="About")]
    ],
    resize_keyboard=True
)

# -------------------------
# TEXTS
# -------------------------
START_TEXT = """Hey surfer!

Looking for waves?
We use real-time ocean data to find your best spot today.
"""

ABOUT_TEXT = """GoSurf helps you quickly find the best surf spot in Bali.

We check waves, wind, and conditions for you — and give a simple recommendation so you can spend less time figuring it out and more time in the water.
"""

WARNING_TEXT = "\n\n⚠️ Some data may be unavailable right now."

# -------------------------
# HELPERS
# -------------------------
def format_response(result):
    spot = result["spot"]
    score = result["score"]
    reason = result["reason"]
    conditions = result["conditions"]
    alternatives = result["alternatives"]
    best_time = result["best_time"]

    tide = conditions.get("tide")
    tide_text = f"{tide} m" if tide else "unknown"

    text = f"""🏄‍♂️ {spot}

Best time: {best_time}

Score: {score}/100

Why:
• {reason[0]}
• {reason[1]}

Conditions:
Wave: {conditions['wave_height']} m
Period: {conditions['period']} sec
Swell: {conditions['swell_direction']}
Wind: {conditions['wind_direction']} {conditions['wind_speed']} m/s
Tide: {tide_text}

Alternative spots:
• {alternatives[0]}
• {alternatives[1]}
"""

    if conditions["source"] == "fallback":
        text += WARNING_TEXT

    return text

# -------------------------
# HANDLERS
# -------------------------
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(START_TEXT, reply_markup=level_keyboard)


@dp.message(lambda message: message.text in ["Beginner", "Intermediate", "Advanced"])
async def level_handler(message: types.Message):
    level = message.text.lower()

    forecast = build_forecast()
    result = get_best_spot(forecast, level)

    text = format_response(result)

    await message.answer(text)


@dp.message(lambda message: message.text == "Update")
async def update_handler(message: types.Message):
    forecast = build_forecast()
    result = get_best_spot(forecast, "intermediate")

    text = format_response(result)

    await message.answer(text)


@dp.message(lambda message: message.text == "About")
async def about_handler(message: types.Message):
    await message.answer(ABOUT_TEXT)


# -------------------------
# MAIN
# -------------------------
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())