import asyncio
from core.base_ws_client import BaseWSClient

BYBIT_URL = "wss://stream.bybit.com/v5/public/linear"
PAIR = "BTCUSDT"
CHANNEL = f"tickers.{PAIR}"

class BybitWS:
    def __init__(self, price_callback):
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
        await self.client.connect()
