import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile
)
from aiogram.filters import CommandStart

from weather import get_spots_data
from decision_engine import pick_best

TOKEN = os.getenv("TELEGRAM_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


# --- MAIN MENU ---
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Restart bot")],
        [KeyboardButton(text="Change level")],
        [KeyboardButton(text="About")],
        [KeyboardButton(text="Pro")]
    ],
    resize_keyboard=True
)


# --- LEVEL BUTTONS ---
levels = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Beginner")],
        [KeyboardButton(text="Intermediate")],
        [KeyboardButton(text="Advanced")]
    ],
    resize_keyboard=True
)


# --- START ---
@dp.message(CommandStart())
async def start(message: types.Message):
    photo = FSInputFile("assets/start.png")

    await message.answer_photo(photo)

    await message.answer(
        "<b>Hey surfer</b>\n\nWhat's your level?",
        parse_mode="HTML",
        reply_markup=levels
    )


# --- LEVEL ---
@dp.message(lambda m: m.text in ["Beginner", "Intermediate", "Advanced"])
async def handle_level(message: types.Message):
    level = message.text

    await message.answer("Loading surf data...")

    spots = get_spots_data()

    result = pick_best(spots, level)

    best = result["best"]
    alt = result["alternatives"]

    # --- IMAGE ---
    await message.answer_photo(FSInputFile("assets/best.png"))

    # --- TEXT ---
    text = (
        f"<b>Best spot: {best['spot']} ({best['score']}/100)</b>\n\n"
        f"<b>Conditions</b>\n"
        f"Wave: {best['wave']} m\n"
        f"Wind: {best['wind']} m/s\n"
        f"Period: {best['period']} s\n\n"
        f"<b>Alternatives</b>\n"
        f"{alt[0]['spot']}\n{alt[1]['spot']}"
    )

    # --- INLINE BUTTONS ---
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="Open map",
            url=f"https://maps.google.com/?q={best['lat']},{best['lng']}"
        )],
        [InlineKeyboardButton(text="Update", callback_data="update")],
        [InlineKeyboardButton(text="Alternative spots", callback_data="alts")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# --- CALLBACK: UPDATE ---
@dp.callback_query(lambda c: c.data == "update")
async def update(call: types.CallbackQuery):
    await handle_level(call.message)


# --- CALLBACK: ALTERNATIVES ---
@dp.callback_query(lambda c: c.data == "alts")
async def show_alts(call: types.CallbackQuery):
    spots = get_spots_data()
    result = pick_best(spots, "Intermediate")

    for spot in result["alternatives"]:
        await call.message.answer_photo(FSInputFile("assets/alt.png"))

        text = (
            f"<b>{spot['spot']}</b>\n\n"
            f"<b>Conditions</b>\n"
            f"Wave: {spot['wave']} m\n"
            f"Wind: {spot['wind']} m/s\n"
            f"Period: {spot['period']} s"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="Open map",
                url=f"https://maps.google.com/?q={spot['lat']},{spot['lng']}"
            )]
        ])

        await call.message.answer(text, parse_mode="HTML", reply_markup=keyboard)


# --- MAIN ---
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())