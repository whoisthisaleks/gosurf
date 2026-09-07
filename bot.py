import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import TELEGRAM_TOKEN
from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from spots import SPOTS


class UserState(StatesGroup):
    level = State()


bot = Bot(
    token=TELEGRAM_TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=MemoryStorage())


# --- KEYBOARDS ---

def level_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Beginner")],
            [KeyboardButton(text="Intermediate")],
            [KeyboardButton(text="Advanced")],
        ],
        resize_keyboard=True
    )


def action_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Update")],
            [KeyboardButton(text="All spots")],
            [KeyboardButton(text="Change level")],
            [KeyboardButton(text="Restart")],
        ],
        resize_keyboard=True
    )


# --- FORMAT ---

def format_best(best, alternatives):
    text = f"<b>Best spot: {best['spot']}</b>\n\n"

    # WHY ПЕРЕД CONDITIONS
    text += f"Why: {best.get('reason', 'good conditions')}\n\n"

    text += f"Wave: {best['wave']}m\n"
    text += f"Period: {best['period']}s\n"
    text += f"Wind: {best['wind']}\n"

    if best.get("swell_dir"):
        text += f"Swell: {int(best['swell_dir'])}°\n"

    if best.get("tide"):
        text += f"Tide: {best['tide']}\n"

    text += "\n<b>Alternatives:</b>\n\n"
    for alt in alternatives:
        text += f"{alt['spot']}\n"

    return text


def format_alternatives(alternatives):
    text = "<b>Alternatives:</b>\n\n"

    for alt in alternatives:
        text += f"<b>{alt['spot']}</b>\n"
        text += f"Wave: {alt['wave']}m\n"
        text += f"Period: {alt['period']}s\n"
        text += f"Wind: {alt['wind']}\n"

        if alt.get("swell_dir"):
            text += f"Swell: {int(alt['swell_dir'])}°\n"

        if alt.get("tide"):
            text += f"Tide: {alt['tide']}\n"

        text += "\n"

    return text


def format_all_spot(spot):
    text = f"<b>{spot['spot']}</b>\n"
    text += f"Wave: {spot['wave']}m\n"
    text += f"Period: {spot['period']}s\n"
    text += f"Wind: {spot['wind']}\n"

    if spot.get("swell_dir"):
        text += f"Swell: {int(spot['swell_dir'])}°\n"

    if spot.get("tide"):
        text += f"Tide: {spot['tide']}\n"

    return text


async def load_all_data():
    return [fetch_spot_weather(s) for s in SPOTS]


async def send_forecast(message, level):
    data = await load_all_data()
    best, alternatives = pick_best_spots(data, level)

    await message.answer_photo(
        FSInputFile("assets/best.png"),
        caption=format_best(best, alternatives),
        reply_markup=action_keyboard()
    )

    await message.answer_photo(
        FSInputFile("assets/alt.png"),
        caption=format_alternatives(alternatives)
    )


# --- HANDLERS ---

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()

    await message.answer_photo(
        FSInputFile("assets/start.png"),
        caption=(
            "<b>Hey surfer!</b>\n\n"
            "Find the best surf spot based on current conditions\n\n"
            "Choose your level:"
        ),
        reply_markup=level_keyboard()
    )


@dp.message(F.text.in_(["Beginner", "Intermediate", "Advanced"]))
async def handle_level(message: types.Message, state: FSMContext):
    level = message.text

    await state.set_state(UserState.level)
    await state.update_data(level=level)

    await message.answer("Updating forecast...")
    await send_forecast(message, level)


@dp.message(F.text == "Update")
async def update(message: types.Message, state: FSMContext):
    data = await state.get_data()
    level = data.get("level")

    if not level:
        await message.answer("Choose your level first", reply_markup=level_keyboard())
        return

    await message.answer("Updating forecast...")
    await send_forecast(message, level)


@dp.message(F.text == "All spots")
async def all_spots(message: types.Message):
    await message.answer("Updating forecast...")

    data = await load_all_data()

    await message.answer_photo(
        FSInputFile("assets/all.png"),
        caption="<b>All spots:</b>"
    )

    for spot in data:
        await message.answer(format_all_spot(spot))


@dp.message(F.text == "Change level")
async def change_level(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Choose your level:", reply_markup=level_keyboard())


@dp.message(F.text == "Restart")
async def restart(message: types.Message, state: FSMContext):
    await state.clear()
    await start(message, state)


# --- MAIN ---

async def main():
    print("Bot started")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())