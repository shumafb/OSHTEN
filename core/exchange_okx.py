from core.base_ws_client import BaseWSClient
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# URL для подключения к WebSocket API биржи OKX
OKX_URL = os.getenv("OKX_URL", "wss://ws.okx.com:8443/ws/v5/public")

class OKXWS:
    """
    Клиент для работы с WebSocket API биржи OKX.
    Получает реал-тайм котировки для нескольких криптовалютных пар.
    """
    
    def __init__(self, symbols: list[str], price_callback):
        """
        Инициализация WebSocket клиента OKX.
        
        Args:
            symbols (list[str]): Список торговых пар для подписки (например, ["BTC-USDT", "ETH-USDT"])
            price_callback (callable): Функция обратного вызова для обработки цен.
                Принимает параметры: symbol(str), exchange (str), bid (float), ask (float), timestamp (float)
        """
        # Формируем аргументы для подписки на несколько пар
        args = [
            {
                "channel": "tickers",
                "instId": symbol
            }
            for symbol in symbols
        ]
        
        self.client = BaseWSClient(
            url=OKX_URL,
            subscribe_payload={
                "op": "subscribe",
                "args": args
            },
            name="OKX",
            message_handler=self.handle_message
        )
        self.price_callback = price_callback

    async def handle_message(self, msg):
        """
        Обработка входящих WebSocket сообщений.
        """
        arg = msg.get("arg", {})
        if arg.get("channel") != "tickers" or "instId" not in arg:
            return
        if "data" not in msg or not msg["data"]:
            return

        symbol = arg["instId"]
        try:
            data = msg["data"][0]
            bid = float(data["bidPx"])
            ask = float(data["askPx"])
            ts = data.get("ts")
            # OKX timestamp is in milliseconds, converting to seconds
            timestamp = float(ts) / 1000 if ts is not None else None
            
            await self.price_callback(
                symbol=symbol,
                exchange="okx",
                bid=bid,
                ask=ask,
                timestamp=timestamp
            )
        except Exception as e:
            logging.error(f"[OKXWS] Ошибка парсинга для {symbol}: {e}")

    async def start(self):
        """
        Запускает WebSocket клиент.
        """
        await self.client.connect()