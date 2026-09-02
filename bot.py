import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    FSInputFile,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN
from weather import get_surf_data
from decision_engine import pick_best_spots
from spots import SPOTS


logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()
router = Router()
dp.include_router(router)

user_level = {}


# ===== MAIN MENU =====

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Restart bot")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="About"), KeyboardButton(text="Pro")]
        ],
        resize_keyboard=True
    )


# ===== MAP LINKS =====

MAP_LINKS = {
    "Uluwatu": "https://maps.google.com/?q=-8.829,115.084",
    "Canggu": "https://maps.google.com/?q=-8.65,115.13",
    "Kuta": "https://maps.google.com/?q=-8.72,115.17",
    "Medewi": "https://maps.google.com/?q=-8.42,114.78"
}


# ===== KEYBOARDS =====

def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def main_inline_keyboard(best_spot: str):
    kb = InlineKeyboardBuilder()

    kb.button(text="Open map", url=MAP_LINKS.get(best_spot))
    kb.button(text="Update", callback_data="update")
    kb.button(text="Alternative spots", callback_data="alt")

    kb.adjust(1)
    return kb.as_markup()


def map_keyboard(spot_name: str):
    kb = InlineKeyboardBuilder()
    kb.button(text="Open map", url=MAP_LINKS.get(spot_name))
    kb.adjust(1)
    return kb.as_markup()


# ===== HELPERS =====

async def fetch_all_spots():
    results = []

    for spot in SPOTS:
        try:
            data = await get_surf_data(spot)
        except Exception as e:
            print(f"[ERROR] {spot['name']}: {e}")
            data = {
                "wave_height": None,
                "period": None,
                "wind_speed": None
            }

        results.append({
            "name": spot["name"],
            "data": data
        })

    return results


def format_conditions(data: dict):
    if not data or all(v is None for v in data.values()):
        return "No data available"

    return f"""Wave: {data.get('wave_height', '—')} m
Period: {data.get('period', '—')} s
Wind: {data.get('wind_speed', '—')} m/s"""


# ===== FLOW =====

async def send_start(message: Message):
    await message.answer_photo(
        photo=FSInputFile("assets/start.png"),
        caption="""<b>Hey surfer!</b>

Let's pick the best surf spot right now.
What's your level?
""",
        reply_markup=main_menu()
    )

    await message.answer(
        "Choose your level:",
        reply_markup=level_keyboard()
    )


async def send_result(message: Message, level: str):
    await message.answer("Loading...", reply_markup=main_menu())

    spots_with_data = await fetch_all_spots()
    result = pick_best_spots(spots_with_data, level)

    best = result.get("best")
    alt = result.get("alternative")

    if not best:
        await message.answer("No data available", reply_markup=main_menu())
        return

    text = f"""<b>Best spot:</b>
🏄 {best['name']}

<b>Conditions:</b>
{format_conditions(best['data'])}
"""

    if alt:
        text += f"""

<b>Alternative spot:</b>
🏄 {alt['name']}
"""

    await message.answer_photo(
        photo=FSInputFile("assets/best.png"),
        caption=text,
        reply_markup=main_inline_keyboard(best["name"])
    )


async def send_alternatives(message: Message, level: str):
    spots_with_data = await fetch_all_spots()
    result = pick_best_spots(spots_with_data, level)

    alt = result.get("alternative")

    if not alt:
        await message.answer("No alternative spots", reply_markup=main_menu())
        return

    # первая альтернатива
    await message.answer_photo(
        photo=FSInputFile("assets/alt.png"),
        caption=f"""<b>{alt['name']}</b>

<b>Conditions:</b>
{format_conditions(alt['data'])}
""",
        reply_markup=map_keyboard(alt["name"])
    )

    # вторая альтернатива (берем третий спот)
    sorted_spots = sorted(
        spots_with_data,
        key=lambda x: x["data"].get("wave_height") or 0,
        reverse=True
    )

    second_alt = sorted_spots[2] if len(sorted_spots) > 2 else None

    if second_alt:
        await message.answer_photo(
            photo=FSInputFile("assets/alt.png"),
            caption=f"""<b>{second_alt['name']}</b>

<b>Conditions:</b>
{format_conditions(second_alt['data'])}
""",
            reply_markup=map_keyboard(second_alt["name"])
        )


# ===== HANDLERS =====

@router.message(CommandStart())
async def start_handler(message: Message):
    await send_start(message)


@router.callback_query(F.data.startswith("level_"))
async def level_handler(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await send_result(callback.message, level)


@router.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await send_start(callback.message)
        return

    await send_result(callback.message, level)


@router.callback_query(F.data == "alt")
async def alt_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await send_start(callback.message)
        return

    await send_alternatives(callback.message, level)


# ===== MENU HANDLERS =====

@router.message(F.text == "Restart bot")
async def restart_handler(message: Message):
    user_level.pop(message.from_user.id, None)
    await send_start(message)


@router.message(F.text == "Change level")
async def change_level_handler(message: Message):
    await message.answer("Choose your level:", reply_markup=level_keyboard())


@router.message(F.text == "About")
async def about_handler(message: Message):
    await message.answer("GoSurf — find best surf spots on Bali 🌊", reply_markup=main_menu())


@router.message(F.text == "Pro")
async def pro_handler(message: Message):
    await message.answer("Pro version coming soon", reply_markup=main_menu())


# ===== MAIN =====

async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())