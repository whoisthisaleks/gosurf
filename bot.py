import asyncio
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.types import (
    Message,
    FSInputFile,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.client.default import DefaultBotProperties

from weather import get_surf_data
from decision_engine import pick_best_spots
from spots import SPOTS

BOT_TOKEN = os.getenv("BOT_TOKEN")

router = Router()
dp = Dispatcher()
dp.include_router(router)

# ===== MAPS =====
MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}

# ===== MAIN MENU =====
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="About"), KeyboardButton(text="Pro")],
        ],
        resize_keyboard=True,
    )

# ===== LEVEL BUTTONS =====
def level_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Beginner", callback_data="level_beginner")],
            [InlineKeyboardButton(text="Intermediate", callback_data="level_intermediate")],
            [InlineKeyboardButton(text="Advanced", callback_data="level_advanced")],
        ]
    )

# ===== RESULT BUTTONS =====
def result_keyboard(spot_name: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Open map", url=MAPS.get(spot_name, ""))],
            [InlineKeyboardButton(text="Update", callback_data="update")],
            [InlineKeyboardButton(text="Alternative spots", callback_data="alt")],
        ]
    )

# ===== FORMAT TEXT =====
def format_spot_text(title: str, data: dict, level: str = ""):
    if not data:
        return "No data available"

    return f"""
<b>{title}</b>

<b>Why:</b> Good wave size & good for your level

<b>Conditions:</b>
Wave: {data.get('wave_height')} m
Period: {data.get('period')} s
Wind: {data.get('wind_speed')} m/s
"""

# ===== START =====
@router.message(F.text == "/start")
@router.message(F.text == "Restart bot")
async def start_handler(message: Message):
    photo = FSInputFile("assets/start.png")

    await message.answer_photo(
        photo=photo,
        caption="Hey surfer!\n\nLet's pick the best surf spot right now.\nWhat's your level?",
        reply_markup=level_keyboard(),
    )

# ===== CHANGE LEVEL =====
@router.message(F.text == "Change level")
async def change_level(message: Message):
    await message.answer("Choose your level:", reply_markup=level_keyboard())

# ===== LEVEL SELECT =====
@router.callback_query(F.data.startswith("level_"))
async def level_selected(callback):
    level = callback.data.split("_")[1]

    await callback.message.answer("Loading...", reply_markup=main_menu())

    spots_with_data = []

    for spot in SPOTS:
        data = await get_surf_data(spot)
        spots_with_data.append({
            "name": spot["name"],
            "data": data
        })

    result = pick_best_spots(spots_with_data, level)

    best = result["best"]
    alt = result["alternative"]

    best_photo = FSInputFile("assets/best.png")

    # BEST SPOT
    await callback.message.answer_photo(
        photo=best_photo,
        caption=format_spot_text(f"Best spot: {best['name']}", best["data"], level),
        reply_markup=result_keyboard(best["name"]),
    )

# ===== UPDATE =====
@router.callback_query(F.data == "update")
async def update_handler(callback):
    await callback.message.answer("Updating...")
    await start_handler(callback.message)

# ===== ALT FLOW =====
@router.callback_query(F.data == "alt")
async def alt_handler(callback):
    alt_photo = FSInputFile("assets/alt.png")

    # Получаем снова данные
    spots_with_data = []
    for spot in SPOTS:
        data = await get_surf_data(spot)
        spots_with_data.append({
            "name": spot["name"],
            "data": data
        })

    result = pick_best_spots(spots_with_data, "intermediate")

    alt1 = result["alternative"]
    alt2 = result["best"]  # просто второй

    # ❗ ВАЖНО: 2 отдельных сообщения
    await callback.message.answer_photo(
        photo=alt_photo,
        caption=format_spot_text(alt1["name"], alt1["data"]),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Open map", url=MAPS[alt1["name"]])]
            ]
        ),
    )

    await callback.message.answer_photo(
        photo=alt_photo,
        caption=format_spot_text(alt2["name"], alt2["data"]),
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Open map", url=MAPS[alt2["name"]])]
            ]
        ),
    )

# ===== ABOUT =====
@router.message(F.text == "About")
async def about_handler(message: Message):
    await message.answer(
        "GoSurf helps you find the best surf spot using real-time ocean data 🌊",
        reply_markup=main_menu(),
    )

# ===== PRO =====
@router.message(F.text == "Pro")
async def pro_handler(message: Message):
    await message.answer(
        "Pro version coming soon 🚀",
        reply_markup=main_menu(),
    )

# ===== MAIN =====
async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    # 🔥 FIX CONFLICT
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())