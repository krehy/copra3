import pandas as pd
import ta
from rich.console import Console

console = Console()

class MeanReversion:
    def __init__(self, rsi_period=14, rsi_overbought=70, rsi_oversold=30, rsi_exit=50, 
                 stop_loss=0.7864378013513643, take_profit=4.994506295949497, trailing_stop=3.8614223762877744, 
                 risk_per_trade=0.04999851390907937, atr_multiplier=1.000068551515273, 
                 max_drawdown_threshold=0.1, drawdown_risk_factor=0.5, max_risk_per_trade=0.02):
        """
        :param max_drawdown_threshold: Kdy začít snižovat risk (např. 0.1 = 10 %)
        :param drawdown_risk_factor: Kolik % risku zachovat při drawdownu (0.5 = poloviční risk)
        :param max_risk_per_trade: Maximální povolené riziko na obchod (např. 2 %)
        """

        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.rsi_exit = rsi_exit
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop
        self.risk_per_trade = risk_per_trade
        self.atr_multiplier = atr_multiplier
        self.max_drawdown_threshold = max_drawdown_threshold  # ✅ Přidáno do __init__()
        self.drawdown_risk_factor = drawdown_risk_factor  # ✅ Přidáno do __init__()
        self.max_risk_per_trade = max_risk_per_trade  # ✅ Přidáno do __init__()

    def adjust_risk_based_on_drawdown(self, balance, max_balance):
        """Upraví velikost risku podle aktuálního drawdownu."""
        current_drawdown = (max_balance - balance) / max_balance if max_balance > 0 else 0

        if current_drawdown > self.max_drawdown_threshold:
            adjusted_risk = self.risk_per_trade * self.drawdown_risk_factor
        else:
            adjusted_risk = self.risk_per_trade  # Plný risk, pokud drawdown není velký

        return min(adjusted_risk, self.max_risk_per_trade)  # Zabráníme příliš velkému risku

    def calculate_position_size(self, capital, entry_price, stop_loss_price, max_balance):
        """Vypočítá velikost pozice na základě rizika na obchod a drawdownu."""
        adjusted_risk = self.adjust_risk_based_on_drawdown(capital, max_balance)
        risk_amount = capital * adjusted_risk
        risk_per_unit = max(abs(entry_price - stop_loss_price), 1e-8)  # Fix pro malé ATR

        position_size = risk_amount / risk_per_unit  
        position_size = min(max(position_size, 0.001), capital / entry_price)  # Fix pro velikosti
        return position_size, stop_loss_price  

    def generate_signals(self, data: pd.DataFrame, capital, max_balance):
        """Generuje obchodní signály na základě RSI a přidává řízení pozic."""
        data = data.copy()
        data["rsi"] = ta.momentum.RSIIndicator(close=data["close"], window=self.rsi_period).rsi()
        data["atr"] = ta.volatility.AverageTrueRange(high=data["high"], low=data["low"], close=data["close"], window=14).average_true_range()

        # Vstupní podmínky (LONG a SHORT)
        data["long_signal"] = (data["rsi"] < self.rsi_oversold)
        data["short_signal"] = (data["rsi"] > self.rsi_overbought)

        # Výstupní podmínky (CLOSE LONG a CLOSE SHORT)
        data["close_long_signal"] = (data["rsi"] > self.rsi_exit)
        data["close_short_signal"] = (data["rsi"] < self.rsi_exit)

        # Výpočet velikosti pozice a stop-lossu pro LONG i SHORT
        long_sizes, short_sizes = [], []
        long_sl, short_sl = [], []

        for i in range(len(data)):
            entry_price = data["close"].iloc[i]
            atr = data["atr"].iloc[i]

            long_sl_price = entry_price - (atr * max(self.atr_multiplier, 1.0))
            short_sl_price = entry_price + (atr * max(self.atr_multiplier, 1.0))

            long_size, _ = self.calculate_position_size(capital, entry_price, long_sl_price, max_balance)
            short_size, _ = self.calculate_position_size(capital, entry_price, short_sl_price, max_balance)

            long_sizes.append(long_size)
            short_sizes.append(short_size)
            long_sl.append(long_sl_price)
            short_sl.append(short_sl_price)

        # Uložení hodnot do DataFrame
        data["long_position_size"] = long_sizes
        data["short_position_size"] = short_sizes
        data["long_stop_loss_price"] = long_sl
        data["short_stop_loss_price"] = short_sl

        # Take-profit & Trailing Stop pro obě strany
        data["long_take_profit_price"] = data["close"] * (1 + self.take_profit)  # Použití optimalizované hodnoty TP
        data["short_take_profit_price"] = data["close"] * (1 - self.take_profit)  # Použití optimalizované hodnoty TP pro short

        data["long_trailing_stop_price"] = data["close"] * (1 - self.trailing_stop)  # Optimalizovaný trailing stop pro long
        data["short_trailing_stop_price"] = data["close"] * (1 + self.trailing_stop)  # Optimalizovaný trailing stop pro short

        console.print(f"[bold yellow]DEBUG: LONG signály: {data['long_signal'].sum()}, SHORT signály: {data['short_signal'].sum()}[/bold yellow]")
        return data
