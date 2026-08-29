import os
import logging
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from weather import build_forecast
from decision_engine import get_best_spot

# -------------------------
# CONFIG
# -------------------------
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # https://gosurf-bot.onrender.com

if not BOT_TOKEN or not WEBHOOK_URL:
    raise ValueError("BOT_TOKEN or WEBHOOK_URL not set")

WEBHOOK_PATH = "/webhook"
FULL_WEBHOOK_URL = WEBHOOK_URL + WEBHOOK_PATH

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

# -------------------------
# KEYBOARDS
# -------------------------
def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def actions_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Update", callback_data="update")
    kb.button(text="Alternative spots", callback_data="alts")
    kb.button(text="About", callback_data="about")
    kb.adjust(1)
    return kb.as_markup()

# -------------------------
# HANDLERS
# -------------------------
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Hey surfer!\n\nLooking for waves?\nWe use real-time ocean data to find your best spot today.",
        reply_markup=level_keyboard()
    )


@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    try:
        data = callback.data

        # ---------------- LEVEL ----------------
        if data.startswith("level_"):
            level = data.split("_")[1]

            forecast = build_forecast()
            best, alternatives = get_best_spot(forecast, level)

            text = (
                f"**Best spot:** {best.get('spot', 'Unknown')}\n"
                f"**Score:** {best.get('score', 0)}/100\n\n"
                f"**Conditions:**\n"
                f"Wave: {best.get('wave_height', '?')} m\n"
                f"Period: {best.get('period', '?')} sec\n"
                f"Swell: {best.get('swell_direction', '?')}\n"
                f"Wind: {best.get('wind_direction', '?')} {best.get('wind_speed', '?')} m/s\n"
                f"Tide: {best.get('tide', 'unknown')}"
            )

            await callback.message.answer(text, reply_markup=actions_keyboard())

        # ---------------- UPDATE ----------------
        elif data == "update":
            forecast = build_forecast()
            best, _ = get_best_spot(forecast, "intermediate")

            text = (
                f"Updated:\n"
                f"{best.get('spot', '?')} — {best.get('wave_height', '?')}m"
            )
            await callback.message.answer(text)

        # ---------------- ALTERNATIVES ----------------
        elif data == "alts":
            forecast = build_forecast()
            _, alternatives = get_best_spot(forecast, "intermediate")

            if not alternatives:
                await callback.message.answer("No alternatives found")
            else:
                text = "Alternative spots:\n"
                for s in alternatives:
                    text += f"{s}\n"

                await callback.message.answer(text)

        # ---------------- ABOUT ----------------
        elif data == "about":
            await callback.message.answer(
                "GoSurf helps you quickly find the best surf spot in Bali.\n\n"
                "We check waves, wind, and conditions for you — and give a simple recommendation so you can spend less time figuring it out and more time in the water."
            )

        await callback.answer()

    except Exception as e:
        logging.exception("Callback error")
        await callback.message.answer("Something went wrong 😕")
        await callback.answer()

# -------------------------
# WEBHOOK
# -------------------------
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    try:
        json_data = request.get_json()
        update = Update.model_validate(json_data)

        asyncio.run(dp.feed_update(bot, update))

    except Exception as e:
        logging.exception("Webhook error")
        return "error", 500

    return "ok", 200


@app.route("/")
def index():
    return "OK"

# -------------------------
# START
# -------------------------
if __name__ == "__main__":
    import requests

    # ставим webhook
    requests.get(
        f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={FULL_WEBHOOK_URL}"
    )

    print("Webhook set:", FULL_WEBHOOK_URL)

    app.run(host="0.0.0.0", port=10000)