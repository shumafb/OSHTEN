# main.py

import asyncio
from core.price_state import PriceState
from core.exchange_bybit import BybitWS
from core.exchange_okx import OKXWS
from core.scanner import ArbitrageScanner

async def main():
    price_state = PriceState()
    scanner = ArbitrageScanner(price_state)

    # Передаем price_callback, который будет обновлять состояние
    bybit = BybitWS(price_callback=price_state.update)
    okx = OKXWS(price_callback=price_state.update)

    # Запускаем WebSocket-клиентов и сканер
    async def run_ws_clients():
        await asyncio.gather(
            bybit.start(),
            okx.start()
        )

    async def run_scanner_loop():
        while True:
            await scanner.check_opportunity()
            await asyncio.sleep(0.5)

    await asyncio.gather(
        run_ws_clients(),
        run_scanner_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
