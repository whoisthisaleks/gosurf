import asyncio
import logging

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery
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


# ===== KEYBOARDS =====

def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def action_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Update", callback_data="update")
    kb.button(text="🔁 Restart", callback_data="restart")
    kb.adjust(1)
    return kb.as_markup()


# ===== HELPERS =====

async def fetch_all_spots():
    results = []

    for spot in SPOTS:
        try:
            data = await get_surf_data(spot)
        except Exception as e:
            print(f"[ERROR] spot fetch {spot['name']}: {e}")
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


def format_spot(title: str, spot: dict) -> str:
    if not spot:
        return f"<b>{title}:</b>\nNo data available\n"

    data = spot["data"]

    if not data or all(v is None for v in data.values()):
        return f"<b>{title}:</b>\nNo data available\n"

    return f"""<b>{title}:</b>
🏄 {spot['name']}
Wave: {data.get('wave_height', '—')} m
Period: {data.get('period', '—')} s
Wind: {data.get('wind_speed', '—')} m/s
"""


# ===== CORE =====

async def generate_and_send(message: Message, level: str):
    try:
        await message.answer("Loading...")

        spots_with_data = await fetch_all_spots()

        result = pick_best_spots(spots_with_data, level)

        best_text = format_spot("Best spot", result.get("best"))
        alt_text = format_spot("Alternative spot", result.get("alternative"))

        text = f"{best_text}\n{alt_text}"

        await message.answer(text, reply_markup=action_keyboard())

    except Exception as e:
        print("[FATAL ERROR]", e)
        await message.answer("No data available")


# ===== HANDLERS =====

@router.message(CommandStart())
async def start_handler(message: Message):
    await message.answer(
        "GoSurf will help you find the best surf spot today 🌊",
        reply_markup=level_keyboard()
    )


@router.callback_query(F.data.startswith("level_"))
async def level_handler(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await generate_and_send(callback.message, level)


@router.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.message.answer("Please select level first")
        return

    await generate_and_send(callback.message, level)


@router.callback_query(F.data == "restart")
async def restart_handler(callback: CallbackQuery):
    user_level.pop(callback.from_user.id, None)

    await callback.message.answer(
        "Select your level:",
        reply_markup=level_keyboard()
    )


# ===== MAIN =====

async def main():
    print("🚀 BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())