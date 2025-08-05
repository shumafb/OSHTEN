

from core.price_state import PriceState

class ArbitrageEvaluator:
    def __init__(self, price_state: PriceState):
        self.price_state = price_state
        self.fees = {
            "bybit": 0.0018,  # 0.18%
            "okx": 0.0010     # 0.10%
        }
        self.min_profit_percent = 0.3

    def evaluate(self, buy_exchange: str, sell_exchange: str):
        buy = self.price_state.get(buy_exchange)
        sell = self.price_state.get(sell_exchange)

        if not buy or not sell:
            return None

        if "ask" not in buy or "bid" not in sell:
            return None

        ask = buy["ask"]
        bid = sell["bid"]

        fee_buy = self.fees.get(buy_exchange, 0)
        fee_sell = self.fees.get(sell_exchange, 0)

        adjusted_ask = ask * (1 + fee_buy)
        adjusted_bid = bid * (1 - fee_sell)

        profit_percent = (adjusted_bid - adjusted_ask) / adjusted_ask * 100

        if profit_percent < self.min_profit_percent:
            return None

        return {
            "buy_exchange": buy_exchange,
            "sell_exchange": sell_exchange,
            "buy_price": ask,
            "sell_price": bid,
            "profit_percent": round(profit_percent, 4)
        }