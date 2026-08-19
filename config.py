import os

from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)


STORMGLASS_API_KEY = os.getenv(
    "STORMGLASS_API_KEY"
)