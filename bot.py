import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from weather import get_spots_data
from decision_engine import pick_best_spots


# ================= CONFIG =================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

if not TELEGRAM_TOKEN:
    raise ValueError("TELEGRAM_TOKEN is missing")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()


# ================= MAPS =================

MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}


# ================= UI =================

def level_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Beginner", callback_data="level_beginner"),
            InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate"),
            InlineKeyboardButton(text="Advanced", callback_data="level_advanced"),
        ]
    ])


def map_button(spot_name: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open map", url=MAPS.get(spot_name))]
    ])


# ================= HANDLERS =================

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Select your level:",
        reply_markup=level_keyboard()
    )


@dp.callback_query()
async def handle_level(callback: types.CallbackQuery):
    try:
        level = callback.data.replace("level_", "")

        await callback.message.answer("Loading surf data...")

        spots_data = get_spots_data()

        if not spots_data:
            await callback.message.answer("No data available")
            return

        result = pick_best_spots(spots_data, level)

        if not result or not isinstance(result, list):
            await callback.message.answer("No spots found")
            return

        best = result[0]

        # 🔥 КРИТИЧЕСКАЯ ПРОВЕРКА
        if not best or not isinstance(best, dict):
            await callback.message.answer("Invalid data from engine")
            return

        name = best.get("name")
        if not name:
            await callback.message.answer("Spot data error")
            return

        text = (
            f"Best spot: {name}\n"
            f"Score: {best.get('score', '-')}\n"
            f"Wave: {best.get('wave_height', '-')}m\n"
            f"Period: {best.get('period', '-')}s\n"
            f"Wind: {best.get('wind', '-')} m/s"
        )

        await callback.message.answer(
            text,
            reply_markup=map_button(name)
        )

    except Exception as e:
        logging.exception("ERROR:")
        await callback.message.answer(f"Error: {e}")


# ================= MAIN =================

async def main():
    # 🔥 КЛЮЧЕВОЙ ФИКС КОНФЛИКТА
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())