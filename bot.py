import asyncio
import os
from flask import Flask, request
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    CallbackQuery,
    FSInputFile,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    Message,
    Update,
)

from weather import build_forecast
from decision_engine import build_recommendation

# ----------------------
# INIT
# ----------------------
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://gosurf-bot.onrender.com

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
app = Flask(__name__)

# ----------------------
# KEYBOARD (BOTTOM MENU)
# ----------------------
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Restart bot"),
                KeyboardButton(text="Change level"),
            ],
            [
                KeyboardButton(text="Your profile"),
                KeyboardButton(text="About & support"),
            ],
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
            "GoSurf — real-time ocean data analysis to pick the best surf spot right now\n\n"
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
# MAIN MENU
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
        "GoSurf helps you find the best surf spot in Bali based on real-time conditions.\n\n"
        "Support: @yourusername",
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
    forecast = build_forecast()
    decision = build_recommendation(forecast, level)

    best = decision["best"]
    best_data = decision["conditions"]

    photo = FSInputFile("assets/best.png")

    reasons_text = "\n".join([f"• {r.capitalize()}" for r in decision["reasons"]])
    alternatives_text = "\n".join([f"• {s}" for s in decision["alternatives"]])

    text = (
        f"<b>Best spot:</b> {best}\n"
        f"<b>Score:</b> {decision['score']}/100\n\n"
        f"<b>Why:</b>\n{reasons_text}\n\n"
        f"<b>Conditions:</b>\n"
        f"Wave: {round(best_data.get('wave_height', 0), 1)} m\n"
        f"Period: {round(best_data.get('period', 0), 1)} sec\n"
        f"Swell: {best_data.get('swell_direction', '-')}\n"
        f"Wind: {best_data.get('wind_direction', '-')} "
        f"{round(best_data.get('wind_speed', 0), 1)} m/s\n\n"
        f"<b>Alternatives:</b>\n{alternatives_text}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{best}")],
            [InlineKeyboardButton(text="Alternative spots", callback_data=f"alts_{level}")],
            [InlineKeyboardButton(text="Update", callback_data=f"update_{level}")],
        ]
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=keyboard,
    )

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

    alternatives = decision["alternatives"]

    if len(alternatives) < 2:
        await callback.message.answer("No alternative spots available")
        return

    alt1, alt2 = alternatives[:2]

    photo = FSInputFile("assets/alt.png")
    await callback.message.answer_photo(photo=photo)

    for spot in [alt1, alt2]:
        data = forecast.get(spot, {})

        text = (
            f"<b>Spot:</b> {spot}\n"
            f"<b>Score:</b> --\n\n"
            f"<b>Conditions:</b>\n"
            f"Wave: {round(data.get('wave_height', 0), 1)} m\n"
            f"Period: {round(data.get('period', 0), 1)} sec\n"
            f"Swell: {data.get('swell_direction', '-')}\n"
            f"Wind: {data.get('wind_direction', '-')} "
            f"{round(data.get('wind_speed', 0), 1)} m/s"
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Open map", callback_data=f"map_{spot}")]
            ]
        )

        await callback.message.answer(text, reply_markup=keyboard)

# ----------------------
# UPDATE
# ----------------------
@dp.callback_query(F.data.startswith("update_"))
async def update_forecast(callback: CallbackQuery):
    level = callback.data.replace("update_", "")
    await callback.answer("Updating...")
    await send_forecast(callback.message, level)

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
# WEBHOOK (CRITICAL)
# ----------------------
@app.route(f"/{BOT_TOKEN}", methods=["POST"])
def webhook():
    update = Update.model_validate(request.json)
    asyncio.run(dp.feed_update(bot, update))
    return "ok"

@app.route("/")
def home():
    return "GoSurf bot is running"

# ----------------------
# START
# ----------------------
async def on_startup():
    await bot.set_webhook(f"{WEBHOOK_URL}/{BOT_TOKEN}")

if __name__ == "__main__":
    asyncio.run(on_startup())
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))