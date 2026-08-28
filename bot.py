import asyncio
import os
import threading

from flask import Flask
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile
)

from weather import build_forecast
from decision_engine import build_recommendation

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

app = Flask(__name__)


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
            "Hey surfer!"
        ),
        reply_markup=get_main_keyboard(),
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
            [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")]
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
    await send_forecast(callback.message, level)


# ----------------------
# FORECAST
# ----------------------
async def send_forecast(message: Message, level: str):
    forecast = build_forecast()
    decision = build_recommendation(forecast, level)

    best = decision["best"]
    best_data = decision["conditions"]

    photo = FSInputFile("assets/best.png")

    reasons_text = "\n".join([f"• {r.capitalize()}" for r in decision["reasons"]])
    alternatives_text = "\n".join([f"• {spot}" for spot in decision["alternatives"]])

    text = f"""
Best spot: {best}
Score: {decision['score']}/100

Why:
{reasons_text}

**Conditions:**
Wave: {round(best_data.get('wave_height', 0), 1)} m
Period: {round(best_data.get('period', 0), 1)} sec
Swell: {best_data.get('swell_direction', '-')}
Wind: {best_data.get('wind_direction', '-')} {round(best_data.get('wind_speed', 0), 1)} m/s

Alternatives:
{alternatives_text}
"""

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Update", callback_data=f"update_{level}")],
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{best}")],
            [InlineKeyboardButton(text="Alternative spots", callback_data=f"alts_{level}")]
        ]
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

    await message.answer("Use the menu below.", reply_markup=get_main_keyboard())


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
        await callback.message.answer(
            "No alternative spots available",
            reply_markup=get_main_keyboard(),
        )
        return

    alt1 = alternatives[0]
    alt2 = alternatives[1]

    alt1_data = forecast.get(alt1, {})
    alt2_data = forecast.get(alt2, {})

    # 📸 картинка перед блоком
    photo = FSInputFile("assets/alt.png")
    await callback.message.answer_photo(
        photo=photo,
        reply_markup=get_main_keyboard(),
    )

    # -------- FIRST --------
    text1 = f"""
Spot: {alt1}
Score: 85/100

**Conditions:**
Wave: {round(alt1_data.get('wave_height', 0), 1)} m
Period: {round(alt1_data.get('period', 0), 1)} sec
Swell: {alt1_data.get('swell_direction', '-')}
Wind: {alt1_data.get('wind_direction', '-')} {round(alt1_data.get('wind_speed', 0), 1)} m/s
"""

    keyboard1 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{alt1}")]
        ]
    )

    await callback.message.answer(
        text1,
        parse_mode="Markdown",
        reply_markup=keyboard1
    )

    # -------- SECOND --------
    text2 = f"""
Spot: {alt2}
Score: 80/100

**Conditions:**
Wave: {round(alt2_data.get('wave_height', 0), 1)} m
Period: {round(alt2_data.get('period', 0), 1)} sec
Swell: {alt2_data.get('swell_direction', '-')}
Wind: {alt2_data.get('wind_direction', '-')} {round(alt2_data.get('wind_speed', 0), 1)} m/s
"""

    keyboard2 = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", callback_data=f"map_{alt2}")]
        ]
    )

    await callback.message.answer(
        text2,
        parse_mode="Markdown",
        reply_markup=keyboard2
    )


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
        "Medewi": "https://maps.google.com/?q=Medewi+Bali"
    }

    await callback.answer()
    await callback.message.answer(
        f"{spot}\n{maps.get(spot)}",
        reply_markup=get_main_keyboard(),
    )


# ----------------------
# WEB (Render)
# ----------------------
@app.route("/")
def home():
    return "GoSurf bot is running"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


# ----------------------
# RUN
# ----------------------
async def main():
    print("GoSurf bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    asyncio.run(main())
