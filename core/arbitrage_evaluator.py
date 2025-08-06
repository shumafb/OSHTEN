from core.price_state import PriceState
import os
from dotenv import load_dotenv

load_dotenv()

TAKER_FEE_BYBIT = float(os.getenv("TAKER_FEE_BYBIT"))
TAKER_FEE_OKX = float(os.getenv("TAKER_FEE_OKX"))
THRESHOLD_PERCENT = float(os.getenv("THRESHOLD_PERCENT"))


class ArbitrageEvaluator:
    def __init__(self, price_state: PriceState):
        self.price_state = price_state
        self.fees = {
            "bybit": TAKER_FEE_BYBIT,
            "okx": TAKER_FEE_OKX
        }
        self.min_profit_percent = THRESHOLD_PERCENT

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
            "fee_buy": fee_buy,
            "fee_sell": fee_sell,
            "profit_percent": round(profit_percent, 4)
        }