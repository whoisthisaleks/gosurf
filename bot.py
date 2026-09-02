import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from config import TELEGRAM_TOKEN
from weather import get_spots_data
from decision_engine import pick_best_spot

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}


def level_keyboard():
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
        [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
        [InlineKeyboardButton(text="Advanced", callback_data="level_advanced")],
    ])
    return kb


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Choose your level:", reply_markup=level_keyboard())


@dp.callback_query(lambda c: c.data.startswith("level_"))
async def handle_level(callback: types.CallbackQuery):
    level = callback.data.split("_")[1]

    await callback.answer("Loading...")

    spots = get_spots_data()
    best = pick_best_spot(spots, level)

    if not best:
        await callback.message.answer("No data сейчас 😢")
        return

    text = (
        f"🏄 Best spot: {best['name']}\n"
        f"Wave: {best['wave_height']}m\n"
        f"Period: {best['period']}s\n"
        f"Wind: {best['wind_speed']} m/s"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open map", url=MAPS[best["name"]])]
    ])

    await callback.message.answer(text, reply_markup=kb)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())