# core/scanner.py

import logging
from core.price_state import PriceState

# === НАСТРАИВАЕМЫЕ КОНСТАНТЫ ===
THRESHOLD_PCT = 0.3              # Минимальная прибыль после комиссий (в %)
TAKER_FEE_BYBIT = 0.0018         # Комиссия биржи Bybit (0.18%)
TAKER_FEE_OKX = 0.001            # Комиссия биржи OKX (0.10%)

class ArbitrageScanner:
    def __init__(self, price_state: PriceState):
        self.price_state = price_state
        self.threshold = THRESHOLD_PCT / 100

    async def check_opportunity(self):
        if not self.price_state.is_ready():
            return

        prices = self.price_state.get_all()
        b1 = prices["bybit"]
        b2 = prices["okx"]

        # Сценарий 1: Покупаем на Bybit, продаём на OKX
        await self._evaluate(
            buy_exchange="bybit",
            sell_exchange="okx",
            buy_price=b1["ask"],
            sell_price=b2["bid"],
            fee_buy=TAKER_FEE_BYBIT,
            fee_sell=TAKER_FEE_OKX
        )

        # Сценарий 2: Покупаем на OKX, продаём на Bybit
        await self._evaluate(
            buy_exchange="okx",
            sell_exchange="bybit",
            buy_price=b2["ask"],
            sell_price=b1["bid"],
            fee_buy=TAKER_FEE_OKX,
            fee_sell=TAKER_FEE_BYBIT
        )

    async def _evaluate(self, buy_exchange, sell_exchange, buy_price, sell_price, fee_buy, fee_sell):
        if buy_price <= 0 or sell_price <= 0:
            return

        gross_profit = (sell_price - buy_price) / buy_price
        net_profit = gross_profit - (fee_buy + fee_sell)

        if net_profit > self.threshold:
            logging.info(f"💰 Арбитражная возможность!")
            logging.info(f"Купить на {buy_exchange} @ {buy_price}")
            logging.info(f"Продать на {sell_exchange} @ {sell_price}")
            logging.info(f"Чистая прибыль: {net_profit * 100:.4f}%")