import logging
import os
import time
from typing import Optional

import aiohttp
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org/bot")

LAST_NOTIFICATION_TIME = 0
COOLDOWN_SECONDS = float(os.getenv("TELEGRAM_COOLDOWN_SECONDS", 30))

_session: Optional[aiohttp.ClientSession] = None

async def _get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
    return _session

def should_notify() -> bool:
    global LAST_NOTIFICATION_TIME
    current_time = time.time()
    if current_time - LAST_NOTIFICATION_TIME >= COOLDOWN_SECONDS:
        LAST_NOTIFICATION_TIME = current_time
        return True
    return False

async def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram токен или chat ID не установлен.")
        return

    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    url = f"{TELEGRAM_API_URL}{TELEGRAM_TOKEN}/sendMessage"
    try:
        session = await _get_session()
        async with session.post(url, data=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                logging.error(f"Ошибка отправки сообщения в Telegram: {resp.status}, {body}")
            else:
                logging.info("Сообщение успешно отправлено в Telegram")
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")

async def close_telegram_session():
    global _session
    if _session and not _session.closed:
        await _session.close()
        _session = None


def pretty_arbitrage_message(opportunity: dict) -> str:
    buy = str(opportunity.get("buy_exchange", "N/A")).capitalize()
    sell = str(opportunity.get("sell_exchange", "N/A")).capitalize()
    buy_price = opportunity.get("buy_price", 0)
    sell_price = opportunity.get("sell_price", 0)
    profit = opportunity.get("profit_percent", 0)

    message = (
        f"💰 Арбитраж! <b>+{profit:.3f}%</b>\n\n"
        f"📈 Связка: {buy} → {sell}\n"
        f"🟢 Купить: {buy_price}﹩\n"
        f"🔴 Продать: {sell_price}﹩\n\n"
    )
    return message