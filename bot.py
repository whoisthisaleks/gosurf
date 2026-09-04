import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile

from weather import get_spots_data
from decision_engine import pick_best

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("BOT_TOKEN is not set")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# =====================
# STATE (простое хранение уровня)
# =====================
user_levels = {}

# =====================
# KEYBOARDS
# =====================

level_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner")],
        [KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")],
    ],
    resize_keyboard=True
)

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔄 Update forecast")],
        [KeyboardButton(text="🔁 Change level")],
    ],
    resize_keyboard=True
)

# =====================
# FORMAT
# =====================

def format_response(best, alternatives):
    text = f"🏄‍♂️ Best spot today: {best['name']}\n\n"

    text += "Conditions:\n"
    text += f"• Wave: {round(best['wave_height'], 1)}m\n"
    text += f"• Period: {round(best['period'], 1)}s\n"
    text += f"• Wind dir: {int(best['wind_dir'])}°\n\n"

    text += "Why:\n"
    text += "Clean swell + favorable wind → best quality waves today\n"

    return text


def format_alternative(spot):
    return f"🌊 {spot['name']} — {round(spot['wave_height'],1)}m, {round(spot['period'],1)}s"


# =====================
# CORE LOGIC
# =====================

async def send_forecast(message: types.Message, level: str):
    try:
        print("LEVEL:", level)

        spots = get_spots_data()
        best, alternatives = pick_best(spots, level)

        # --- BEST SPOT ---
        text = format_response(best, alternatives)
        await message.answer(text, reply_markup=main_keyboard)

        # --- ALTERNATIVES ---
        if alternatives:
            photo = FSInputFile("assets/alt.png")

            # картинка ТОЛЬКО перед первым
            await message.answer_photo(
                photo=photo,
                caption="Alternative spots:"
            )

            for alt in alternatives:
                await message.answer(format_alternative(alt))

    except Exception as e:
        logging.exception(e)
        await message.answer("⚠️ Error getting surf data. Try again later.")


# =====================
# HANDLERS
# =====================

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "🏄‍♂️ GoSurf\n\nChoose your level:",
        reply_markup=level_keyboard
    )


@dp.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def set_level(message: types.Message):
    level_map = {
        "Beginner": "beginner",
        "Intermediate": "intermediate",
        "Advanced": "advanced"
    }

    level = level_map[message.text]
    user_levels[message.from_user.id] = level

    await send_forecast(message, level)


@dp.message(F.text == "🔄 Update forecast")
async def update_handler(message: types.Message):
    level = user_levels.get(message.from_user.id)

    if not level:
        await message.answer("Choose level first 👇", reply_markup=level_keyboard)
        return

    await send_forecast(message, level)


@dp.message(F.text == "🔁 Change level")
async def change_level(message: types.Message):
    await message.answer(
        "Choose your level again 👇",
        reply_markup=level_keyboard
    )


# =====================
# MAIN
# =====================

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())