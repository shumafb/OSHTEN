from core.base_ws_client import BaseWSClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# URL для подключения к WebSocket API биржи Bybit
BYBIT_URL = os.getenv("BYBIT_URL", "wss://stream.bybit.com/v5/public/linear")

class BybitWS:
    """
    Клиент для работы с WebSocket API биржи Bybit.
    Получает реал-тайм котировки для нескольких криптовалютных пар.
    """
    
    def __init__(self, symbols: list[str], price_callback):
        """
        Инициализация WebSocket клиента Bybit.
        
        Args:
            symbols (list[str]): Список торговых пар для подписки (например, ["BTC-USDT", "ETH-USDT"])
            price_callback (callable): Функция обратного вызова для обработки цен.
                Принимает параметры: symbol(str), exchange (str), bid (float), ask (float), timestamp (float)
        """
        channels = [f"tickers.{symbol.replace('-', '')}" for symbol in symbols]
        self.client = BaseWSClient(
            url=BYBIT_URL,
            subscribe_payload={
                "op": "subscribe",
                "args": channels
            },
            name="Bybit",
            message_handler=self.handle_message
        )
        self.price_callback = price_callback
        # Для обратного маппинга из топика в символ
        self.topic_to_symbol = {channel: symbol for channel, symbol in zip(channels, symbols)}

    async def handle_message(self, msg):
        """
        Обработка входящих WebSocket сообщений.
        """
        if "topic" not in msg or not msg.get("data"):
            return

        topic = msg["topic"]
        symbol = self.topic_to_symbol.get(topic)
        if not symbol:
            return

        data = msg["data"]
        try:
            ts = msg.get("ts")
            timestamp = float(ts) / 1000 if ts is not None else None
            update = {"symbol": symbol, "exchange": "bybit", "timestamp": timestamp}
            
            if "ask1Price" in data:
                update["ask"] = float(data["ask1Price"])
            if "bid1Price" in data:
                update["bid"] = float(data["bid1Price"])

            if "ask" in update or "bid" in update:
                await self.price_callback(**update)

        except Exception as e:
            logging.error(f"[BybitWS] Ошибка парсинга для {symbol}: {e}")

    async def start(self):
        """
        Запускает WebSocket клиент.
        """
        await self.client.connect()