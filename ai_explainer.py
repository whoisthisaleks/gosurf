import os
import aiohttp
import logging

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


async def generate_explanation(level, spot, data):
    if not OPENAI_API_KEY:
        return fallback(data)

    prompt = f"""
You are a professional surf coach.

User level: {level}
Spot: {spot}

Conditions:
- wave: {data['wave']} m
- period: {data['period']} sec
- swell direction: {data['direction']}
- wind speed: {data['wind']} m/s

Explain why this spot is good.

Return ONLY 3-4 bullet points.
Short, clean, surfer style.
"""

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            ) as resp:

                data = await resp.json()
                text = data["choices"][0]["message"]["content"]

                return parse_bullets(text)

    except Exception:
        logging.exception("AI_ERROR")
        return fallback(data)


def parse_bullets(text):
    lines = text.split("\n")
    return [l.replace("-", "").strip() for l in lines if l.strip()]


def fallback(data):
    reasons = []

    if data["wave"] > 1:
        reasons.append("good wave size")

    if data["period"] >= 10:
        reasons.append("long swell period")

    if data["wind"] < 6:
        reasons.append("light wind")

    return reasons