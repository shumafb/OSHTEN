import logging
import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = os.getenv("TELEGRAM_API_URL", "https://api.telegram.org/bot")

LAST_NOTIFICATION_TIME = 0
COOLDOWN_SECONDS = float(os.getenv("TELEGRAM_COOLDOWN_SECONDS", 30))

def should_notify() -> bool:
    global LAST_NOTIFICATION_TIME
    current_time = time.time()
    if current_time - LAST_NOTIFICATION_TIME >= COOLDOWN_SECONDS:
        LAST_NOTIFICATION_TIME = current_time
        return True
    return False

def send_telegram_message(text: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram токен или chat ID не установлен.")
        return

    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(f"{TELEGRAM_API_URL}{TELEGRAM_TOKEN}/sendMessage", data=payload)
        if response.status_code != 200:
            logging.error(f"Ошибка отправки сообщения в Telegram: {response.status_code}, {response.text}")
        else:
            logging.info(f"Сообщение успешно отправлено в Telegram. {text}")
    except requests.RequestException as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")


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


op = {"buy_exchange": "okx",
    "sell_exchange": "bybit",
    "buy_price": 100.0,
    "sell_price": 105.0,
    "profit_percent": 5.0
}

send_telegram_message(pretty_arbitrage_message(op))