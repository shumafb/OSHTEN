import asyncio
import logging
import datetime
import time
import os
from dotenv import load_dotenv

from core.arbitrage_evaluator import ArbitrageEvaluator
from core.exchange_bybit import BybitWS
from core.exchange_okx import OKXWS
from core.price_state import PriceState

from notifier.telegram import (
    send_telegram_message,
    pretty_arbitrage_message,
    should_notify,
    close_telegram_session,
    setup_telegram_bot,
    start_polling
)

load_dotenv()

ENABLE_LATENCY_LOGGING = os.getenv("ENABLE_LATENCY_LOGGING", "False").lower() in ("true", "1", "yes")
MAX_TICK_DELAY_MS = int(os.getenv("MAX_TICK_DELAY_MS"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(f"logs/{datetime.datetime.now().strftime('%Y-%m-%d')}.log"),
        logging.StreamHandler()
    ]
)


async def main():
    price_state = PriceState()
    evaluator = ArbitrageEvaluator(price_state)

    def price_callback(exchange: str, bid: float = None, ask: float = None, timestamp: float = None):
        if bid is None and ask is None:
            return

        price_state.update(exchange=exchange, bid=bid, ask=ask, timestamp=timestamp)

        if not price_state.is_ready():
            return

        # Проверка свежести тиков и рассинхрона между биржами
        if ENABLE_LATENCY_LOGGING or MAX_TICK_DELAY_MS:
            prices = price_state.get_all()
            now_ms = time.time() * 1000
            ts_bybit = prices.get("bybit", {}).get("timestamp")
            ts_okx = prices.get("okx", {}).get("timestamp")

            fresh_bybit = (now_ms - ts_bybit) if ts_bybit is not None else None
            fresh_okx = (now_ms - ts_okx) if ts_okx is not None else None

            if ENABLE_LATENCY_LOGGING:
                desync = abs(fresh_bybit - fresh_okx) if fresh_bybit and fresh_okx else None
                logging.info(f"[LATENCY] bybit: {fresh_bybit:.0f}ms, okx: {fresh_okx:.0f}ms, desync: {desync:.0f}ms")

            if MAX_TICK_DELAY_MS:
                if (fresh_bybit is None or fresh_bybit > MAX_TICK_DELAY_MS) or \
                   (fresh_okx is None or fresh_okx > MAX_TICK_DELAY_MS):
                    return

        op1 = evaluator.evaluate("okx", "bybit")
        if op1:
            logging.info(f"💰 Арбитраж!: {op1}")
            if should_notify():
                asyncio.create_task(send_telegram_message(pretty_arbitrage_message(op1)))

        op2 = evaluator.evaluate("bybit", "okx")
        if op2:
            logging.info(f"💰 Арбитраж!: {op2}")
            if should_notify():
                asyncio.create_task(send_telegram_message(pretty_arbitrage_message(op2)))

    bybit_ws = BybitWS(price_callback=price_callback)
    okx_ws = OKXWS(price_callback=price_callback)

    # Контекст для Telegram-бота
    bot_context = {
        "price_state": price_state,
        "bybit_ws": bybit_ws,
        "okx_ws": okx_ws
    }
    setup_telegram_bot(bot_context)

    # Запускаем WebSocket-клиентов и Telegram polling
    main_tasks = asyncio.gather(
        bybit_ws.start(),
        okx_ws.start(),
        start_polling()
    )

    try:
        await main_tasks
    finally:
        await close_telegram_session()
        logging.info("Бот остановлен.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Получен сигнал KeyboardInterrupt. Завершение работы...")
