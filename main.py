import asyncio
import logging
import datetime

from core.arbitrage_evaluator import ArbitrageEvaluator
from core.exchange_bybit import BybitWS
from core.exchange_okx import OKXWS
from core.price_state import PriceState
from core.paper_trading import PaperTradeExecutor

from notifier.telegram import send_telegram_message, pretty_arbitrage_message, should_notify

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
    paper_executor = PaperTradeExecutor()

    def price_callback(exchange: str, bid: float = None, ask: float = None):
        price_state.update(exchange=exchange, bid=bid, ask=ask)

        if not price_state.is_ready():
            return


        op1 = evaluator.evaluate("okx", "bybit")
        if op1 and should_notify():
            logging.info(f"💰 Арбитраж!: {op1}")
            send_telegram_message(pretty_arbitrage_message(op1))
            paper_executor.execute(op1)

        op2 = evaluator.evaluate("bybit", "okx")
        if op2 and should_notify():
            logging.info(f"💰 Арбитраж!: {op2}")
            send_telegram_message(pretty_arbitrage_message(op2))
            paper_executor.execute(op2)

    bybit = BybitWS(price_callback=price_callback)
    okx = OKXWS(price_callback=price_callback)

    # Запускаем WebSocket-клиентов и сканер
    async def run_ws_clients():
        await asyncio.gather(
            bybit.start(),
            okx.start()
        )

    await run_ws_clients()

if __name__ == "__main__":
    asyncio.run(main())
