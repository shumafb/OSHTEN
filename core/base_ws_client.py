# core/base_ws_client.py

import asyncio
import websockets
import json
import logging

logging.basicConfig(level=logging.INFO)

class BaseWSClient:
    def __init__(self, url: str, subscribe_payload: dict, name: str, message_handler):
        self.url = url
        self.subscribe_payload = subscribe_payload
        self.name = name
        self.message_handler = message_handler
        self.ws = None
        self.reconnect_delay = 5  # seconds

    async def connect(self):
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=20, ping_timeout=10) as ws:
                    self.ws = ws
                    logging.info(f"[{self.name}] Connected to {self.url}")
                    await self.subscribe()
                    await self.listen()
            except Exception as e:
                logging.warning(f"[{self.name}] Connection error: {e}")
                logging.info(f"[{self.name}] Reconnecting in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)

    async def subscribe(self):
        msg = json.dumps(self.subscribe_payload)
        await self.ws.send(msg)
        logging.info(f"[{self.name}] Subscribed with payload: {msg}")

    async def listen(self):
        async for message in self.ws:
            try:
                data = json.loads(message)
                await self.message_handler(data)
            except Exception as e:
                logging.error(f"[{self.name}] Failed to handle message: {e}")
