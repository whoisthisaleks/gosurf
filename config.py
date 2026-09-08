from dotenv import load_dotenv
import os

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")