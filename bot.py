from aiogram.types import FSInputFile
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
    KeyboardButton
)

from weather import build_forecast
from decision_engine import build_recommendation


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)


# ----------------------
# MAIN MENU (BOTTOM)
# ----------------------

def get_main_menu():
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
        resize_keyboard=True
    )


# ----------------------
# START
# ----------------------

@dp.message(F.text == "/start")
async def start(message: Message):

    photo = FSInputFile("assets/start.png")
    menu = get_main_menu()

    await message.answer_photo(
        photo=photo,
        caption=(
            "GoSurf — real-time ocean data analysis to pick the best surf spot right now\n\n"
            "*Hey surfer!*"
        ),
        parse_mode="Markdown",
        reply_markup=menu
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Beginner",
                    callback_data="level_beginner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Intermediate",
                    callback_data="level_intermediate"
                )
            ]
        ]
    )

    await message.answer(
        "What’s your level?",
        reply_markup=keyboard
    )


# ----------------------
# MENU HANDLERS
# ----------------------

@dp.message(F.text == "Restart bot")
async def restart(message: Message):
    await start(message)


@dp.message(F.text == "Change level")
async def change_level(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Beginner",
                    callback_data="level_beginner"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Intermediate",
                    callback_data="level_intermediate"
                )
            ]
        ]
    )

    await message.answer(
        "What’s your level?",
        reply_markup=keyboard
    )


@dp.message(F.text == "Your profile")
async def profile(message: Message):
    await message.answer("Profile coming soon")


@dp.message(F.text == "About & support")
async def about(message: Message):
    await message.answer("GoSurf Bali — surf assistant. Support: @yourusername")


# ----------------------
# LEVEL
# ----------------------

@dp.callback_query(F.data.startswith("level_"))
async def choose_level(callback: CallbackQuery):

    level = callback.data.replace("level_", "")

    await callback.answer()

    await send_forecast(
        callback.message,
        level
    )


# ----------------------
# FORECAST
# ----------------------

async def send_forecast(
        message: Message,
        level: str
):

    forecast = build_forecast()
    print("FORECAST:", forecast)

    decision = build_recommendation(
        forecast,
        level
    )

    print("DECISION:", decision)

    best = decision["best"]
    best_data = decision["conditions"]

    photo = FSInputFile("assets/best.png")

    reasons_text = "\n".join(
        [f"• {r.capitalize()}" for r in decision["reasons"]]
    )

    alternatives_text = "\n".join(
        [f"• {spot}" for spot in decision["alternatives"]]
    )

    text = (
        f"Best spot: **{best}**\n"
        f"Score: **{decision['score']}/100**\n\n"
        f"*Why:*\n\n"
        f"{reasons_text}\n\n"
        f"*Conditions:*\n\n"
        f"Wave: **{round(best_data.get('wave_height', 0), 1)} m**\n\n"
        f"Period: **{round(best_data.get('period', 0), 1)} sec**\n\n"
        f"Swell: **{best_data.get('swell_direction', '-')}**\n\n"
        f"Wind: **{best_data.get('wind_direction', '-')} {round(best_data.get('wind_speed', 0), 1)} m/s**\n\n"
        f"*Alternatives:*\n\n"
        f"{alternatives_text}"
    )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Update",
                    callback_data=f"update_{level}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Open map",
                    callback_data=f"map_{best}"
                )
            ]
        ]
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


# ----------------------
# UPDATE BUTTON
# ----------------------

@dp.callback_query(F.data.startswith("update_"))
async def update_forecast(callback: CallbackQuery):

    level = callback.data.replace("update_", "")

    await callback.answer("Updating...")

    await send_forecast(
        callback.message,
        level
    )


# ----------------------
# MAP BUTTON
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
        f"{spot}\n\n{maps.get(spot)}"
    )


# ----------------------
# RUN
# ----------------------

@app.route("/")
def home():
    return "GoSurf bot is running"


def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


async def main():
    print("🔥 Go Surf Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    asyncio.run(main())
