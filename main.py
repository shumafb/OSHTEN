import asyncio
import logging

from core.arbitrage_evaluator import ArbitrageEvaluator
from core.exchange_bybit import BybitWS
from core.exchange_okx import OKXWS
from core.price_state import PriceState
from core.dry_executor import DryRunExecutor

logging.basicConfig(
    # level=logging.DEBUG,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("logs/scanner.log"),
        logging.StreamHandler()
                    ])

async def main():
    price_state = PriceState()
    evaluator = ArbitrageEvaluator(price_state)
    dry_executor = DryRunExecutor(price_state)

    def price_callback(exchange: str, bid: float = None, ask: float = None):
        price_state.update(exchange=exchange, bid=bid, ask=ask)

        if not price_state.is_ready():
            return

        logging.debug(f"📈 {exchange} - Bid: {bid}, Ask: {ask}, разница: {ask - bid}")
        
        op1 = evaluator.evaluate("okx", "bybit")
        if op1:
            logging.info(f"💰 Арбитраж!: {op1}")
            dry_executor.execute(op1)
            logging.info(f"Баланс после сделки: {dry_executor.balances}")

        op2 = evaluator.evaluate("bybit", "okx")
        if op2:
            logging.info(f"💰 Арбитраж!: {op2}")
            dry_executor.execute(op2)
            logging.info(f"Баланс после сделки: {dry_executor.balances}")

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
