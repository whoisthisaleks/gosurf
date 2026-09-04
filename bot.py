import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN
from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from spots import SPOTS


bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()


# ======================
# UI TEXT BUILDERS
# ======================

def build_start_text():
    return (
        "<b>Hey surfer!</b>\n\n"
        "Find the best surf spot based on current conditions\n\n"
        "Choose your level:"
    )


def build_best_text(best, alternatives):
    text = f"<b>Best spot: {best['spot']}</b>\n\n"
    text += (
        f"Wave: {best['wave']}m\n"
        f"Period: {best['period']}s\n"
        f"Wind: {best['wind']}\n\n"
    )

    if alternatives:
        text += "<b>Alternatives:</b>\n\n"
        for alt in alternatives:
            text += f"{alt['spot']}\n"

    return text


def build_alternatives_text(alternatives):
    text = "<b>Alternatives:</b>\n\n"

    for alt in alternatives:
        text += (
            f"<b>{alt['spot']}</b>\n"
            f"Wave: {alt['wave']}m\n"
            f"Period: {alt['period']}s\n"
            f"Wind: {alt['wind']}\n\n"
        )

    return text


# ======================
# KEYBOARDS
# ======================

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Update forecast")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="Restart")],
        ],
        resize_keyboard=True
    )


def get_level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")],
        ],
        resize_keyboard=True
    )


# ======================
# STATE
# ======================

user_level = {}


# ======================
# HANDLERS
# ======================

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer_photo(
        photo=FSInputFile("assets/start.png"),
        caption=build_start_text(),
        reply_markup=get_level_keyboard()
    )


@dp.message()
async def handle(message: types.Message):
    text = (message.text or "").strip().lower()
    user_id = message.from_user.id

    # LEVEL SELECT
    if text in ["beginner", "intermediate", "advanced"]:
        user_level[user_id] = text

        await message.answer("Updating forecast...")

        weather_data = [fetch_spot_weather(s) for s in SPOTS]
        best, alternatives = pick_best_spots(weather_data, text)

        # BEST MESSAGE
        await message.answer_photo(
            photo=FSInputFile("assets/best.png"),
            caption=build_best_text(best, alternatives),
            reply_markup=get_main_keyboard()
        )

        # DETAILED ALTERNATIVES
        if alternatives:
            await message.answer_photo(
                photo=FSInputFile("assets/alt.png"),
                caption=build_alternatives_text(alternatives),
                reply_markup=get_main_keyboard()
            )

        return

    # UPDATE
    if text == "update forecast":
        level = user_level.get(user_id, "intermediate")

        await message.answer("Updating forecast...")

        weather_data = [fetch_spot_weather(s) for s in SPOTS]
        best, alternatives = pick_best_spots(weather_data, level)

        await message.answer_photo(
            photo=FSInputFile("assets/best.png"),
            caption=build_best_text(best, alternatives),
            reply_markup=get_main_keyboard()
        )

        if alternatives:
            await message.answer_photo(
                photo=FSInputFile("assets/alt.png"),
                caption=build_alternatives_text(alternatives),
                reply_markup=get_main_keyboard()
            )

        return

    # CHANGE LEVEL
    if text == "change level":
        await start(message)
        return

    # RESTART
    if text == "restart":
        user_level.pop(user_id, None)
        await start(message)
        return

    await message.answer("Use buttons", reply_markup=get_main_keyboard())


# ======================
# RUN
# ======================

async def main():
    print("Bot started")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())