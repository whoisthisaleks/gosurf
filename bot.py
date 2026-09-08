import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from config import TELEGRAM_TOKEN
from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from spots import SPOTS

from scheduler import start_scheduler
from users_storage import register_user
from pro import (
    start_trial,
    is_pro,
    add_pro_user,
    days_left,
    should_notify_expired
)

from scheduler import send_morning_forecast


bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher()


# ======================
# KEYBOARDS
# ======================

def level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Beginner"),
                KeyboardButton(text="Intermediate"),
                KeyboardButton(text="Advanced")
            ]
        ],
        resize_keyboard=True
    )


def main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="Update"),
                KeyboardButton(text="Change level")
            ],
            [
                KeyboardButton(text="All spots"),
                KeyboardButton(text="Pro")
            ],
            [
                KeyboardButton(text="Restart")
            ]
        ],
        resize_keyboard=True
    )


# ======================
# FORMATTERS
# ======================

def format_best(best, alternatives, pro=False):
    text = f"<b>Best spot: {best.get('spot', 'N/A')}</b>\n"

    if best.get("confidence"):
        text += f"{best['confidence']}\n\n"

    if best.get("bad_day"):
        text += "❌ No good surf today. Better to skip.\n\n"

    # ❗ WHY только для PRO
    if pro and best.get("reason"):
        text += f"<b>Why:</b> {best['reason']}\n\n"

    text += f"Wave: {best.get('wave', 'N/A')}m\n"
    text += f"Period: {best.get('period', 'N/A')}s\n"
    text += f"Wind: {best.get('wind', 'N/A')}\n"

    if best.get("swell_dir") is not None:
        text += f"Swell: {int(best['swell_dir'])}°\n"

    if best.get("tide"):
        text += f"Tide: {best['tide']}\n"

    # alternatives только для PRO
    if pro and alternatives:
        text += "\n\n<b>Alternatives:</b>\n"
        for alt in alternatives:
            text += f"• {alt.get('spot', 'N/A')}\n"

    # paywall
    if not pro:
        text += "\n🔒 <b>Pro users get:</b>\n"
        text += "• Best time to surf today\n"
        text += "• Two alternative spots\n"
        text += "• Full surf analysis\n"
        text += "• Daily forecast\n"

    return text


def format_alternatives(alternatives):
    text = "<b>Alternatives:</b>\n\n"

    for spot in alternatives:
        text += f"<b>{spot.get('spot', 'N/A')}</b>\n"
        text += f"Wave: {spot.get('wave', 'N/A')}m\n"
        text += f"Period: {spot.get('period', 'N/A')}s\n"
        text += f"Wind: {spot.get('wind', 'N/A')}\n"

        if spot.get("swell_dir") is not None:
            text += f"Swell: {int(spot['swell_dir'])}°\n"

        if spot.get("tide"):
            text += f"Tide: {spot['tide']}\n"

        text += "\n"

    return text


def format_all_spots(data):
    text = ""

    for spot in data:
        text += f"<b>{spot.get('spot', 'N/A')}</b>\n"
        text += f"Wave: {spot.get('wave', 'N/A')}m\n"
        text += f"Period: {spot.get('period', 'N/A')}s\n"
        text += f"Wind: {spot.get('wind', 'N/A')}\n"

        if spot.get("swell_dir") is not None:
            text += f"Swell: {int(spot['swell_dir'])}°\n"

        if spot.get("tide"):
            text += f"Tide: {spot['tide']}\n"

        text += "\n"

    return text


# ======================
# STATE
# ======================

user_level = {}


# ======================
# PRO COMMAND
# ======================

@dp.message(Command("pro"))
async def give_pro(message: Message):
    user_id = message.from_user.id
    add_pro_user(user_id)
    await message.answer("✅ You are now PRO user")


# ======================
# SAFE FETCH
# ======================

async def get_safe_data():
    try:
        raw = [fetch_spot_weather(s) for s in SPOTS]
        return [d for d in raw if isinstance(d, dict)]
    except Exception as e:
        print("FETCH ERROR:", e)
        return []


# ======================
# HANDLERS
# ======================

