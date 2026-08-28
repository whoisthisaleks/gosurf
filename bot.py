import asyncio
import os
from flask import Flask, request
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Update,
    FSInputFile,
)
from aiogram.client.default import DefaultBotProperties

from weather import build_forecast, build_hourly_forecast
from decision_engine import build_recommendation


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://gosurf-bot.onrender.com/webhook"

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
app = Flask(__name__)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


def format_tide(tide):
    if tide is None:
        return "unknown"

    if tide < 0.8:
        state = "low"
    elif tide < 1.8:
        state = "mid"
    else:
        state = "high"

    return f"{state} ({round(tide,1)} m)"


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot"), KeyboardButton(text="Change level")],
            [KeyboardButton(text="About")],
        ],
        resize_keyboard=True,
    )


@dp.message(F.text == "/start")
async def start(message: Message):
    photo = FSInputFile("assets/start.png")

    await message.answer_photo(
        photo=photo,
        caption=(
            "Hey surfer!\n\n"
            "Looking for waves?\n"
            "We use real-time ocean data to find your best spot today."
        ),
        reply_markup=get_main_keyboard(),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
            [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
            [InlineKeyboardButton(text="Advanced", callback_data="level_advanced")],
        ]
    )

    await message.answer("What’s your level?", reply_markup=keyboard)


@dp.callback_query(F.data.startswith("level_"))
async def choose_level(callback: CallbackQuery):
    level = callback.data.replace("level_", "")
    await callback.answer()
    await send_forecast(callback.message, level)


async def send_forecast(message: Message, level: str):
    forecast = build_forecast()
    hourly = build_hourly_forecast()

    decision = build_recommendation(forecast, level, hourly)

    best = decision["best"]
    data = decision["conditions"]

    reasons = "\n".join([f"• {r}" for r in decision["reasons"]])
    alts = "\n".join([f"• {s}" for s in decision["alternatives"]])

    tide_text = format_tide(data.get("tide"))

    text = (
        f"<b>Best spot:</b> {best}\n"
        f"<b>Best time:</b> {decision.get('best_time')}\n"
        f"<b>Score:</b> {decision['score']}/100\n\n"
        f"<b>Why:</b>\n{reasons}\n\n"
        f"<b>Conditions:</b>\n"
        f"Wave: {round(data.get('wave_height', 0), 1)} m\n"
        f"Period: {round(data.get('period', 0), 1)} sec\n"
        f"Swell: {data.get('swell_direction', '-')}\n"
        f"Wind: {data.get('wind_direction', '-')} {round(data.get('wind_speed', 0), 1)} m/s\n"
        f"Tide: {tide_text}\n\n"
        f"<b>Alternative spots:</b>\n{alts}"
    )

    await message.answer(text)