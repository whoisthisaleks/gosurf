import logging
from pathlib import Path

from aiogram.types import FSInputFile, KeyboardButton, ReplyKeyboardMarkup

from pro import is_pro
from users_storage import get_users


logger = logging.getLogger(__name__)


async def send_support_message(bot):
    users = get_users()
    project_dir = Path(__file__).resolve().parent
    image_path = project_dir / "support.png"
    if not image_path.is_file():
        image_path = project_dir / "assets" / "support.png"

    keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❤️ Support GoSurf")]],
        resize_keyboard=True,
    )

    for user_id in users.keys():
        if is_pro(user_id):
            continue
        try:
            await bot.send_photo(
                chat_id=user_id,
                photo=FSInputFile(image_path),
                caption=(
                    "🌊 Enjoying GoSurf?\n\n"
                    "Support the project and get:\n"
                    "• better surf spots\n"
                    "• unlimited access\n"
                    "• more accurate forecasts\n\n"
                    "It takes 10 seconds 🤙"
                ),
                reply_markup=keyboard,
            )
        except Exception:
            logger.exception("Could not send support message to user %s", user_id)
