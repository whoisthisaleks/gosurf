import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from weather import get_surf_data
from decision_engine import pick_best_spots
from spots import SPOTS
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

router = Router()

# MAP LINKS
MAPS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78",
}


# MAIN MENU
def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="About"), KeyboardButton(text="Pro")]
        ],
        resize_keyboard=True
    )


# LEVEL BUTTONS
def level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")]
        ],
        resize_keyboard=True
    )


# INLINE BUTTONS (RESULT)
def result_buttons(spot_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open map", url=MAPS[spot_name])],
        [InlineKeyboardButton(text="Update", callback_data="update")],
        [InlineKeyboardButton(text="Alternative spots", callback_data="alt")]
    ])


def alt_button(spot_name):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open map", url=MAPS[spot_name])]
    ])


# START
@router.message(CommandStart())
async def start_handler(message: Message):
    photo = FSInputFile("assets/start.png")

    await message.answer_photo(
        photo,
        caption=(
            "Hey surfer!\n\n"
            "Let's pick the best surf spot right now.\n"
            "What's your level?"
        ),
        reply_markup=level_keyboard()
    )


# LEVEL HANDLER (🔥 ТУТ БЫЛА ПРОБЛЕМА)
@router.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def level_handler(message: Message):
    level = message.text.lower()

    await message.answer("Loading...")

    try:
        spots_with_data = []

        for spot in SPOTS:
            data = await get_surf_data(spot)
            spots_with_data.append({
                "spot": spot,
                "data": data
            })

        result = pick_best_spots(spots_with_data, level)

        best = result["best"]
        alt = result["alternative"]

        best_name = best["spot"]["name"]
        d = best["data"]

        text = (
            f"**Best spot:**\n"
            f"**{best_name}**\n\n"
            f"**Conditions:**\n"
            f"Wave: {d['wave_height']} m\n"
            f"Period: {d['period']} s\n"
            f"Wind: {d['wind_speed']} m/s\n\n"
            f"**Alternative spots:**\n"
            f"{alt['spot']['name']}"
        )

        photo = FSInputFile("assets/best.png")

        await message.answer_photo(
            photo,
            caption=text,
            parse_mode="Markdown",
            reply_markup=result_buttons(best_name)
        )

    except Exception as e:
        print("ERROR:", e)
        await message.answer("No data available", reply_markup=main_menu())


# ALTERNATIVE FLOW (🔥 строго 2 сообщения)
@router.callback_query(F.data == "alt")
async def alt_handler(callback):
    await callback.answer()

    try:
        spots_with_data = []

        for spot in SPOTS:
            data = await get_surf_data(spot)
            spots_with_data.append({
                "spot": spot,
                "data": data
            })

        result = pick_best_spots(spots_with_data, "intermediate")

        alt1 = result["alternative"]
        alt2 = result["best"]

        photo = FSInputFile("assets/alt.png")

        # 1 сообщение
        d1 = alt1["data"]
        await callback.message.answer_photo(
            photo,
            caption=(
                f"**{alt1['spot']['name']}**\n\n"
                f"**Conditions:**\n"
                f"Wave: {d1['wave_height']} m\n"
                f"Period: {d1['period']} s\n"
                f"Wind: {d1['wind_speed']} m/s"
            ),
            parse_mode="Markdown",
            reply_markup=alt_button(alt1["spot"]["name"])
        )

        # 2 сообщение
        d2 = alt2["data"]
        await callback.message.answer_photo(
            photo,
            caption=(
                f"**{alt2['spot']['name']}**\n\n"
                f"**Conditions:**\n"
                f"Wave: {d2['wave_height']} m\n"
                f"Period: {d2['period']} s\n"
                f"Wind: {d2['wind_speed']} m/s"
            ),
            parse_mode="Markdown",
            reply_markup=alt_button(alt2["spot"]["name"])
        )

    except Exception as e:
        print("ALT ERROR:", e)


# MAIN MENU HANDLERS
@router.message(F.text == "Restart bot")
async def restart_handler(message: Message):
    await start_handler(message)


@router.message(F.text == "Change level")
async def change_level_handler(message: Message):
    await message.answer("Choose your level:", reply_markup=level_keyboard())


@router.message(F.text == "About")
async def about_handler(message: Message):
    await message.answer("GoSurf — finds best surf spot 🌊", reply_markup=main_menu())


@router.message(F.text == "Pro")
async def pro_handler(message: Message):
    await message.answer("Pro coming soon 🚀", reply_markup=main_menu())


# MAIN
async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )

    # 🔥 CRITICAL FIX
    await bot.delete_webhook(drop_pending_updates=True)

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())