@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    start_trial(user_id)

    await message.answer_photo(
        FSInputFile("assets/start.png"),
        caption=(
            "<b>Hey surfer!</b>\n\n"
            "Find the best surf spot\n\n"
            "Choose your level:"
        ),
        reply_markup=level_keyboard()
    )


@dp.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def handle_level(message: Message):
    level = message.text
    user_level[message.chat.id] = level
    register_user(message.chat.id, level)

    user_id = message.from_user.id
    pro = is_pro(user_id)

    # ❗ уведомление об окончании trial
    if should_notify_expired(user_id):
        await message.answer(
            "Hey surfer!\n\n"
            "Your one-week trial of the Pro version of the bot has ended. "
            "You are now using the Free version.\n\n"
            "To use the full version again, tap the Pro button in the bottom menu.\n\n"
            "🔒 Pro users get:\n"
            "• The best time to surf today\n"
            "• Two alternative spots\n"
            "• Conditions for all spots\n"
            "• Daily morning forecast"
        )

    await message.answer("Updating forecast...")

    data = await get_safe_data()
    if not data:
        await message.answer("⚠️ No surf data available now")
        return

    best, alternatives = pick_best_spots(data, level)

    await message.answer_photo(
        FSInputFile("assets/best.png"),
        caption=format_best(best, alternatives, pro=pro),
        reply_markup=main_keyboard()
    )

    if pro:
        await message.answer_photo(
            FSInputFile("assets/alt.png"),
            caption=format_alternatives(alternatives)
        )


@dp.message(F.text == "Update")
async def update(message: Message):
    level = user_level.get(message.chat.id, "Intermediate")

    user_id = message.from_user.id
    pro = is_pro(user_id)

    if should_notify_expired(user_id):
        await message.answer(
            "Hey surfer!\n\n"
            "Your one-week trial of the Pro version of the bot has ended. "
            "You are now using the Free version.\n\n"
            "To use the full version again, tap the Pro button in the bottom menu.\n\n"
            "🔒 Pro users get:\n"
            "• The best time to surf today\n"
            "• Two alternative spots\n"
            "• Conditions for all spots\n"
            "• Daily morning forecast"
        )

    await message.answer("Updating forecast...")

    data = await get_safe_data()
    if not data:
        await message.answer("⚠️ No surf data available now")
        return

    best, alternatives = pick_best_spots(data, level)

    await message.answer_photo(
        FSInputFile("assets/best.png"),
        caption=format_best(best, alternatives, pro=pro)
    )

    if pro:
        await message.answer_photo(
            FSInputFile("assets/alt.png"),
            caption=format_alternatives(alternatives)
        )


@dp.message(F.text == "All spots")
async def all_spots(message: Message):
    user_id = message.from_user.id

    if not is_pro(user_id):
        await message.answer(
            "🔒 This feature is available in Pro only.\n\n"
            "Tap the Pro button in the menu to unlock full access."
        )
        return

    data = await get_safe_data()
    if not data:
        await message.answer("⚠️ No data")
        return

    await message.answer_photo(
        FSInputFile("assets/all.png"),
        caption=format_all_spots(data)
    )


@dp.message(F.text == "Change level")
async def change_level(message: Message):
    await message.answer("Choose level:", reply_markup=level_keyboard())


@dp.message(F.text == "Restart")
async def restart(message: Message):
    user_level.pop(message.chat.id, None)
    await start(message)


@dp.message(F.text == "Pro")
async def pro_status(message: Message):
    user_id = message.from_user.id

    if is_pro(user_id):
        days = days_left(user_id)

        await message.answer(
            f"🔥 Pro is active\n\nDays left: {days}"
        )
    else:
        # 🔥 авто-продление на 31 день
        add_pro_user(user_id)

        await message.answer(
            "🔥 Pro activated!\n\n"
            "You now have full access for 31 days.\n\n"
            "Enjoy better surf sessions 🤙"
        )

@dp.message(Command("morning"))
async def manual_morning(message: Message):
    await send_morning_forecast(bot)        


# ======================
# MAIN
# ======================

async def main():
    print("Bot started")

    await bot.delete_webhook(drop_pending_updates=True)
    start_scheduler(bot)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())