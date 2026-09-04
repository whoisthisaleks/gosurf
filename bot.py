      import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from weather import get_spots_data
from decision_engine import pick_best

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =====================
# KEYBOARD
# =====================
level_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner")],
        [KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")],
    ],
    resize_keyboard=True
)

# =====================
# RESPONSE FORMAT
# =====================
def format_response(best, alternatives):
    text = f"🏄‍♂️ Best spot today: {best['name']}\n\n"

    text += "Conditions:\n"
    text += f"• Wave: {round(best['wave_height'], 1)}m\n"
    text += f"• Period: {round(best['period'], 1)}s\n"
    text += f"• Wind dir: {int(best['wind_dir'])}°\n\n"

    text += "Why:\n"
    text += "Clean swell + favorable wind → best quality waves today\n\n"

    if alternatives:
        text += "Alternative:\n"
        for alt in alternatives:
            text += f"• {alt['name']} ({round(alt['wave_height'], 1)}m)\n"

    text += "\nTap /start to restart"

    return text


# =====================
# HANDLERS
# =====================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🏄‍♂️ GoSurf\n\nChoose your level:",
        reply_markup=level_keyboard
    )


@dp.message()
async def handle_level(message: types.Message):
    level_map = {
        "Beginner": "beginner",
        "Intermediate": "intermediate",
        "Advanced": "advanced"
    }

    level = level_map.get(message.text)

    if not level:
        await message.answer("Please choose your level from buttons 👇")
        return

    try:
        print("USER LEVEL:", level)

        spots = get_spots_data()
        best, alternatives = pick_best(spots, level)

        print("BEST:", best["name"])

        response = format_response(best, alternatives)

        await message.answer(response)

    except Exception as e:
        logging.exception(e)
        await message.answer("⚠️ Error getting surf data. Try again later.")


# =====================
# MAIN
# =====================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())