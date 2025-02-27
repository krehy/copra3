import logging

class Execution:
    def __init__(self):
        pass

    def execute_trades(self, signals):
        for signal in signals:
            if signal == "BUY":
                logging.info("Vykonán nákupní obchod")
                print("🟢 Nákup proveden")
            elif signal == "SELL":
                logging.info("Vykonán prodejní obchod")
                print("🔴 Prodej proveden")
            else:
                logging.info("Žádná akce (HOLD)")
                print("⚪ Žádná akce (HOLD)")
