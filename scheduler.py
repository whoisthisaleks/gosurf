import asyncio
from datetime import datetime, time
import pytz

from spots import SPOTS
from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from pro import is_pro
from users_storage import get_users

from aiogram.types import FSInputFile

from stats import track_morning


# ======================
# FORMATTERS (локальные)
# ======================

def format_best_morning(best):
    text = f"<b>Best spot: {best.get('spot')}</b>\n"

    if best.get("confidence"):
        text += f"{best['confidence']}\n\n"

    if best.get("bad_day"):
        text += "❌ No good surf today\n\n"

    if best.get("reason"):
        text += f"<b>Why:</b> {best['reason']}\n\n"

    text += f"Wave: {best.get('wave')}m\n"
    text += f"Period: {best.get('period')}s\n"
    text += f"Wind: {best.get('wind')}\n"

    if best.get("swell_dir") is not None:
        text += f"Swell: {int(best['swell_dir'])}°\n"

    if best.get("tide"):
        text += f"Tide: {best.get('tide')}\n"

    return text


def format_all_spots_morning(data):
    text = "<b>All spots:</b>\n\n"

    for spot in data:
        text += f"<b>{spot.get('spot')}</b>\n"
        text += f"Wave: {spot.get('wave')}m\n"
        text += f"Period: {spot.get('period')}s\n"
        text += f"Wind: {spot.get('wind')}\n"

        if spot.get("swell_dir") is not None:
            text += f"Swell: {int(spot['swell_dir'])}°\n"

        if spot.get("tide"):
            text += f"Tide: {spot.get('tide')}\n"

        text += "\n"

    return text


# ======================
# MORNING SEND
# ======================

async def send_morning_forecast(bot):
    print("🌅 Morning forecast started")

    users = get_users()
    print("USERS:", users)

    for chat_id, level in users.items():
        try:
            if not is_pro(chat_id):
                continue  # ❗ только PRO

            data = [fetch_spot_weather(s) for s in SPOTS]

            if not data:
                continue

            best, _ = pick_best_spots(data, level)

            track_morning()

            # 1. 🌅 картинка
            await bot.send_photo(
            chat_id,
            FSInputFile("assets/sun.png")
)

            # 2. 🏄 Best spot
            await bot.send_message(
            chat_id,
            format_best_morning(best)
)

            # 3. 📊 All spots (ВАЖНО: сразу вторым текстовым блоком)
            await bot.send_message(
            chat_id,
            format_all_spots_morning(data)
)

        except Exception as e:
            print("Morning forecast error:", e)


# ======================
# SCHEDULER LOOP
# ======================

async def scheduler_loop(bot):
    tz = pytz.timezone("Asia/Makassar")

    last_run_date = None

    while True:
        now = datetime.now(tz)

        target_time = time(6, 58)

        if (
            now.time().hour == target_time.hour
            and now.time().minute == target_time.minute
            and (last_run_date != now.date())
        ):
            await send_morning_forecast(bot)
            last_run_date = now.date()

            # защита от дублей
            await asyncio.sleep(60)

        await asyncio.sleep(20)


# ======================
# START
# ======================

def start_scheduler(bot):
    print("✅ Scheduler started")
    asyncio.create_task(scheduler_loop(bot))