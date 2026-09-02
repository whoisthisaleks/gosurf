import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from config import TELEGRAM_TOKEN
from spots import SPOTS
from weather import get_spots_data
from decision_engine import pick_best_spots

logging.basicConfig(level=logging.INFO)

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- MAP LINKS ---
MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}


# --- KEYBOARDS ---

def level_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏄 Beginner", callback_data="level_beginner")],
        [InlineKeyboardButton(text="🏄‍♂️ Intermediate", callback_data="level_intermediate")],
        [InlineKeyboardButton(text="🏄‍🔥 Advanced", callback_data="level_advanced")],
    ])


def result_keyboard(spot_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📍 Open map", url=MAPS.get(spot_name, ""))],
        [InlineKeyboardButton(text="🔄 Update", callback_data="update")],
    ])


# --- HANDLERS ---

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🌊 GoSurf\n\nSelect your level:",
        reply_markup=level_keyboard()
    )


@dp.callback_query(F.data.startswith("level_"))
async def handle_level(callback: CallbackQuery):
    level = callback.data.split("_")[1]

    await callback.message.answer("⏳ Checking conditions...")

    # 👉 получаем данные по всем спотам
    spots_data = get_spots_data(SPOTS)

    if not spots_data:
        await callback.message.answer("⚠️ Failed to get surf data. Try again later.")
        return

    # 👉 выбираем лучший спот
    best = pick_best_spots(spots_data, level)

    if not best:
        await callback.message.answer("😕 No good spots found today.")
        return

    top_spot = best[0]

    spot_name = top_spot["spot"]["name"]
    cond = top_spot["conditions"]

    text = (
        f"🏆 Best spot: {spot_name}\n\n"
        f"🌊 Wave: {cond['wave_height']} m\n"
        f"⏱ Period: {cond['wave_period']} s\n"
        f"💨 Wind: {cond['wind_speed']} m/s\n"
    )

    await callback.message.answer(
        text,
        reply_markup=result_keyboard(spot_name)
    )


@dp.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    await callback.message.answer("🔄 Updating...")
    await start(callback.message)


# --- MAIN ---

async def main():
    # 🔥 фикс конфликта
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())