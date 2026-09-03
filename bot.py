import logging
import os

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from weather import get_spots_data
from decision_engine import pick_best

logging.basicConfig(level=logging.INFO)

from dotenv import load_dotenv
import os

from config import TOKEN

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_level = {}


# ====== KEYBOARDS ======

def level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")]
        ],
        resize_keyboard=True
    )


def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="About"), KeyboardButton(text="Pro")]
        ],
        resize_keyboard=True
    )


def result_keyboard(best):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Map", url=f"https://maps.google.com/?q={best['lat']},{best['lng']}")],
        [InlineKeyboardButton(text="Update", callback_data="update")],
        [InlineKeyboardButton(text="Alternative spots", callback_data="alts")]
    ])


def alt_keyboard(spot):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open Map", url=f"https://maps.google.com/?q={spot['lat']},{spot['lng']}")]
    ])


# ====== START ======

@dp.message(Command("start"))
async def start(message: types.Message):
    photo = types.FSInputFile("assets/start.png")

    await message.answer_photo(
        photo=photo,
        caption="<b>Hey surfer</b>\nWhat's your level?",
        parse_mode="HTML",
        reply_markup=level_keyboard()
    )


# ====== LEVEL SELECT ======

@dp.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def handle_level(message: types.Message):
    level = message.text.lower()
    user_level[message.from_user.id] = level

    await send_best(message, level)


# ====== CORE FUNCTION ======

async def send_best(message, level):
    await message.answer("Loading surf data...")

    spots = get_spots_data()
    best, alternatives = pick_best(spots, level)

    photo = types.FSInputFile("assets/best.png")

    text = (
        f"<b>Best spot: {best['name']} — {best['score']}/100</b>\n\n"
        f"<b>Conditions</b>\n"
        f"Wave: {best['wave']} m\n"
        f"Wind: {best['wind']} m/s\n"
        f"Period: {best['period']} s\n"
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        parse_mode="HTML",
        reply_markup=result_keyboard(best)
    )

    await message.answer("Menu", reply_markup=main_menu())

    # сохраняем альтернативы
    user_level[f"{message.from_user.id}_alts"] = alternatives


# ====== UPDATE ======

@dp.callback_query(F.data == "update")
async def update_handler(callback: types.CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Choose level first")
        return

    await send_best(callback.message, level)


# ====== ALTERNATIVES ======

@dp.callback_query(F.data == "alts")
async def alts_handler(callback: types.CallbackQuery):
    alts = user_level.get(f"{callback.from_user.id}_alts")

    if not alts:
        await callback.message.answer("No alternatives")
        return

    photo = types.FSInputFile("assets/alt.png")

    await callback.message.answer_photo(photo=photo)

    for spot in alts:
        text = (
            f"<b>{spot['name']}</b>\n\n"
            f"<b>Conditions</b>\n"
            f"Wave: {spot['wave']} m\n"
            f"Wind: {spot['wind']} m/s\n"
            f"Period: {spot['period']} s\n"
        )

        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=alt_keyboard(spot)
        )


# ====== MENU ======

@dp.message(F.text == "Restart bot")
async def restart(message: types.Message):
    await start(message)


@dp.message(F.text == "Change level")
async def change_level(message: types.Message):
    await message.answer("Choose level:", reply_markup=level_keyboard())


@dp.message(F.text == "About")
async def about(message: types.Message):
    await message.answer("About section in progress")


@dp.message(F.text == "Pro")
async def pro(message: types.Message):
    await message.answer("Pro version coming soon")


# ====== MAIN ======

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())