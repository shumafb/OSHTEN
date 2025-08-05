import asyncio
from core.base_ws_client import BaseWSClient

# URL для подключения к WebSocket API биржи Bybit
BYBIT_URL = "wss://stream.bybit.com/v5/public/linear"
# Торговая пара BTC/USDT
PAIR = "BTCUSDT"
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
                Ожидаемый формат:
                {
                    "topic": "tickers.BTCUSDT",
                    "data": {
                        "bid1Price": "цена покупки",
                        "ask1Price": "цена продажи"
                    }
                }
        """
        # Пропускаем системные сообщения
        if "topic" not in msg or not msg.get("data"):
            return

        if msg["topic"] != CHANNEL:
            return

        data = msg["data"]
        try:
            bid = float(data["bid1Price"])
            ask = float(data["ask1Price"])
            await self.price_callback(
                exchange="bybit",
                bid=bid,
                ask=ask
            )
        except Exception as e:
            print(f"[BybitWS] Error parsing price: {e}")

    async def start(self):
        """
        Запускает WebSocket клиент.
        Устанавливает соединение с биржей и начинает получать данные.
        """
        await self.client.connect()
