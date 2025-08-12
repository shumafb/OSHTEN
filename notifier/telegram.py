import asyncio
import datetime
import glob
import io
import logging
import os
import time
from typing import Optional, List

import aiohttp
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

LAST_NOTIFICATION_TIME = 0
COOLDOWN_SECONDS = float(os.getenv("TELEGRAM_COOLDOWN_SECONDS", 30))

_session: Optional[aiohttp.ClientSession] = None
_bot_context = {}


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


async def send_telegram_message(text: str, chat_id: str = None):
    chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_TOKEN or not chat_id:
        logging.warning("Telegram токен или chat ID не установлен.")
        return

    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    url = f"{TELEGRAM_API_URL}/sendMessage"
    try:
        session = await _get_session()
        async with session.post(url, data=payload) as resp:
            if resp.status != 200:
                body = await resp.text()
                logging.error(f"Ошибка отправки сообщения в Telegram: {resp.status}, {body}")
            else:
                logging.info(f"Сообщение успешно отправлено в чат {chat_id}")
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка при отправке сообщения в Telegram: {e}")


async def send_telegram_document(document_data: bytes, filename: str, caption: str, chat_id: str):
    if not TELEGRAM_TOKEN or not chat_id:
        logging.warning("Telegram токен или chat ID не установлен.")
        return

    url = f"{TELEGRAM_API_URL}/sendDocument"
    data = aiohttp.FormData()
    data.add_field("chat_id", chat_id)
    data.add_field("caption", caption)
    data.add_field("document", document_data, filename=filename, content_type="text/plain")

    try:
        session = await _get_session()
        async with session.post(url, data=data) as resp:
            if resp.status != 200:
                body = await resp.text()
                logging.error(f"Ошибка отправки документа в Telegram: {resp.status}, {body}")
            else:
                logging.info(f"Документ успешно отправлен в чат {chat_id}")
    except aiohttp.ClientError as e:
        logging.error(f"Ошибка при отправке документа в Telegram: {e}")


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


# --- Command Handling ---

async def handle_command(command: str, chat_id: str):
    if command == "/logs":
        await handle_logs_command(chat_id)
    elif command == "/healthcheck":
        await handle_healthcheck_command(chat_id)
    else:
        await send_telegram_message("Неизвестная команда.", chat_id)


async def handle_logs_command(chat_id: str, lines: int = 300):
    try:
        log_dir = "logs"
        list_of_files = glob.glob(f"{log_dir}/*.log")
        if not list_of_files:
            await send_telegram_message("Лог-файлы не найдены.", chat_id)
            return

        latest_file = max(list_of_files, key=os.path.getctime)
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            log_lines = f.readlines()
            last_lines = log_lines[-lines:]
        
        if not last_lines:
            await send_telegram_message(f"Лог-файл {os.path.basename(latest_file)} пуст.", chat_id)
            return

        caption = f"Последние {len(last_lines)} строк из {os.path.basename(latest_file)}"
        log_data = "".join(last_lines).encode('utf-8')
        filename = f"log_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"

        await send_telegram_document(log_data, filename, caption, chat_id)

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /logs: {e}")
        await send_telegram_message(f"Произошла ошибка при чтении логов: {e}", chat_id)


async def handle_healthcheck_command(chat_id: str):
    try:
        price_state = _bot_context.get("price_state")
        bybit_ws = _bot_context.get("bybit_ws")
        okx_ws = _bot_context.get("okx_ws")

        if not all([price_state, bybit_ws, okx_ws]):
            await send_telegram_message("Компоненты бота не инициализированы.", chat_id)
            return

        bybit_status = "🟢 Подключено" if bybit_ws.client.is_connected() else "🔴 Отключено"
        okx_status = "🟢 Подключено" if okx_ws.client.is_connected() else "🔴 Отключено"

        prices = price_state.get_all()
        now = time.time() * 1000
        
        def get_last_tick_info(exchange_name):
            data = prices.get(exchange_name, {})
            ts = data.get("timestamp")
            if not ts:
                return "Нет данных"
            
            age_ms = now - ts
            return f"{age_ms:.0f} мс назад (bid: {data.get('bid', 'N/A')}, ask: {data.get('ask', 'N/A')})"

        bybit_last_tick = get_last_tick_info("bybit")
        okx_last_tick = get_last_tick_info("okx")

        message = (
            f"<b>🩺 Health Check</b>\n\n"
            f"<b>Соединения:</b>\n"
            f"- Bybit: {bybit_status}\n"
            f"- OKX: {okx_status}\n\n"
            f"<b>Последние данные:</b>\n"
            f"- Bybit: {bybit_last_tick}\n"
            f"- OKX: {okx_last_tick}\n"
        )

        await send_telegram_message(message, chat_id)

    except Exception as e:
        logging.error(f"Ошибка при обработке команды /healthcheck: {e}")
        await send_telegram_message(f"Произошла ошибка при проверке состояния: {e}", chat_id)


async def get_updates(session: aiohttp.ClientSession, offset: int) -> List[dict]:
    url = f"{TELEGRAM_API_URL}/getUpdates"
    params = {"offset": offset, "timeout": 60}
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                return (await resp.json()).get("result", [])
    except (aiohttp.ClientError, asyncio.TimeoutError) as e:
        logging.warning(f"Ошибка получения обновлений от Telegram: {e}")
    return []


async def start_polling():
    logging.info("Запуск Telegram polling...")
    session = await _get_session()
    offset = 0
    while True:
        updates = await get_updates(session, offset)
        for update in updates:
            offset = update["update_id"] + 1
            if "message" in update and "text" in update["message"]:
                message = update["message"]
                chat_id = message["chat"]["id"]
                text = message["text"]
                if text.startswith("/"):
                    logging.info(f"Получена команда '{text}' от чата {chat_id}")
                    await handle_command(text, str(chat_id))
        await asyncio.sleep(1)

def setup_telegram_bot(context: dict):
    global _bot_context
    _bot_context = context
