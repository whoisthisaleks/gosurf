import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from weather import get_spots_data
from decision_engine import pick_best_spots

logging.basicConfig(level=logging.INFO)

# =========================
# TOKEN
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# =========================
# MAPS
# =========================
MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}

# =========================
# START
# =========================
@dp.message(CommandStart())
async def start(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
        [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
        [InlineKeyboardButton(text="Advanced", callback_data="level_advanced")],
    ])

    await message.answer(
        "GoSurf Bali\n\nChoose your level:",
        reply_markup=kb
    )

# =========================
# LEVEL HANDLER
# =========================
@dp.callback_query(F.data.startswith("level_"))
async def handle_level(callback: CallbackQuery):
    level = callback.data.split("_")[1]

    await callback.answer("Checking conditions...")

    try:
        spots_data = await get_spots_data()

        if not spots_data:
            await callback.message.answer("No surf data available")
            return

        best, second = pick_best_spots(spots_data, level)

        if not best:
            await callback.message.answer("No good spots today")
            return

        # =========================
        # MAIN RESULT
        # =========================
        text = f"""
{best['label']}

{best['name']}
Wave: {best['wave']} m
Period: {best['period']} s
Wind: {best['wind']} m/s

Why:
• {"\n• ".join(best["reasons"])}
"""

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Open map", url=MAPS[best["name"]])]
        ])

        # =========================
        # SECOND OPTION
        # =========================
        if second:
            text += f"""

Second option:
{second['name']} ({second['label']})
Wave: {second['wave']} m

Why:
• {"\n• ".join(second["reasons"])}
"""

        await callback.message.answer(text, reply_markup=kb)

    except Exception as e:
        logging.exception("ERROR:")
        await callback.message.answer(f"Error: {str(e)}")

# =========================
# MAIN
# =========================
async def main():
    # фикс конфликта polling
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())