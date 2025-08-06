import logging
import os
from dotenv import load_dotenv

load_dotenv()
# Загрузка переменных окружения из .env файла
PAPER_BYBIT_BALANCE_USDT = float(os.getenv("PAPER_BYBIT_BALANCE_USDT"))
PAPER_BYBIT_BALANCE_BTC = float(os.getenv("PAPER_BYBIT_BALANCE_BTC"))
PAPER_OKX_BALANCE_USDT = float(os.getenv("PAPER_OKX_BALANCE_USDT"))
PAPER_OKX_BALANCE_BTC = float(os.getenv("PAPER_OKX_BALANCE_BTC"))
PAPER_SAFETY_MARGIN = float(os.getenv("PAPER_SAFETY_MARGIN"))

class PaperTradeExecutor:
    def __init__(self):
        self.balances = {
            "bybit": {"USDT": PAPER_BYBIT_BALANCE_USDT, "BTC": PAPER_BYBIT_BALANCE_BTC},
            "okx": {"USDT": PAPER_OKX_BALANCE_USDT, "BTC": PAPER_OKX_BALANCE_BTC}
        }
        self.safety_margin = PAPER_SAFETY_MARGIN

    def execute(self, opportunity: dict):
        logging.info(f"[PAPER TRADE] Обнаружена возможность: {opportunity}")
        buy_ex = opportunity["buy_exchange"]
        sell_ex = opportunity["sell_exchange"]
        buy_price = opportunity["buy_price"]
        sell_price = opportunity["sell_price"]
        fee_buy = opportunity["fee_buy"]
        fee_sell = opportunity["fee_sell"]

        available_usdt = self.balances[buy_ex]["USDT"] * (1 - self.safety_margin)
        available_btc = self.balances[sell_ex]["BTC"] * (1 - self.safety_margin)

        # Рассчитываем, сколько BTC можно купить на доступный USDT (с учётом комиссии)
        btc_buyable = (available_usdt * (1 - fee_buy)) / buy_price

        # Проверяем, сколько BTC мы реально можем продать на бирже-продаже
        btc_to_trade = min(btc_buyable, available_btc)
        if btc_to_trade <= 0:
            logging.debug("[PAPER TRADE] Недостаточно средств для сделки")
            return

        # Финальные значения сделки
        usdt_spent = btc_to_trade * buy_price / (1 - fee_buy)
        usdt_received = btc_to_trade * sell_price * (1 - fee_sell)
        profit = usdt_received - usdt_spent

        # Обновляем балансы
        self.balances[buy_ex]["USDT"] -= usdt_spent
        self.balances[buy_ex]["BTC"] += btc_to_trade

        self.balances[sell_ex]["BTC"] -= btc_to_trade
        self.balances[sell_ex]["USDT"] += usdt_received

        logging.info(f"[PAPER TRADE] BUY {buy_ex} @ {buy_price:.2f} | SELL {sell_ex} @ {sell_price:.2f}")
        logging.info(f"[PAPER TRADE] BTC: {btc_to_trade:.6f} | Δ USDT: {profit:.4f}")
        logging.info(f"[BALANCE] {buy_ex}: {self.balances[buy_ex]}")
        logging.info(f"[BALANCE] {sell_ex}: {self.balances[sell_ex]}")