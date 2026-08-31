import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode

from decision_engine import get_best_spot, get_alternative_spots

# --- CONFIG через ENV (ВАЖНО для Render)
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set")

# --- LOGGING (Render-friendly)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

# --- MEMORY STORE (простой и стабильный)
user_level = {}


# =========================
# KEYBOARDS
# =========================

def level_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="Beginner", callback_data="level_beginner")
    kb.button(text="Intermediate", callback_data="level_intermediate")
    kb.button(text="Advanced", callback_data="level_advanced")
    kb.adjust(1)
    return kb.as_markup()


def main_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔄 Update", callback_data="update")
    kb.button(text="📍 Alternative spots", callback_data="alternatives")
    kb.adjust(1)
    return kb.as_markup()


# =========================
# HANDLERS
# =========================

@router.message(Command("start"))
async def start_handler(message: Message):
    await message.answer(
        "GoSurf will help you find the best surf spot today 🌊\n\n"
        "Choose your level:",
        reply_markup=level_keyboard()
    )


@router.callback_query(F.data.startswith("level_"))
async def level_handler(callback: CallbackQuery):
    level = callback.data.split("_")[1]
    user_level[callback.from_user.id] = level

    await callback.answer()
    await callback.message.answer("⏳ Loading...")

    await send_spot(callback.message, level)


async def send_spot(message: Message, level: str):
    try:
        result = await get_best_spot(level)

        caption = (
            f"<b>🏄 {result['spot']}</b>\n\n"
            f"🌊 Wave: {result['wave']} m\n"
            f"⏱ Period: {result['period']} s\n"
            f"💨 Wind: {result['wind']} m/s\n\n"
            f"<b>Why:</b> {result['why']}\n\n"
            f"<i>Some data may be unavailable from Stormglass API</i>"
        )

        photo_path = f"assets/{result['spot'].lower()}.jpg"

        if os.path.exists(photo_path):
            await message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=caption,
                reply_markup=main_keyboard()
            )
        else:
            # fallback если нет картинки
            await message.answer(
                caption,
                reply_markup=main_keyboard()
            )

    except Exception as e:
        logging.exception("SEND_SPOT_ERROR")
        await message.answer("⚠️ Failed to load surf data.")


@router.callback_query(F.data == "update")
async def update_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.answer()
        await callback.message.answer("Please use /start")
        return

    await callback.answer()
    await callback.message.answer("🔄 Updating...")

    await send_spot(callback.message, level)


@router.callback_query(F.data == "alternatives")
async def alternatives_handler(callback: CallbackQuery):
    level = user_level.get(callback.from_user.id)

    if not level:
        await callback.answer()
        await callback.message.answer("Please use /start")
        return

    try:
        spots = await get_alternative_spots(level)

        text = "<b>📍 Alternative spots</b>\n\n"

        for s in spots:
            text += (
                f"<b>{s['spot']}</b>\n"
                f"🌊 {s['wave']}m | ⏱ {s['period']}s | 💨 {s['wind']}m/s\n\n"
            )

        photo_path = "assets/alt.png"

        if os.path.exists(photo_path):
            await callback.message.answer_photo(
                photo=FSInputFile(photo_path),
                caption=text
            )
        else:
            await callback.message.answer(text)

    except Exception:
        logging.exception("ALT_ERROR")
        await callback.message.answer("⚠️ Failed to load alternatives")

    await callback.answer()


# =========================
# START
# =========================

async def main():
    dp.include_router(router)

    logging.info("Bot started (polling)...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())