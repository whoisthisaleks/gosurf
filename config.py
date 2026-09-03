import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TELEGRAM_TOKEN")
STORMGLASS_API_KEY = os.getenv("STORMGLASS_API_KEY")

print("TOKEN:", TOKEN)
print("STORM:", STORMGLASS_API_KEY)

if not TOKEN:
    raise ValueError("TELEGRAM_TOKEN is not set")

if not STORMGLASS_API_KEY:
    raise ValueError("STORMGLASS_API_KEY is not set")