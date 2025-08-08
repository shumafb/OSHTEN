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
from core.paper_trading import PaperTradeExecutor

from notifier.telegram import (
    send_telegram_message,
    pretty_arbitrage_message,
    should_notify,
    close_telegram_session,
)

load_dotenv()

ENABLE_LATENCY_LOGGING = os.getenv("ENABLE_LATENCY_LOGGING", "False").lower() in ("true", "1", "yes")
MAX_TICK_DELAY_MS = int(os.getenv("MAX_TICK_DELAY_MS")) 

logging.basicConfig(
    # level=logging.DEBUG,
    level=logging.INFO,
    # level=logging.ERROR,
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

        # t0 = time.perf_counter()

        price_state.update(exchange=exchange, bid=bid, ask=ask, timestamp=timestamp)

        # t1 = time.perf_counter()

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
                desync = None
                if fresh_bybit is not None and fresh_okx is not None:
                    desync = abs(fresh_bybit - fresh_okx)
                logging.info(f"[LATENCY] bybit: {fresh_bybit} ms, okx: {fresh_okx} ms, desync: {desync} ms")

            if MAX_TICK_DELAY_MS:
                # Если любой тик устарел — пропускаем расчёт
                if (fresh_bybit is None or fresh_bybit > MAX_TICK_DELAY_MS) or (
                    fresh_okx is None or fresh_okx > MAX_TICK_DELAY_MS
                ):
                    return

        # prices = price_state.get_all()
        # ts_bybit = prices.get("bybit", {}).get("timestamp")
        # ts_okx = prices.get("okx", {}).get("timestamp")
        # now = time.time() * 1000

        # fresh_bybit = now - ts_bybit if ts_bybit is not None else None
        # fresh_okx = now - ts_okx if ts_okx is not None else None
        # desync = abs(fresh_bybit - fresh_okx) if fresh_bybit is not None and fresh_okx is not None else None

        # logging.info(f"[LATENCY] bybit: {fresh_bybit} ms, okx: {fresh_okx} ms, desync: {desync} ms")

        op1 = evaluator.evaluate("okx", "bybit")
        # t2 = time.perf_counter()

        if op1:
            logging.info(f"💰 Арбитраж!: {op1}")
            if should_notify():
                asyncio.create_task(send_telegram_message(pretty_arbitrage_message(op1)))
            # t3 = time.perf_counter()
            # send_telegram_message(pretty_arbitrage_message(op1))
            # t4 = time.perf_counter()

            # logging.info(f"Время выполнения: "
            #                 f"price_callback={round((t1 - t0)*1000, 4):.4f}ms, "
            #                 f"evaluate={round((t2 - t1)*1000, 4):.4f}ms, "
            #                 f"logging={round((t3 - t2)*1000, 4):.4f}ms, "
            #                 f"send_telegram_message_1={round((t4 - t3)*1000, 4):.4f}ms, ")

        op2 = evaluator.evaluate("bybit", "okx")
        # t5 = time.perf_counter()
        if op2:
            logging.info(f"💰 Арбитраж!: {op2}")
            if should_notify():
                asyncio.create_task(send_telegram_message(pretty_arbitrage_message(op2)))
            # t6 = time.perf_counter()
            # send_telegram_message(pretty_arbitrage_message(op2))
            # t7 = time.perf_counter()

            # logging.info(f"Время выполнения: "
            #                 f"price_callback={round((t1 - t0)*1000, 4):.4f}ms, "
            #                 f"evaluate={round((t5 - t1)*1000, 4):.4f}ms, "
            #                 f"logging={round((t6 - t5)*1000, 4):.4f}ms, "
            #                 f"send_telegram_message_2={round((t7 - t6)*1000, 4):.4f}ms, ")


    bybit = BybitWS(price_callback=price_callback)
    okx = OKXWS(price_callback=price_callback)

    # Запускаем WebSocket-клиентов и сканер
    async def run_ws_clients():
        await asyncio.gather(
            bybit.start(),
            okx.start()
        )

    try:
        await run_ws_clients()
    finally:
        await close_telegram_session()

if __name__ == "__main__":
    asyncio.run(main())
