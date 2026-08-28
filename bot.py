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

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


# ----------------------
# FORMATTER
# ----------------------
def format_recommendation(rec):
    spot = rec["best"]
    conditions = rec["conditions"]
    reasons = rec["reasons"]
    alternatives = rec["alternatives"]
    best_time = rec.get("best_time")

    wave = round(conditions.get("wave_height", 0), 1)
    period = round(conditions.get("period", 0), 1)
    swell = conditions.get("swell_direction", "-")
    wind_speed = round(conditions.get("wind_speed", 0), 1)
    wind_dir = conditions.get("wind_direction", "-")
    tide = conditions.get("tide")

    if wind_dir == "unknown":
        wind_text = "unavailable"
    else:
        wind_text = f"{wind_dir} {wind_speed} m/s"

    tide_text = tide if tide is not None else "-"

    # порядок: сначала spot, потом time
    text = f"<b>Best spot:</b> {spot}\n"

    if best_time:
        text += f"Best time: {best_time}\n\n"
    else:
        text += "\n"

    text += (
        f"<b>Conditions:</b>\n"
        f"Wave: {wave} m\n"
        f"Period: {period} sec\n"
        f"Swell: {swell}\n"
        f"Wind: {wind_text}\n"
        f"Tide: {tide_text}\n\n"
        f"<b>Why:</b>\n"
    )

    for r in reasons[:3]:
        text += f"- {r}\n"

    if alternatives:
        text += "\n<b>Alternative spots:</b>\n"
        for i, alt in enumerate(alternatives):
            if i == 0:
                text += f"{alt}\n"
            else:
                text += f"{alt}"

    return text.strip()


# ----------------------
# KEYBOARD
# ----------------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot"), KeyboardButton(text="Change level")],
            [KeyboardButton(text="Your profile"), KeyboardButton(text="About & support")],
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
            "GoSurf — real-time ocean data analysis\n\n"
            "<b>Hey surfer!</b>"
        ),
        reply_markup=get_main_keyboard(),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
            [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
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
        ]
    )
    await message.answer("What’s your level?", reply_markup=keyboard)


@dp.message(F.text == "Your profile")
async def profile(message: Message):
    await message.answer("Profile coming soon", reply_markup=get_main_keyboard())


@dp.message(F.text == "About & support")
async def about(message: Message):
    await message.answer(
        "GoSurf helps you find the best surf spot in Bali.\n\nSupport: @yourusername",
        reply_markup=get_main_keyboard(),
    )


# ----------------------
# LEVEL
# ----------------------
@dp.callback_query(F.data.startswith("level_"))
async def choose_level(callback: CallbackQuery):
    level = callback.data.replace("level_", "")
    await callback.answer()
    await send_forecast(callback.message, level, is_first=True)


# ----------------------
# FORECAST
# ----------------------
async def send_forecast(message: Message, level: str, is_first=False):
    hourly = build_hourly_forecast()
    forecast = {spot: hours[0] for spot, hours in hourly.items()}

    decision = build_recommendation(
        forecast,
        level,
        hourly_forecast=hourly
    )

    text = format_recommendation(decision)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{decision['best']}")],
            [InlineKeyboardButton(text="Alternative spots", callback_data=f"alts_{level}")],
            [InlineKeyboardButton(text="Update", callback_data=f"update_{level}")],
        ]
    )

    photo = FSInputFile("assets/best.png")

    await message.answer_photo(photo=photo, caption=text, reply_markup=keyboard)

    if is_first:
        await message.answer("You can also use the menu at the bottom")


# ----------------------
# ALTERNATIVES
# ----------------------
@dp.callback_query(F.data.startswith("alts_"))
async def show_alternatives(callback: CallbackQuery):
    level = callback.data.replace("alts_", "")
    forecast = build_forecast()

    decision = build_recommendation(forecast, level)

    await callback.answer()

    alts = decision["alternatives"]

    if len(alts) < 2:
        await callback.message.answer("No alternative spots")
        return

    photo = FSInputFile("assets/alt.png")
    await callback.message.answer_photo(photo=photo)

    for spot in alts[:2]:
        data = forecast.get(spot, {})

        wind_dir = data.get("wind_direction", "-")
        wind_speed = round(data.get("wind_speed", 0), 1)

        if wind_dir == "unknown":
            wind_text = "unavailable"
        else:
            wind_text = f"{wind_dir} {wind_speed} m/s"

        tide = data.get("tide")
        tide_text = tide if tide is not None else "-"

        text = (
            f"<b>Spot:</b> {spot}\n\n"
            f"<b>Conditions:</b>\n"
            f"Wave: {round(data.get('wave_height', 0), 1)} m\n"
            f"Period: {round(data.get('period', 0), 1)} sec\n"
            f"Swell: {data.get('swell_direction', '-')}\n"
            f"Wind: {wind_text}\n"
            f"Tide: {tide_text}"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Open map", callback_data=f"map_{spot}")]
            ]
        )

        await callback.message.answer(text, reply_markup=keyboard)


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
# WEBHOOK
# ----------------------
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    update = Update.model_validate(data)

    loop.run_until_complete(dp.feed_update(bot, update))
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
    loop.run_until_complete(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))