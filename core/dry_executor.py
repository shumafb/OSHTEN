import logging
from datetime import datetime

logger = logging.getLogger("arbitrage")

TRADE_VOLUME_USDT = 100  # Сколько USDT использовать в каждой сделке

class DryRunExecutor:
    def __init__(self, initial_usdt: float = 500):
        self.balances = {
            "bybit": {"usdt": initial_usdt, "btc": 0},
            "okx": {"usdt": initial_usdt, "btc": 0},
        }

    def execute(self, buy_exchange, sell_exchange, buy_price, sell_price, fee_buy, fee_sell):
        b_buy = self.balances[buy_exchange]
        b_sell = self.balances[sell_exchange]

        # Проверка доступности средств
        if b_buy["usdt"] < TRADE_VOLUME_USDT:
            logger.warning(f"[{buy_exchange}] Недостаточно USDT для покупки")
            return
        if b_sell["btc"] < TRADE_VOLUME_USDT / buy_price:
            logger.warning(f"[{sell_exchange}] Недостаточно BTC для продажи")
            return

        # Расчёт объёма BTC
        btc_amount = TRADE_VOLUME_USDT / buy_price

        # Учитываем комиссии
        usdt_spent = TRADE_VOLUME_USDT * (1 + fee_buy)
        usdt_received = sell_price * btc_amount * (1 - fee_sell)
        profit = usdt_received - usdt_spent

        # Обновление балансов
        b_buy["usdt"] -= usdt_spent
        b_buy["btc"] += btc_amount

        b_sell["btc"] -= btc_amount
        b_sell["usdt"] += usdt_received

        # Лог
        logger.info(
            f"[{datetime.utcnow().isoformat()}] Симуляция: BUY on {buy_exchange} @ {buy_price:.2f}, "
            f"SELL on {sell_exchange} @ {sell_price:.2f}, PROFIT: {profit:.4f} USDT"
        )