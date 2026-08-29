import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import BOT_TOKEN
from weather import get_weather
from decision_engine import get_best_spot, get_alternatives

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Храним выбранный уровень пользователя
user_level = {}


# ===== UI =====

def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🟢 Beginner", callback_data="level_beginner")
    kb.button(text="🟡 Intermediate", callback_data="level_intermediate")
    kb.button(text="🔴 Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def result_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🌊 Best spot", callback_data="best")
    kb.button(text="🏄 Alternative spots", callback_data="alt")
    kb.button(text="🔄 Update", callback_data="update")
    kb.adjust(1)
    return kb.as_markup()


# ===== FORMATTERS =====

def format_spot(spot, reason, conditions):
    return f"""
<b>🌊 {spot}</b>

{reason}

<b>Conditions:</b>
• Wave: {conditions.get('wave', '—')}
• Period: {conditions.get('period', '—')}
• Wind: {conditions.get('wind', '—')}
"""


def format_alternatives(spots):
    text = "<b>🏄 Alternative spots:</b>\n\n"

    for s in spots:
        text += f"""
<b>{s['name']}</b>
{s['reason']}
"""

    return text


# ===== CORE =====

async def send_best(message: Message, level: str):
    weather = await get_weather()

    if not weather:
        await message.answer(
            "⚠️ Some data may be unavailable from Stormglass\n\nTry again later."
        )
        return

    best = get_best_spot(weather, level)

    text = format_spot(
        best["name"],
        best["reason"],
        best["conditions"]
    )

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
        "<b>🏄 GoSurf</b>\n\nSelect your level:",
        reply_markup=level_keyboard()
    )


@dp.callback_query(F.data.startswith("level_"))
async def set_level(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await callback.message.answer("🔍 Finding best spot...")
    await send_best(callback.message, level)


@dp.callback_query(F.data == "best")
async def best_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Please select level first /start")
        return

    await callback.message.answer("🔄 Updating...")
    await send_best(callback.message, level)


@dp.callback_query(F.data == "alt")
async def alt_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Please select level first /start")
        return

    weather = await get_weather()

    if not weather:
        await callback.message.answer("⚠️ No data available")
        return

    alternatives = get_alternatives(weather, level)

    text = format_alternatives(alternatives)

    photo = FSInputFile("assets/alt.png")

    await callback.message.answer_photo(
        photo=photo,
        caption=text,
        reply_markup=result_keyboard()
    )


@dp.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Please select level first /start")
        return

    await callback.message.answer("🔄 Updating conditions...")
    await send_best(callback.message, level)


# ===== MAIN =====

async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())