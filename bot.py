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


keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner"), KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")],
        [KeyboardButton(text="Update"), KeyboardButton(text="About")]
    ],
    resize_keyboard=True
)


def format_response(r):
    c = r["conditions"]

    tide = f"{c['tide']} m" if c["tide"] else "unknown"

    text = f"""🏄‍♂️ {r['spot']}

Best time: {r['best_time']}

Score: {r['score']}/100

Why:
• {r['reason'][0]}
• {r['reason'][1]}

Conditions:
Wave: {c['wave_height']} m
Period: {c['period']} sec
Swell: {c['swell_direction']}
Wind: {c['wind_direction']} {c['wind_speed']} m/s
Tide: {tide}

Alternative spots:
• {r['alternatives'][0]}
• {r['alternatives'][1]}
"""

    if c["source"] == "fallback":
        text += "\n⚠️ Live data temporarily unavailable"

    return text


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "Hey surfer!\n\nLooking for waves?\nWe use real-time ocean data to find your best spot today.",
        reply_markup=keyboard
    )


@dp.message(lambda m: m.text in ["Beginner", "Intermediate", "Advanced"])
async def level(message: types.Message):
    forecast = build_forecast()
    result = get_best_spot(forecast, message.text.lower())
    await message.answer(format_response(result))


@dp.message(lambda m: m.text == "Update")
async def update(message: types.Message):
    forecast = build_forecast()
    result = get_best_spot(forecast, "intermediate")
    await message.answer(format_response(result))


@dp.message(lambda m: m.text == "About")
async def about(message: types.Message):
    await message.answer(
        "GoSurf helps you quickly find the best surf spot in Bali.\n\nWe check waves, wind, and conditions for you."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())