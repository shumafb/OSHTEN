import logging
import time
from typing import Dict, Optional

class PriceState:
    """
    Хранит состояние цен (bid/ask) для нескольких валютных пар с разных бирж.
    """
    def __init__(self, symbols: list[str]):
        """
        Инициализация состояния цен.

        Args:
            symbols (list[str]): Список валютных пар для отслеживания.
        """
        self.symbols = symbols
        self.data: Dict[str, Dict[str, Dict[str, Optional[float]]]] = {
            symbol: {
                "bybit": {"bid": None, "ask": None, "timestamp": None},
                "okx": {"bid": None, "ask": None, "timestamp": None}
            }
            for symbol in symbols
        }

    def update(self, symbol: str, exchange: str, bid: float = None, ask: float = None, timestamp: float = None):
        """
        Обновляет цену для указанной пары и биржи.
        """
        if symbol not in self.data:
            logging.warning(f"[PriceState] Попытка обновить цену для неизвестной пары: {symbol}")
            return
        if exchange not in self.data[symbol]:
            logging.warning(f"[PriceState] Попытка обновить цену для неизвестной биржи: {exchange}")
            return

        if bid is not None:
            self.data[symbol][exchange]["bid"] = bid
        if ask is not None:
            self.data[symbol][exchange]["ask"] = ask
        if timestamp is not None:
            self.data[symbol][exchange]["timestamp"] = timestamp

    def get(self, symbol: str, exchange: str) -> Optional[Dict[str, Optional[float]]]:
        """
        Возвращает данные о цене для указанной пары и биржи.
        """
        return self.data.get(symbol, {}).get(exchange)

    def get_all_for_symbol(self, symbol: str) -> Optional[Dict[str, Dict[str, Optional[float]]]]:
        """
        Возвращает все данные о ценах для указанной пары.
        """
        return self.data.get(symbol)

    def get_all(self) -> Dict[str, Dict[str, Dict[str, Optional[float]]]]:
        """
        Возвращает все данные о ценах.
        """
        return self.data

    def is_ready(self, symbol: str) -> bool:
        """
        Проверяет, есть ли полные данные (bid/ask) для пары с обеих бирж.
        """
        if symbol not in self.data:
            return False
        
        return all(
            self.data[symbol][ex]["bid"] is not None and self.data[symbol][ex]["ask"] is not None
            for ex in self.data[symbol]
        )

    def is_stale(self, symbol: str, timeout: int = 10) -> bool:
        """
        Проверяет, не устарели ли данные для указанной пары.
        """
        now = time.time()
        if symbol not in self.data:
            return True # Если данных нет, считаем их "устаревшими"

        return any(
            (now - self.data[symbol][ex].get("timestamp", now)) > timeout
            for ex in self.data[symbol]
        )
