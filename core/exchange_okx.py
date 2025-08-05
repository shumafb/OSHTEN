import asyncio
from core.base_ws_client import BaseWSClient

# URL для подключения к WebSocket API биржи OKX
OKX_URL = "wss://ws.okx.com:8443/ws/v5/public"
# Торговая пара BTC/USDT
PAIR = "BTC-USDT"
# Параметры подписки на канал тикеров
CHANNEL = {
    "op": "subscribe",
    "args": [{
        "channel": "tickers",
        "instId": PAIR
    }]
}

class OKXWS:
    """
    Клиент для работы с WebSocket API биржи OKX.
    Получает реал-тайм котировки криптовалютных пар.
    """
    
    def __init__(self, price_callback):
        """
        Инициализация WebSocket клиента OKX.
        
        Args:
            price_callback (callable): Функция обратного вызова для обработки цен.
                Принимает параметры: exchange (str), bid (float), ask (float)
        """
        self.client = BaseWSClient(
            url=OKX_URL,
            subscribe_payload=CHANNEL,
            name="OKX",
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
                    "arg": {"channel": "tickers", ...},
                    "data": [{
                        "bidPx": "цена покупки",
                        "askPx": "цена продажи"
                    }]
                }
        """
        if "arg" not in msg or msg.get("arg", {}).get("channel") != "tickers":
            return
        if "data" not in msg or not msg["data"]:
            return

        try:
            data = msg["data"][0]
            bid = float(data["bidPx"])
            ask = float(data["askPx"])
            self.price_callback(
                exchange="okx",
                bid=bid,
                ask=ask
            )
        except Exception as e:
            print(f"[OKXWS] Ошибка парсинга цены: {e}")

    async def start(self):
        """
        Запускает WebSocket клиент.
        Устанавливает соединение с биржей и начинает получать данные.
        """
        await self.client.connect()