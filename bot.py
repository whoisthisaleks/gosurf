import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from spots import SPOTS
from weather import get_surf_data
from decision_engine import pick_best_spots

logging.basicConfig(level=logging.INFO)

router = Router()

# ===== MAP LINKS =====
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")],
        ],
        resize_keyboard=True,
    )


# ===== START =====
@router.message(F.text == "/start")
async def start_handler(message: Message):
    photo = FSInputFile("assets/start.png")

    await message.answer_photo(
        photo=photo,
        caption=(
            "<b>Hey surfer!</b>\n\n"
            "Let's pick the best surf spot right now.\n"
            "What's your level?"
        ),
        reply_markup=level_keyboard(),
    )


# ===== LEVEL SELECT =====
@router.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def level_handler(message: Message):
    level = message.text.lower()

    await message.answer("Loading...", reply_markup=main_menu())

    spots_with_data = []

    for spot in SPOTS:
        data = await get_surf_data(spot)

        if not data:
            continue

        spots_with_data.append({
            "spot": spot,
            "data": data
        })

    if not spots_with_data:
        await message.answer("No data available", reply_markup=main_menu())
        return

    result = pick_best_spots(spots_with_data, level)

    best = result["best"]
    alt = result["alternative"]

    best_spot = best["spot"]
    best_data = best["data"]

    photo = FSInputFile("assets/best.png")

    text = (
        f"<b>Best spot:</b>\n"
        f"<b>{best_spot['name']}</b>\n\n"

        f"<b>Why:</b>\n"
        f"Good wave size & good for your level\n\n"

        f"<b>Conditions:</b>\n"
        f"Wave: {best_data['wave_height']} m\n"
        f"Period: {best_data['period']} s\n"
        f"Wind: {best_data['wind_speed']} m/s\n\n"

        f"<b>Alternative spots:</b>\n"
        f"{alt['spot']['name']}"
    )

    inline = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Open map",
                    url=MAPS[best_spot["name"]]
                )
            ],
            [InlineKeyboardButton(text="Update", callback_data="update")],
            [InlineKeyboardButton(text="Alternative spots", callback_data="alt")],
        ]
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=inline,
    )


# ===== UPDATE =====
@router.callback_query(F.data == "update")
async def update_handler(callback):
    await callback.answer()
    await callback.message.answer("Updating...")
    await level_handler(callback.message)


# ===== ALTERNATIVE FLOW =====
@router.callback_query(F.data == "alt")
async def alt_handler(callback):
    await callback.answer()

    level = "intermediate"  # позже можно хранить user state

    spots_with_data = []

    for spot in SPOTS:
        data = await get_surf_data(spot)
        if not data:
            continue

        spots_with_data.append({
            "spot": spot,
            "data": data
        })

    if len(spots_with_data) < 2:
        await callback.message.answer("No alternatives available")
        return

    result = pick_best_spots(spots_with_data, level)

    best = result["best"]
    alt = result["alternative"]

    alternatives = [alt]

    photo = FSInputFile("assets/alt.png")

    for item in alternatives:
        spot = item["spot"]
        data = item["data"]

        text = (
            f"<b>{spot['name']}</b>\n\n"
            f"<b>Conditions:</b>\n"
            f"Wave: {data['wave_height']} m\n"
            f"Period: {data['period']} s\n"
            f"Wind: {data['wind_speed']} m/s"
        )

        inline = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Open map",
                        url=MAPS[spot["name"]]
                    )
                ]
            ]
        )

        await callback.message.answer_photo(
            photo=photo,
            caption=text,
            reply_markup=inline,
        )


# ===== MENU BUTTONS =====
@router.message(F.text == "Restart bot")
async def restart_handler(message: Message):
    await start_handler(message)


@router.message(F.text == "Change level")
async def change_level_handler(message: Message):
    await message.answer("Choose level:", reply_markup=level_keyboard())


@router.message(F.text == "About")
async def about_handler(message: Message):
    await message.answer("GoSurf — surf spot recommendation bot 🌊", reply_markup=main_menu())


@router.message(F.text == "Pro")
async def pro_handler(message: Message):
    await message.answer("Pro version coming soon", reply_markup=main_menu())


# ===== MAIN =====
async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())