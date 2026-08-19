import asyncio
import os

from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from weather import build_forecast
from decision_engine import build_recommendation


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")


bot = Bot(
    token=BOT_TOKEN
)

dp = Dispatcher()



# ----------------------
# START
# ----------------------

@dp.message(F.text == "/start")
async def start(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🏄 Beginner",
                    callback_data="level_beginner"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🌊 Intermediate",
                    callback_data="level_intermediate"
                )
            ]

        ]
    )


    await message.answer(
        """
🏄 Welcome to Go Surf Bali

I will help you find the best surf spot today.

Choose your level:
        """,
        reply_markup=keyboard
    )



# ----------------------
# LEVEL
# ----------------------

@dp.callback_query(
    F.data.startswith("level_")
)
async def choose_level(
        callback: CallbackQuery
):

    level = callback.data.replace(
        "level_",
        ""
    )


    await callback.answer()


    await send_forecast(
        callback.message,
        level
    )



# ----------------------
# FORECAST
# ----------------------

async def send_forecast(
        message: Message,
        level: str
):


    forecast = build_forecast()


    print(
        "FORECAST:",
        forecast
    )


    decision = build_recommendation(
        forecast,
        level
    )


    print(
        "DECISION:",
        decision
    )



    best = decision["best"]


    best_data = decision["conditions"]



    text = f"""
🏄 GO SURF TODAY

🥇 Best spot:

{best}


⭐ Score:
{decision['score']}/100


Why:

"""


    for reason in decision["reasons"]:

        text += f"✅ {reason}\n"



    text += f"""

🌊 CONDITIONS

Wave:
{best_data.get('wave_height', '-')} m

Period:
{best_data.get('period', '-')} sec

Swell:
{best_data.get('swell_direction', '-')}


🏖 Alternatives:

"""


    for spot in decision["alternatives"]:

        text += f"• {spot}\n"



    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="🔄 Update",
                    callback_data=f"update_{level}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="🗺 Open map",
                    callback_data=f"map_{best}"
                )
            ]

        ]
    )



    await message.answer(
        text,
        reply_markup=keyboard
    )



# ----------------------
# UPDATE BUTTON
# ----------------------

@dp.callback_query(
    F.data.startswith("update_")
)
async def update_forecast(
        callback: CallbackQuery
):

    level = callback.data.replace(
        "update_",
        ""
    )


    await callback.answer(
        "Updating..."
    )


    await send_forecast(
        callback.message,
        level
    )



# ----------------------
# MAP BUTTON
# ----------------------

@dp.callback_query(
    F.data.startswith("map_")
)
async def open_map(
        callback: CallbackQuery
):

    spot = callback.data.replace(
        "map_",
        ""
    )


    maps = {

        "Uluwatu":
        "https://maps.google.com/?q=Uluwatu+Bali",

        "Canggu":
        "https://maps.google.com/?q=Canggu+Bali",

        "Kuta":
        "https://maps.google.com/?q=Kuta+Bali",

        "Medewi":
        "https://maps.google.com/?q=Medewi+Bali"

    }



    await callback.answer()


    await callback.message.answer(
        f"🗺 {spot}\n\n{maps.get(spot)}"
    )



# ----------------------
# RUN
# ----------------------

async def main():

    print(
        "🔥 Go Surf Bot started"
    )


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(
        main()
    )
