import pandas as pd
import ta
from rich.console import Console

console = Console()

class MeanReversion:
    def __init__(self, rsi_period=14, rsi_overbought=70, rsi_oversold=30, rsi_exit=50, stop_loss=0.02, take_profit=0.05, trailing_stop=0.03):
        """
        Inicializuje Mean Reversion strategii s RSI indikátorem + SL/TP/Trailing Stop.
        :param rsi_period: Počet period pro RSI
        :param rsi_overbought: Hranice překoupeného trhu
        :param rsi_oversold: Hranice přeprodaného trhu
        :param rsi_exit: RSI úroveň pro výstup z obchodu
        :param stop_loss: Stop-loss v procentech (např. 0.02 = 2%)
        :param take_profit: Take-profit v procentech (např. 0.05 = 5%)
        :param trailing_stop: Trailing stop v procentech (např. 0.03 = 3%)
        """
        self.rsi_period = rsi_period
        self.rsi_overbought = rsi_overbought
        self.rsi_oversold = rsi_oversold
        self.rsi_exit = rsi_exit
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.trailing_stop = trailing_stop

    def generate_signals(self, data: pd.DataFrame):
        """Generuje obchodní signály na základě RSI a přidává řízení pozic."""
        data = data.copy()
        data["rsi"] = ta.momentum.RSIIndicator(close=data["close"], window=self.rsi_period).rsi()

        # Vstupní podmínky (LONG)
        data["long_signal"] = (data["rsi"] < self.rsi_oversold)

        # Výstupní podmínky (CLOSE LONG)
        data["close_long_signal"] = (data["rsi"] > self.rsi_exit)

        # Stop-Loss & Take-Profit
        data["stop_loss_price"] = data["close"] * (1 - self.stop_loss)  # SL je 2 % pod vstupem
        data["take_profit_price"] = data["close"] * (1 + self.take_profit)  # TP je 5 % nad vstupem

        # Trailing Stop - začíná na vstupní ceně a posouvá se nahoru, pokud cena roste
        data["trailing_stop_price"] = data["close"] * (1 - self.trailing_stop)  # 3 % pod max cenou

        # **Přidání short_signálu (i když ho Mean Reversion nepoužívá)**
        data["short_signal"] = False  # Mean Reversion neotvírá SHORTY

        # Debug - kolik máme LONG signálů + SL/TP/TL
        num_long = data["long_signal"].sum()
        num_close_long = data["close_long_signal"].sum()
        num_short = data["short_signal"].sum()
        console.print(f"[bold yellow]DEBUG: LONG signálů: {num_long}, CLOSE LONG signálů: {num_close_long}, SHORT signálů: {num_short}[/bold yellow]")

        return data
