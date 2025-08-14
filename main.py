import asyncio
import logging
import os
import signal

from dotenv import load_dotenv

from core.arbitrage_evaluator import ArbitrageEvaluator
from core.exchange_bybit import BybitWS
from core.exchange_okx import OKXWS
from core.price_state import PriceState
from notifier.telegram import (
    close_telegram_session,
    pretty_arbitrage_message,
    send_telegram_message,
    should_notify,
)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

# Загрузка переменных окружения
load_dotenv()


async def main():
    """Главная функция запуска и управления приложением."""
    # Загрузка списка валютных пар из .env
    symbols_str = os.getenv("SYMBOLS", "BTC-USDT,ETH-USDT")
    symbols = [symbol.strip() for symbol in symbols_str.split(",")]
    logging.info(f"Запускаем мониторинг для пар: {symbols}")

    # Инициализация компонентов
    price_state = PriceState(symbols)
    arbitrage_evaluator = ArbitrageEvaluator()

    # Обратный вызов для обработки обновлений цен
    async def process_price_update(symbol, exchange, timestamp, bid=None, ask=None):
        # Обновляем состояние цены
        price_state.update(symbol, exchange, bid, ask, timestamp)

        # Проверяем, готовы ли данные для анализа арбитража
        if not price_state.is_ready(symbol):
            return

        # Проверяем, не устарели ли данные
        if price_state.is_stale(symbol, timeout=5):
            logging.warning(f"Данные для {symbol} устарели, пропускаем оценку.")
            return

        # Получаем цены и оцениваем возможность арбитража
        prices = price_state.get_all_for_symbol(symbol)
        opportunity = arbitrage_evaluator.evaluate(symbol, prices)

        if opportunity and should_notify():
            message = pretty_arbitrage_message(opportunity)
            await send_telegram_message(message)

    # Создание и запуск WebSocket клиентов
    bybit_client = BybitWS(symbols, process_price_update)
    okx_client = OKXWS(symbols, process_price_update)

    # Задачи для асинхронного выполнения
    tasks = [bybit_client.start(), okx_client.start()]

    # Ожидание завершения задач
    await asyncio.gather(*tasks)


async def shutdown(loop: asyncio.AbstractEventLoop):
    """Корректное завершение работы приложения."""
    logging.info("Получен сигнал завершения, начинаем остановку...")
    await close_telegram_session()
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    [task.cancel() for task in tasks]
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()
    logging.info("Приложение остановлено.")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    # Настройка обработки сигналов для корректного завершения
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        if not loop.is_closed():
            loop.run_until_complete(shutdown(loop))