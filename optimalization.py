import optuna
import exchange
import os
import numpy as np
from backtest import Backtest
from mean_reversion import MeanReversion
from trend_following import TrendFollowing
from rich.console import Console

console = Console()
LOG_FILE = "logs/optimalization_debug.log"

def log_optimization_results(best_params, avg_score, strategy_name, symbol, timeframe, candles, initial_balance, n_trials, n_splits):
    """Zapíše výsledky optimalizace do logu."""
    os.makedirs("logs", exist_ok=True)

    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write("=== WALK-FORWARD OPTIMALIZACE ===\n")
        f.write(f"Strategie: {strategy_name}\n")
        f.write(f"Symbol: {symbol}, Timeframe: {timeframe}, Počet svíček: {candles}\n")
        f.write(f"Počáteční kapitál: ${initial_balance}\n")
        f.write(f"Počet testů na segment: {n_trials}, Počet segmentů: {n_splits}\n\n")
        f.write("🏆 Nejlepší nalezené parametry:\n")
        for param, value in best_params.items():
            f.write(f"🔹 {param}: {value}\n")
        f.write(f"\n📈 Průměrný dosažený kapitál na testovacích datech: ${avg_score:.2f}\n")

def split_data(historical_data, n_splits=5, train_ratio=0.7):
    """Rozdělí dataset na tréninkové a testovací části."""
    split_size = len(historical_data) // n_splits
    splits = []

    for i in range(n_splits):
        start_idx = i * split_size
        train_end = start_idx + int(split_size * train_ratio)
        test_end = start_idx + split_size

        train_data = historical_data[start_idx:train_end]
        test_data = historical_data[train_end:test_end]

        if len(train_data) == 0 or len(test_data) == 0:
            break  # Pokud už není dostatek dat, přestaneme

        splits.append((train_data, test_data))

    return splits

def objective(trial, strategy_name, train_data, initial_balance, symbol, timeframe):
    """Optimalizační funkce pro Optuna."""

    take_profit = trial.suggest_float("take_profit", 0.5, 5.0)
    stop_loss = trial.suggest_float("stop_loss", 0.5, 5.0)
    trailing_stop = trial.suggest_float("trailing_stop", 0.5, 5.0)
    risk_per_trade = trial.suggest_float("risk_per_trade", 0.01, 0.05)
    atr_multiplier = trial.suggest_float("atr_multiplier", 1.0, 3.0)

    if strategy_name == "mean_reversion":
        strategy = MeanReversion(
            rsi_period=14,
            rsi_overbought=70,
            rsi_oversold=30,
            stop_loss=stop_loss / 100,
            take_profit=take_profit / 100,
            trailing_stop=trailing_stop / 100,
            risk_per_trade=risk_per_trade,
            atr_multiplier=atr_multiplier
        )
    else:
        strategy = TrendFollowing(take_profit, stop_loss, trailing_stop)

    backtest = Backtest(strategy, initial_balance)
    results = backtest.run(train_data.copy(), symbol, timeframe)

    return results["final_balance"]

def optimize_strategy(strategy_name, symbol, timeframe, candles, initial_balance, n_trials, n_splits):
    """Spustí Walk-forward optimalizaci strategie."""
    
    console.print(f"[bold cyan]🚀 Stahuji historická data pro {symbol} ({timeframe})...[/bold cyan]")
    historical_data = exchange.get_historical_data(symbol, timeframe, candles)

    console.print(f"[bold cyan]✅ Data stažena! Spouštím Walk-forward analýzu pro {strategy_name.upper()}...[/bold cyan]")

    splits = split_data(historical_data, n_splits)

    all_scores = []
    best_params = {}

    for i, (train_data, test_data) in enumerate(splits):
        console.print(f"[bold yellow]🔄 Walk-forward segment {i+1}/{len(splits)}...[/bold yellow]")

        study = optuna.create_study(direction="maximize")
        study.optimize(lambda trial: objective(trial, strategy_name, train_data, initial_balance, symbol, timeframe), n_trials=n_trials)

        segment_params = study.best_params
        segment_score = study.best_value

        # Otestování na testovacích datech
        if strategy_name == "mean_reversion":
            strategy = MeanReversion(
                rsi_period=14,
                rsi_overbought=70,
                rsi_oversold=30,
                stop_loss=segment_params["stop_loss"] / 100,
                take_profit=segment_params["take_profit"] / 100,
                trailing_stop=segment_params["trailing_stop"] / 100,
                risk_per_trade=segment_params["risk_per_trade"],
                atr_multiplier=segment_params["atr_multiplier"]
            )
        else:
            strategy = TrendFollowing(segment_params["take_profit"], segment_params["stop_loss"], segment_params["trailing_stop"])

        backtest = Backtest(strategy, initial_balance)
        test_results = backtest.run(test_data.copy(), symbol, timeframe)

        test_score = test_results["final_balance"]
        all_scores.append(test_score)

        if not best_params or test_score > max(all_scores[:-1], default=0):  
            best_params = segment_params  

        console.print(f"[bold green]✅ Segment {i+1} - Testovací kapitál: ${test_score:.2f}[/bold green]")

    avg_score = np.mean(all_scores)

    log_optimization_results(best_params, avg_score, strategy_name, symbol, timeframe, candles, initial_balance, n_trials, n_splits)

    console.print("[bold green]✅ Walk-forward optimalizace dokončena![/bold green]")
    console.print(f"🏆 Průměrný kapitál na testovacích datech: ${avg_score:.2f}")

    return best_params
