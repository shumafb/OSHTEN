import os
from dotenv import load_dotenv

load_dotenv()

# Загрузка комиссий и минимального процента из переменных окружения
TAKER_FEE_BYBIT = float(os.getenv("TAKER_FEE_BYBIT", 0.001))
TAKER_FEE_OKX = float(os.getenv("TAKER_FEE_OKX", 0.001))
THRESHOLD_PERCENT = float(os.getenv("THRESHOLD_PERCENT", 0.1))

class ArbitrageEvaluator:
    """
    Оценивает возможность арбитража между двумя биржами для одной валютной пары.
    """
    def __init__(self):
        self.fees = {
            "bybit": TAKER_FEE_BYBIT,
            "okx": TAKER_FEE_OKX
        }
        self.min_profit_percent = THRESHOLD_PERCENT

    def evaluate(self, symbol: str, prices: dict):
        """
        Оценивает арбитражную возможность.

        Args:
            symbol (str): Валютная пара.
            prices (dict): Словарь с ценами с бирж, например:
                         {"bybit": {"ask": 1, "bid": 2}, "okx": {"ask": 1, "bid": 2}}

        Returns:
            dict or None: Словарь с деталями арбитража или None, если возможности нет.
        """
        # Проверяем все возможные комбинации покупки и продажи
        exchanges = list(prices.keys())
        for i in range(len(exchanges)):
            for j in range(len(exchanges)):
                if i == j:
                    continue

                buy_exchange_name = exchanges[i]
                sell_exchange_name = exchanges[j]

                buy_price_info = prices[buy_exchange_name]
                sell_price_info = prices[sell_exchange_name]

                # Убедимся, что у нас есть и ask и bid цены
                if "ask" not in buy_price_info or "bid" not in sell_price_info:
                    continue
                
                ask_price = buy_price_info["ask"]
                bid_price = sell_price_info["bid"]

                if ask_price is None or bid_price is None:
                    continue

                # Расчет с учетом комиссий
                fee_buy = self.fees.get(buy_exchange_name, 0)
                fee_sell = self.fees.get(sell_exchange_name, 0)

                adjusted_ask = ask_price * (1 + fee_buy)
                adjusted_bid = bid_price * (1 - fee_sell)

                # Проверка на возможность арбитража
                if adjusted_ask >= adjusted_bid:
                    continue

                profit_percent = ((adjusted_bid - adjusted_ask) / adjusted_ask) * 100

                if profit_percent >= self.min_profit_percent:
                    return {
                        "symbol": symbol,
                        "buy_exchange": buy_exchange_name,
                        "sell_exchange": sell_exchange_name,
                        "buy_price": ask_price,
                        "sell_price": bid_price,
                        "profit_percent": round(profit_percent, 4)
                    }
        
        return None
