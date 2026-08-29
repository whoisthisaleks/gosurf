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


def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Open map", callback_data="map")
    kb.button(text="Update", callback_data="update")
    kb.button(text="Alternative spots", callback_data="alt")
    kb.adjust(1)
    return kb.as_markup()


def map_keyboard(spot_name: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Open map", callback_data=f"map_{spot_name}")
    kb.adjust(1)
    return kb.as_markup()


# ===== FORMAT =====

def start_text():
    return """<b>Hey surfer!</b>

Let's pick the best surf spot right now.
What's your level?
"""


def result_text(best, alternatives):
    alt_text = "\n".join([s["name"] for s in alternatives])

    return f"""<b>Best spot:</b> <b>{best['name']}</b>

<b>Why:</b> Good wave size & good for your level

<b>Conditions:</b>
Wave: {best['conditions']['wave']}
Period: {best['conditions']['period']}
Wind: {best['conditions']['wind']}

<b>Alternative spots:</b>
{alt_text}
"""


def alt_text_block(spot):
    return f"""<b>{spot['name']}</b>

<b>Conditions:</b>
Wave: {spot['conditions']['wave']}
Period: {spot['conditions']['period']}
Wind: {spot['conditions']['wind']}
"""


# ===== CORE =====

async def send_start(message: Message):
    await message.answer_photo(
        photo=FSInputFile("assets/start.png"),
        caption=start_text(),
        reply_markup=level_keyboard()
    )


async def send_best(message: Message, level: str):
    weather = await get_weather()

    best = get_best_spot(weather, level)
    alternatives = get_alternatives(weather, level)

    await message.answer_photo(
        photo=FSInputFile("assets/best.png"),
        caption=result_text(best, alternatives),
        reply_markup=main_keyboard()
    )


async def send_alternatives(message: Message, level: str):
    weather = await get_weather()
    alternatives = get_alternatives(weather, level)

    for spot in alternatives:
        await message.answer_photo(
            photo=FSInputFile("assets/alt.png"),
            caption=alt_text_block(spot),
            reply_markup=map_keyboard(spot["name"])
        )


# ===== HANDLERS =====

@dp.message(CommandStart())
async def start(message: Message):
    await send_start(message)


@dp.callback_query(F.data.startswith("level_"))
async def set_level(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await send_best(callback.message, level)


@dp.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)
    if not level:
        await send_start(callback.message)
        return

    await send_best(callback.message, level)


@dp.callback_query(F.data == "alt")
async def alt_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)
    if not level:
        await send_start(callback.message)
        return

    await send_alternatives(callback.message, level)


@dp.callback_query(F.data.startswith("map_"))
async def map_handler(callback: CallbackQuery):
    spot = callback.data.replace("map_", "")
    await callback.message.answer(f"Opening map for {spot} soon")


@dp.callback_query(F.data == "map")
async def map_main_handler(callback: CallbackQuery):
    await callback.message.answer("Map coming soon")


# ===== MAIN =====

async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())io.run(main())