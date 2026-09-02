import asyncio
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import CommandStart

from weather import get_surf_data
from decision_engine import pick_best_spots
from spots import SPOTS

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()

# =========================
# MAIN MENU
# =========================
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="About"), KeyboardButton(text="Pro")],
        ],
        resize_keyboard=True,
    )

# =========================
# MAP LINKS
# =========================
MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}

def map_button(spot_name):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", url=MAPS[spot_name])]
        ]
    )

# =========================
# START
# =========================
@router.message(CommandStart())
async def start(message: Message):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")],
        ],
        resize_keyboard=True,
    )

    await message.answer(
        "GoSurf will help you find the best surf spot today 🌊",
        reply_markup=keyboard,
    )

# =========================
# LEVEL HANDLER (ФИКС!)
# =========================
@router.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def handle_level(message: Message):
    level = message.text.lower()

    await message.answer("⏳ Loading...", reply_markup=main_menu())

    spots_data = []

    for spot in SPOTS:
        data = await get_surf_data(spot)

        if not data:
            continue

        spots_data.append({
            "name": spot["name"],
            "data": data
        })

    if len(spots_data) < 2:
        await message.answer("No data available", reply_markup=main_menu())
        return

    result = pick_best_spots(spots_data, level)

    best = result["best"]
    alt = result["alternative"]

    # BEST SPOT
    await message.answer_photo(
        photo=open("assets/" + best["name"].lower() + ".jpg", "rb"),
        caption=(
            f"🏄 Best spot: {best['name']}\n"
            f"Wave: {best['data']['wave_height']} m\n"
            f"Period: {best['data']['period']} s\n"
            f"Wind: {best['data']['wind_speed']} m/s"
        ),
        reply_markup=map_button(best["name"]),
    )

    # ALTERNATIVE BUTTON (просто текст)
    await message.answer("👉 Tap 'Alternative spots'")

    # сохраняем alt в message context нельзя → просто отправляем сразу
    await send_alternatives(message, alt)

# =========================
# ALTERNATIVE (2 сообщения!)
# =========================
async def send_alternatives(message: Message, alt):
    await message.answer_photo(
        photo=open("assets/" + alt["name"].lower() + ".jpg", "rb"),
        caption=(
            f"🏄 Alternative: {alt['name']}\n"
            f"Wave: {alt['data']['wave_height']} m\n"
            f"Period: {alt['data']['period']} s\n"
            f"Wind: {alt['data']['wind_speed']} m/s"
        ),
        reply_markup=map_button(alt["name"]),
    )

# =========================
# MENU HANDLERS
# =========================
@router.message(F.text == "Restart bot")
async def restart(message: Message):
    await start(message)

@router.message(F.text == "Change level")
async def change_level(message: Message):
    await start(message)

@router.message(F.text == "About")
async def about(message: Message):
    await message.answer("GoSurf — find best surf spots on Bali 🌊", reply_markup=main_menu())

@router.message(F.text == "Pro")
async def pro(message: Message):
    await message.answer("Pro version coming soon 🚀", reply_markup=main_menu())

# =========================
# MAIN
# =========================
async def main():
    dp.include_router(router)

    # 🔥 КРИТИЧЕСКИЙ ФИКС
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())