import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN
from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from spots import SPOTS

from scheduler import start_scheduler, register_user


bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()


# ======================
# KEYBOARDS
# ======================

def level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Beginner"),
                KeyboardButton(text="Intermediate"),
                KeyboardButton(text="Advanced")
            ]
        ],
        resize_keyboard=True
    )


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Update"),
                KeyboardButton(text="Change level")
            ],
            [
                KeyboardButton(text="All spots"),
                KeyboardButton(text="Restart")
            ]
        ],
        resize_keyboard=True
    )


# ======================
# FORMATTERS
# ======================

def format_best(best, alternatives):
    text = f"<b>Best spot: {best['spot']}</b>\n"
    text += f"{best.get('confidence', '')}\n\n"

    if best.get("bad_day"):
        text += "❌ No good surf today. Better to skip.\n\n"

    text += f"Why: {best.get('reason', 'good conditions')}\n\n"

    text += f"Wave: {best['wave']}m\n"
    text += f"Period: {best['period']}s\n"
    text += f"Wind: {best['wind']}\n"

    if best.get("swell_dir"):
        text += f"Swell: {int(best['swell_dir'])}°\n"

    if best.get("tide"):
        text += f"Tide: {best['tide']}\n"

    text += "\n<b>Alternatives:</b>\n\n"

    for alt in alternatives:
        text += f"{alt['spot']}\n"

    return text


def format_alternatives(alternatives):
    text = "<b>Alternatives:</b>\n\n"

    for spot in alternatives:
        text += f"<b>{spot['spot']}</b>\n"
        text += f"Wave: {spot['wave']}m\n"
        text += f"Period: {spot['period']}s\n"
        text += f"Wind: {spot['wind']}\n"

        if spot.get("swell_dir"):
            text += f"Swell: {int(spot['swell_dir'])}°\n"

        if spot.get("tide"):
            text += f"Tide: {spot['tide']}\n"

        text += "\n"

    return text


def format_all_spots(data):
    text = ""

    for spot in data:
        text += f"<b>{spot['spot']}</b>\n"
        text += f"Wave: {spot['wave']}m\n"
        text += f"Period: {spot['period']}s\n"
        text += f"Wind: {spot['wind']}\n"

        if spot.get("swell_dir"):
            text += f"Swell: {int(spot['swell_dir'])}°\n"

        if spot.get("tide"):
            text += f"Tide: {spot['tide']}\n"

        text += "\n"

    return text


# ======================
# STATE
# ======================

user_level = {}


# ======================
# HANDLERS
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    await message.answer_photo(
        FSInputFile("assets/start.png"),
        caption=(
            "<b>Hey surfer!</b>\n\n"
            "Find the best surf spot based on current conditions\n\n"
            "Choose your level:"
        ),
        reply_markup=level_keyboard()
    )


@dp.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def handle_level(message: Message):
    level = message.text
    user_level[message.chat.id] = level
    register_user(message.chat.id, level)

    await message.answer("Updating forecast...")

    data = [fetch_spot_weather(s) for s in SPOTS]
    best, alternatives = pick_best_spots(data, level)

    # BEST
    await message.answer_photo(
        FSInputFile("assets/best.png"),
        caption=format_best(best, alternatives),
        reply_markup=main_keyboard()
    )

    # ALTERNATIVES (детали)
    await message.answer_photo(
        FSInputFile("assets/alt.png"),
        caption=format_alternatives(alternatives)
    )


@dp.message(F.text == "Update")
async def update(message: Message):
    level = user_level.get(message.chat.id, "Intermediate")

    await message.answer("Updating forecast...")

    data = [fetch_spot_weather(s) for s in SPOTS]
    best, alternatives = pick_best_spots(data, level)

    await message.answer_photo(
        FSInputFile("assets/best.png"),
        caption=format_best(best, alternatives)
    )

    await message.answer_photo(
        FSInputFile("assets/alt.png"),
        caption=format_alternatives(alternatives)
    )


@dp.message(F.text == "Change level")
async def change_level(message: Message):
    await message.answer(
        "Choose your level:",
        reply_markup=level_keyboard()
    )


@dp.message(F.text == "Restart")
async def restart(message: Message):
    user_level.pop(message.chat.id, None)
    await start(message)


@dp.message(F.text == "All spots")
async def all_spots(message: Message):
    data = [fetch_spot_weather(s) for s in SPOTS]

    await message.answer_photo(
        FSInputFile("assets/all.png"),
        caption=format_all_spots(data)
    )


# ======================
# MAIN
# ======================

async def main():
    print("Bot started")

    await bot.delete_webhook(drop_pending_updates=True)

    start_scheduler(bot)

    await dp.start_polling(bot)

    print("STARTING SCHEDULER...")
    start_scheduler(bot)


if __name__ == "__main__":
    asyncio.run(main())