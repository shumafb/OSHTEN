import asyncio
from core.base_ws_client import BaseWSClient

OKX_URL = "wss://ws.okx.com:8443/ws/v5/public"
PAIR = "BTC-USDT"
CHANNEL = {
    "op": "subscribe",
    "args": [{
        "channel": "tickers",
        "instId": PAIR
    }]
}

class OKXWS:
    def __init__(self, price_callback):
        self.client = BaseWSClient(
            url=OKX_URL,
            subscribe_payload=CHANNEL,
            name="OKX",
            message_handler=self.handle_message
        )
        self.price_callback = price_callback

    async def handle_message(self, msg):
        if "arg" not in msg or msg.get("arg", {}).get("channel") != "tickers":
            return
        if "data" not in msg or not msg["data"]:
            return

        try:
            data = msg["data"][0]
            bid = float(data["bidPx"])
            ask = float(data["askPx"])
            await self.price_callback(
                exchange="okx",
                bid=bid,
                ask=ask
            )
        except Exception as e:
            print(f"[OKXWS] Error parsing price: {e}")

    async def start(self):
        await self.client.connect()
