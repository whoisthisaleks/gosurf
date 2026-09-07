import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from weather import fetch_spot_weather
from decision_engine import pick_best_spots
from spots import SPOTS

from aiogram.types import FSInputFile


BALI_TZ = pytz.timezone("Asia/Makassar")

users = {}


def register_user(chat_id, level):
    users[chat_id] = level


async def morning_job(bot):
    print("🌅 Morning job started")

    for chat_id, level in users.items():
        try:
            data = [fetch_spot_weather(s) for s in SPOTS]
            best, _ = pick_best_spots(data, level)

            # --- 1. BEST SPOT ---
            text = f"<b>Best spot: {best['spot']}</b>\n"
            text += f"{best.get('confidence', '')}\n\n"

            if best.get("bad_day"):
                text += "❌ No good surf today. Better to skip.\n\n"

            text += f"Why: {best.get('reason', '')}\n\n"

            text += f"Wave: {best['wave']}m\n"
            text += f"Period: {best['period']}s\n"
            text += f"Wind: {best['wind']}\n"

            if best.get("swell_dir"):
                text += f"Swell: {int(best['swell_dir'])}°\n"

            if best.get("tide"):
                text += f"Tide: {best['tide']}\n"

            # отправляем best + картинку
            await bot.send_photo(
                chat_id,
                FSInputFile("assets/sun.png"),
                caption=text
            )

            # --- 2. ALL SPOTS ---
            all_text = "<b>All spots:</b>\n\n"

            for s in data:
                line = f"<b>{s['spot']}</b>\n"
                line += f"Wave: {s['wave']}m\n"
                line += f"Period: {s['period']}s\n"
                line += f"Wind: {s['wind']}\n"

                if s.get("swell_dir"):
                    line += f"Swell: {int(s['swell_dir'])}°\n"

                if s.get("tide"):
                    line += f"Tide: {s['tide']}\n"

                line += "\n"
                all_text += line

            await bot.send_message(chat_id, all_text)

        except Exception as e:
            print(f"Morning job error: {e}")


def start_scheduler(bot):
    scheduler = AsyncIOScheduler(timezone=BALI_TZ)

    scheduler.add_job(
    morning_job,
    trigger="cron",
    hour=6,
    minute=58,
    args=[bot]
)

    scheduler.start()
    print("✅ Scheduler started")