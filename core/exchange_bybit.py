from core.base_ws_client import BaseWSClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# URL для подключения к WebSocket API биржи Bybit
BYBIT_URL = os.getenv("BYBIT_URL", "wss://stream.bybit.com/v5/public/linear")
# Торговая пара BTC/USDT
PAIR = os.getenv("BYBIT_PAIR")
# Канал подписки на тикеры
CHANNEL = f"tickers.{PAIR}"

class BybitWS:
    """
    Клиент для работы с WebSocket API биржи Bybit.
    Получает реал-тайм котировки криптовалютных пар.
    """
    
    def __init__(self, price_callback):
        """
        Инициализация WebSocket клиента Bybit.
        
        Args:
            price_callback (callable): Функция обратного вызова для обработки цен.
                Принимает параметры: exchange (str), bid (float), ask (float)
        """
        self.client = BaseWSClient(
            url=BYBIT_URL,
            subscribe_payload={
                "op": "subscribe",
                "args": [CHANNEL]
            },
            name="Bybit",
            message_handler=self.handle_message
        )
        self.price_callback = price_callback

    async def handle_message(self, msg):
        """
        Обработка входящих WebSocket сообщений.
        
        Args:
            msg (dict): Сообщение от биржи, содержащее данные о ценах.
        """
        # Пропускаем системные сообщения
        if "topic" not in msg or not msg.get("data"):
            return

        if msg["topic"] != CHANNEL:
            return

        data = msg["data"]
        try:
            timestamp = float(msg.get("ts"))
            update = {"exchange": "bybit", "timestamp": timestamp}
            

            if "ask1Price" in data:
                update["ask"] = float(data["ask1Price"])
            if "bid1Price" in data:
                update["bid"] = float(data["bid1Price"])

            if "ask" in update or "bid" in update:
                self.price_callback(**update)


        except Exception as e:
            logging.error(f"[BybitWS] Ошибка парсинга: {e}")

    async def start(self):
        """
        Запускает WebSocket клиент.
        Устанавливает соединение с биржей и начинает получать данные.
        """
        await self.client.connect()
