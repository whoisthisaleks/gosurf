import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from decision_engine import get_best_spot, get_alternative_spots

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
router = Router()

user_data = {}


# =========================
# KEYBOARDS
# =========================

def level_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def main_kb(lat, lng):
    kb = InlineKeyboardBuilder()
    kb.button(text="Open map", url=f"https://www.google.com/maps?q={lat},{lng}")
    kb.button(text="Update", callback_data="update")
    kb.button(text="Alternative spots", callback_data="alts")
    kb.adjust(1)
    return kb.as_markup()


def bottom_menu():
    kb = ReplyKeyboardBuilder()
    kb.button(text="Restart bot")
    kb.button(text="Change level")
    kb.button(text="About")
    kb.button(text="GoSurf Pro")
    kb.adjust(2)
    return kb.as_markup(resize_keyboard=True)


# =========================
# START
# =========================

@router.message(Command("start"))
async def start(message: Message):
    photo = FSInputFile("assets/start.png")

    text = (
        "<b>Hey surfer!</b>\n\n"
        "We use real-time ocean data analysis to pick the best surf spot right now.\n\n"
        "What's your level?"
    )

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=level_kb()
    )

    await message.answer(
        " ",
        reply_markup=bottom_menu()
    )


# =========================
# LEVEL SELECT
# =========================

@router.callback_query(F.data.startswith("level_"))
async def level_handler(callback: CallbackQuery):
    user_id = callback.from_user.id
    level = callback.data.split("_")[1]

    user_data[user_id] = {"level": level}

    await callback.answer()
    await send_best(callback.message, user_id)


# =========================
# SEND BEST SPOT
# =========================

async def send_best(message: Message, user_id: int):
    level = user_data[user_id]["level"]

    result = await get_best_spot(level)

    user_data[user_id]["last"] = result

    reasons_text = "\n".join([f"- {r}" for r in result["reasons"]])

    text = (
        f"<b>Best spot: {result['spot']}</b>\n\n"
        f"Score: {result['score']}/100\n\n"
        f"{reasons_text}\n\n"
        f"<b>Conditions:</b>\n\n"
        f"Wave: {result['wave']} m\n"
        f"Period: {result['period']} sec\n"
        f"Swell: {result['swell']}\n"
        f"Wind: {result['wind_text']}\n"
        f"Tide: not available\n\n"
        f"<b>Alternative spots:</b>\n"
        f"- {result['alts'][0]}\n"
        f"- {result['alts'][1]}"
    )

    photo = FSInputFile("assets/best.png")

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=main_kb(result["lat"], result["lng"])
    )


# =========================
# UPDATE
# =========================

@router.callback_query(F.data == "update")
async def update(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.message.answer("Use /start first")
        return

    await callback.answer()
    await send_best(callback.message, user_id)


# =========================
# ALTERNATIVE SPOTS
# =========================

@router.callback_query(F.data == "alts")
async def alternatives(callback: CallbackQuery):
    user_id = callback.from_user.id

    if user_id not in user_data:
        await callback.message.answer("Use /start first")
        return

    level = user_data[user_id]["level"]

    spots = await get_alternative_spots(level)

    for s in spots:
        text = (
            f"<b>{s['spot']}</b>\n\n"
            f"Score: {s['score']}/100\n\n"
            f"<b>Conditions:</b>\n\n"
            f"Wave: {s['wave']} m\n"
            f"Period: {s['period']} sec\n"
            f"Swell: {s['swell']}\n"
            f"Wind: {s['wind_text']}\n"
            f"Tide: not available"
        )

        kb = InlineKeyboardBuilder()
        kb.button(
            text="Open map",
            url=f"https://www.google.com/maps?q={s['lat']},{s['lng']}"
        )

        await callback.message.answer_photo(
            photo=FSInputFile("assets/alt.png"),
            caption=text,
            reply_markup=kb.as_markup()
        )

    await callback.answer()


# =========================
# BOTTOM MENU
# =========================

@router.message(F.text == "Restart bot")
async def restart(message: Message):
    await start(message)


@router.message(F.text == "Change level")
async def change_level(message: Message):
    await message.answer("Choose level:", reply_markup=level_kb())


@router.message(F.text == "About")
async def about(message: Message):
    await message.answer("GoSurf uses ocean data to find best surf spots")


@router.message(F.text == "GoSurf Pro")
async def pro(message: Message):
    await message.answer("Pro version coming soon")


# =========================
# RUN
# =========================

async def main():
    dp.include_router(router)

    # КРИТИЧЕСКИЙ ФИКС (убирает конфликт polling/webhook)
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())