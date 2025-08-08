import logging
import time
from typing import Dict


class PriceState:
    def __init__(self):
        self.data: Dict[str, Dict[str, float]] = {
            "bybit": {"bid": None, "ask": None, "timestamp": None},
            "okx": {"bid": None, "ask": None, "timestamp": None}
        }

    def update(self, exchange: str, bid: float = None, ask: float = None, timestamp: float = None):
        if exchange not in self.data:
            self.data[exchange] = {"bid": None, "ask": None, "timestamp": None}

        if bid is not None:
            self.data[exchange]["bid"] = bid
        if ask is not None:
            self.data[exchange]["ask"] = ask
        if timestamp is not None:
            self.data[exchange]["timestamp"] = timestamp

    def get(self, exchange: str):
        return self.data.get(exchange)

    def get_all(self):
        return self.data

    def is_ready(self):
        return all("bid" in self.data[ex] and "ask" in self.data[ex] for ex in self.data)