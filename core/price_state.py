import time
from typing import Dict

class PriceState:
    def __init__(self):
        self.data: Dict[str, Dict[str, float]] = {
            "bybit": {},
            "okx": {}
        }

    def update(self, exchange: str, bid: float, ask: float):
        self.data[exchange] = {
            "bid": bid,
            "ask": ask,
            "timestamp": time.time()
        }

    def get(self, exchange: str):
        return self.data.get(exchange)

    def get_all(self):
        return self.data

    def is_ready(self):
        return all("bid" in self.data[ex] and "ask" in self.data[ex] for ex in self.data)
