from mean_reversion import MeanReversion
from exchange import Exchange

class TradingBot:
    def __init__(self):
        self.exchange = Exchange()
        self.strategy = MeanReversion()

    def run(self, symbol="BTCUSDT", timeframe="1h"):
        """Spustí živé obchodování."""
        historical_data = self.exchange.get_historical_data(symbol, timeframe, 100)
        df = pd.DataFrame(historical_data)
        df["signal"] = self.strategy.generate_signals(df)

        latest_signal = df["signal"].iloc[-1]

        if latest_signal == "BUY":
            print("[BOT] Odesílám BUY objednávku")
            # execution.send_order("BUY", symbol)

        elif latest_signal == "SELL":
            print("[BOT] Odesílám SELL objednávku")
            # execution.send_order("SELL", symbol)

bot = TradingBot()
bot.run()
