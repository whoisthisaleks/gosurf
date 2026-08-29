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

from weather import build_forecast
from decision_engine import build_recommendation


# ----------------------
# CONFIG
# ----------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://gosurf-bot.onrender.com/webhook"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()
app = Flask(__name__)


# ----------------------
# KEYBOARD
# ----------------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot"), KeyboardButton(text="Change level")],
            [KeyboardButton(text="About")],
        ],
        resize_keyboard=True,
    )


# ----------------------
# START
# ----------------------
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


# ----------------------
# MENU
# ----------------------
@dp.message(F.text == "Restart bot")
async def restart(message: Message):
    await start(message)


@dp.message(F.text == "Change level")
async def change_level(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
            [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
            [InlineKeyboardButton(text="Advanced", callback_data="level_advanced")],
        ]
    )
    await message.answer("What’s your level?", reply_markup=keyboard)


@dp.message(F.text == "About")
async def about(message: Message):
    await message.answer(
        "GoSurf helps you quickly find the best surf spot in Bali.\n\n"
        "We check waves, wind, and conditions for you — and give a simple recommendation "
        "so you can spend less time figuring it out and more time in the water.",
        reply_markup=get_main_keyboard(),
    )


# ----------------------
# LEVEL (FIXED)
# ----------------------
@dp.callback_query(F.data.startswith("level_"))
async def choose_level(callback: CallbackQuery):
    level = callback.data.replace("level_", "")

    await callback.answer()

    # 🔥 ВАЖНО: используем message.answer, а не callback.message
    await send_forecast(callback.message, level, is_first=True)


# ----------------------
# FORECAST
# ----------------------
async def send_forecast(message: Message, level: str, is_first=False):
    forecast = build_forecast()
    decision = build_recommendation(forecast, level)

    best = decision["best"]
    data = decision["conditions"]

    reasons = "\n".join([f"• {r}" for r in decision["reasons"]])
    alts = "\n".join([f"• {s}" for s in decision["alternatives"]])

    tide = data.get("tide")
    tide_text = f"{round(tide,1)} m" if tide else "not available"

    text = (
        f"<b>Best spot:</b> {best}\n"
        f"<b>Score:</b> {decision['score']}/100\n\n"
        f"<b>Why:</b>\n{reasons}\n\n"
        f"<b>Conditions:</b>\n"
        f"Wave: {data.get('wave_height')} m\n"
        f"Period: {data.get('period')} sec\n"
        f"Swell: {data.get('swell_direction')}\n"
        f"Wind: {data.get('wind_direction')} {data.get('wind_speed')} m/s\n"
        f"Tide: {tide_text}\n\n"
        f"<b>Alternative spots:</b>\n{alts}"
    )

    # ⚠️ Плашка если fallback
    if data.get("source") == "fallback":
        text += "\n\n<i>Some data is estimated (Stormglass unavailable)</i>"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{best}")],
            [InlineKeyboardButton(text="Alternative spots", callback_data=f"alts_{level}")],
            [InlineKeyboardButton(text="Update", callback_data=f"update_{level}")],
        ]
    )

    photo = FSInputFile("assets/best.png")

    await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)

    if is_first:
        await message.answer("You can also use the menu at the bottom")


# ----------------------
# UPDATE (FIX)
# ----------------------
@dp.callback_query(F.data.startswith("update_"))
async def update_forecast(callback: CallbackQuery):
    level = callback.data.replace("update_", "")
    await callback.answer("Updating...")
    await send_forecast(callback.message, level)


# ----------------------
# ALTERNATIVES (FIXED)
# ----------------------
@dp.callback_query(F.data.startswith("alts_"))
async def show_alternatives(callback: CallbackQuery):
    level = callback.data.replace("alts_", "")
    forecast = build_forecast()
    decision = build_recommendation(forecast, level)

    await callback.answer()

    alts = decision["alternatives"]

    if not alts:
        await callback.message.answer("No alternative spots")
        return

    photo = FSInputFile("assets/alt.png")
    await callback.message.answer_photo(photo=photo)

    for spot in alts[:2]:
        data = forecast.get(spot, {})

        tide = data.get("tide")
        tide_text = f"{round(tide,1)} m" if tide else "not available"

        text = (
            f"<b>Spot:</b> {spot}\n\n"
            f"<b>Conditions:</b>\n"
            f"Wave: {data.get('wave_height')} m\n"
            f"Period: {data.get('period')} sec\n"
            f"Swell: {data.get('swell_direction')}\n"
            f"Wind: {data.get('wind_direction')} {data.get('wind_speed')} m/s\n"
            f"Tide: {tide_text}"
        )

        await callback.message.answer(text)


# ----------------------
# MAP
# ----------------------
@dp.callback_query(F.data.startswith("map_"))
async def open_map(callback: CallbackQuery):
    spot = callback.data.replace("map_", "")

    maps = {
        "Uluwatu": "https://maps.google.com/?q=Uluwatu+Bali",
        "Canggu": "https://maps.google.com/?q=Canggu+Bali",
        "Kuta": "https://maps.google.com/?q=Kuta+Bali",
        "Medewi": "https://maps.google.com/?q=Medewi+Bali",
    }

    await callback.answer()
    await callback.message.answer(f"{spot}\n{maps.get(spot)}")


# ----------------------
# WEBHOOK (FIXED)
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.model_validate(request.json)

    asyncio.run(dp.feed_update(bot, update))  # 🔥 фикс loop

    return "ok"


@app.route("/")
def home():
    return "GoSurf bot is running"


# ----------------------
# STARTUP
# ----------------------
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    print("Webhook set")


if __name__ == "__main__":
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))