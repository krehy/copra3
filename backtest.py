import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from rich.console import Console

console = Console()
LOG_FILE = "logs/backtest_debug.log"

class Backtest:
    def __init__(self, strategy, initial_balance=10000):
        """Inicializace backtestovacího enginu."""
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.positions = []
        self.trades = []
        self.max_balance = initial_balance
        self.drawdowns = []
        self.capital_history = [initial_balance]  # Historie kapitálu pro graf
        self.symbol = None  # Přidáme symbol a timeframe
        self.timeframe = None
        self.num_candles = 0  # Počet testovaných svíček

        # Vytvoření složky logs, pokud neexistuje
        os.makedirs("logs", exist_ok=True)

        # Vyčištění starého logu
        with open(LOG_FILE, "w") as f:
            f.write("=== BACKTEST DEBUG LOG ===\n")

    def log_debug(self, message):
        """Zapíše debug zprávu do konzole a log souboru."""
        console.print(message)
        with open(LOG_FILE, "a") as f:
            f.write(message + "\n")

    def run(self, data: pd.DataFrame, symbol: str, timeframe: str):
        """Spustí backtest."""
        self.symbol = symbol
        self.timeframe = timeframe
        self.num_candles = len(data)  # Uložíme počet svíček
        data = self.strategy.generate_signals(data)

        self.log_debug(f"[bold yellow]DEBUG: Spouštím backtest pro {symbol} ({timeframe}) na {self.num_candles} svíčkách...[/bold yellow]")

        for i in range(len(data)):
            row = data.iloc[i]

            # Otevření LONG pozice (pokud nejsme už v obchodě)
            if row["long_signal"] and not self.positions:
                self.log_debug(f"[green]DEBUG: Otevření LONG pozice za {row['close']}[/green]")
                self.positions.append({
                    "entry_price": row["close"],
                    "stop_loss": row["stop_loss_price"],
                    "take_profit": row["take_profit_price"],
                    "trailing_stop": row["trailing_stop_price"]
                })

            # Uzavření LONG pozice (Stop-Loss, Take-Profit, Trailing Stop nebo RSI exit)
            for position in self.positions[:]:  # Procházíme kopii seznamu, aby nedošlo k chybě při mazání položek
                if row["close"] <= position["stop_loss"]:
                    # Stop-Loss aktivován
                    profit = position["stop_loss"] - position["entry_price"]
                    self.balance += profit
                    self.trades.append(profit)
                    self.log_debug(f"[red]DEBUG: SL uzavřel LONG za {row['close']}, Profit: {profit}[/red]")
                    self.positions.remove(position)

                elif row["close"] >= position["take_profit"]:
                    # Take-Profit aktivován
                    profit = position["take_profit"] - position["entry_price"]
                    self.balance += profit
                    self.trades.append(profit)
                    self.log_debug(f"[green]DEBUG: TP uzavřel LONG za {row['close']}, Profit: {profit}[/green]")
                    self.positions.remove(position)

                elif row["close"] < position["trailing_stop"]:
                    # Trailing Stop aktivován
                    profit = position["trailing_stop"] - position["entry_price"]
                    self.balance += profit
                    self.trades.append(profit)
                    self.log_debug(f"[cyan]DEBUG: TS uzavřel LONG za {row['close']}, Profit: {profit}[/cyan]")
                    self.positions.remove(position)

                elif row["close_long_signal"]:
                    # RSI exit signál aktivován
                    profit = row["close"] - position["entry_price"]
                    self.balance += profit
                    self.trades.append(profit)
                    self.log_debug(f"[yellow]DEBUG: RSI exit uzavřel LONG za {row['close']}, Profit: {profit}[/yellow]")
                    self.positions.remove(position)

            # Aktualizace trailing stopu (pokud je v otevřené pozici)
            for position in self.positions:
                if row["close"] > position["entry_price"]:
                    position["trailing_stop"] = max(position["trailing_stop"], row["close"] * (1 - self.strategy.trailing_stop))

            # Aktualizace max balance a drawdownu
            self.max_balance = max(self.max_balance, self.balance)
            drawdown = (self.max_balance - self.balance) / self.max_balance * 100
            self.drawdowns.append(drawdown)

            self.capital_history.append(self.balance)  # Uložení stavu kapitálu

        timeframe_to_minutes = {
            "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "2h": 120, "4h": 240, "6h": 360, "12h": 720,
            "1d": 1440, "1w": 10080, "1M": 43200
        }

        if timeframe in timeframe_to_minutes:
            total_minutes = self.num_candles * timeframe_to_minutes[timeframe]

            years = total_minutes // (60 * 24 * 365)
            days = (total_minutes % (60 * 24 * 365)) // (60 * 24)
            hours = (total_minutes % (60 * 24)) // 60
            minutes = total_minutes % 60

            test_period = f"{years} let, {days} dní, {hours} hodin, {minutes} minut"


            test_years = total_minutes / (60 * 24 * 365)  # Přesný počet let
        else:
            test_period = "Neznámé timeframe"
            test_years = None

        # Výpočet metrik
        total_profit = sum(p for p in self.trades if p > 0)
        total_loss = sum(p for p in self.trades if p < 0)
        total_wins = len([p for p in self.trades if p > 0])
        total_losses = len([p for p in self.trades if p < 0])
        win_rate = total_wins / max(1, len(self.trades))
        max_drawdown = max(self.drawdowns) if self.drawdowns else 0

        # **📌 Opravený výpočet ročního výnosu – zprůměrovaný CAGR**
        if test_years and test_years >= 1:
            yearly_balances = []
            num_years = int(test_years)

            for year in range(1, num_years + 1):
                index = int(year * (self.num_candles / test_years))
                if index < len(self.capital_history):
                    yearly_balances.append(self.capital_history[index])

            if len(yearly_balances) > 1:
                annual_returns = [
                    (yearly_balances[i] / yearly_balances[i - 1]) - 1 for i in range(1, len(yearly_balances))
                ]
                annual_return = (sum(annual_returns) / len(annual_returns)) * 100
            else:
                annual_return = None  # Nedostatek dat pro výpočet
        else:
            annual_return = None  


        # Opravený výpočet Profit Factor
        profit_factor = (total_profit / abs(total_loss)) if total_loss != 0 else float("inf")

        # Výpočet průměrného zisku a ztráty na obchod
        avg_profit_per_trade = total_profit / max(1, total_wins)
        avg_loss_per_trade = total_loss / max(1, total_losses)

        # Opravený výpočet Risk-Reward Ratio (RRR)
        rrr = (avg_profit_per_trade / abs(avg_loss_per_trade)) if total_losses > 0 else float("inf")
        
        sharpe_ratio = np.mean(self.trades) / np.std(self.trades) if len(self.trades) > 1 else 0

        # Generování grafu vývoje kapitálu
        console.print("📈 [bold cyan]Generuji graf kapitálu...[/bold cyan]")
        plt.figure(figsize=(10, 5))
        plt.plot(self.capital_history, label="Kapitál", color="blue")
        plt.xlabel("Počet svíček")
        plt.ylabel("Hodnota kapitálu")
        plt.title(f"Vývoj kapitálu během backtestu ({symbol}, {timeframe})")
        plt.legend()
        plt.grid()

        graph_path = "capital_chart.png"
        plt.savefig(graph_path)
        plt.close()

        self.log_debug(f"[bold magenta]DEBUG: Finální kapitál: {self.balance}[/bold magenta]")
        self.log_debug(f"[bold magenta]DEBUG: Max Drawdown: {max_drawdown}%[/bold magenta]")
        self.log_debug(f"[bold magenta]DEBUG: Win Rate: {win_rate*100:.2f}%[/bold magenta]")

        return {
            "initial_balance": self.initial_balance,
            "final_balance": round(self.balance, 2),
            "trades": len(self.trades),
            "win_rate": win_rate,
            "max_drawdown": max_drawdown,
            "profit_factor": profit_factor,
            "rrr": rrr,
            "annual_return": annual_return,
            "sharpe_ratio": sharpe_ratio,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "total_wins": total_wins,
            "total_losses": total_losses,
            "avg_profit_per_trade": total_profit / max(1, total_wins),
            "avg_loss_per_trade": total_loss / max(1, total_losses),
            "num_candles": self.num_candles,  # Přidáno
            "timeframe": self.timeframe,  # Přidáno
            "symbol": self.symbol,  # Přidáno
            "test_period": test_period,  # **Nově přidané testované období**
            "capital_chart": graph_path  # Přidání cesty ke grafu do výsledků
        }
