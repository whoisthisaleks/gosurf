import asyncio
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from weather import get_weather
from decision_engine import get_best_spot, get_alternatives

logging.basicConfig(level=logging.INFO)

# ✅ FIX для aiogram 3.7+
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

user_level = {}


# ===== KEYBOARDS =====

def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def result_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Best spot", callback_data="best")
    kb.button(text="Alternative spots", callback_data="alt")
    kb.button(text="Update", callback_data="update")
    kb.adjust(1)
    return kb.as_markup()


# ===== FORMAT =====

def build_message(best, alternatives, show_warning=False):
    alt_text = "\n".join([f"• {s['name']}" for s in alternatives])

    warning = ""
    if show_warning:
        warning = "\n\n<blockquote>Live data temporarily unavailable</blockquote>"

    return f"""
<b>Hey surfer!</b>

<b>{best['name']}</b>

<b>Why:</b>
{best['reason']}

<b>Conditions:</b>
Wave: {best['conditions']['wave']}
Period: {best['conditions']['period']}
Wind: {best['conditions']['wind']}

<b>Alternative spots:</b>
{alt_text}
{warning}
"""


# ===== CORE =====

async def generate_response(message: Message, level: str):
    weather = await get_weather()

    show_warning = False
    if not weather:
        show_warning = True

    best = get_best_spot(weather, level)
    alternatives = get_alternatives(weather, level)

    text = build_message(best, alternatives, show_warning)

    photo = FSInputFile("assets/best.png")

    await message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=result_keyboard()
    )


# ===== HANDLERS =====

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "<b>Hey surfer!</b>\n\nSelect your level:",
        reply_markup=level_keyboard()
    )


@dp.callback_query(F.data.startswith("level_"))
async def set_level(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await callback.message.answer("Looking for waves...")
    await generate_response(callback.message, level)


@dp.callback_query(F.data == "best")
async def best_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Select level first: /start")
        return

    await generate_response(callback.message, level)


@dp.callback_query(F.data == "alt")
async def alt_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Select level first: /start")
        return

    await generate_response(callback.message, level)


@dp.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Select level first: /start")
        return

    await callback.message.answer("Updating...")
    await generate_response(callback.message, level)


# ===== MAIN =====

async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())