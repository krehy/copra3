import sys
import exchange
from mean_reversion import MeanReversion
from trend_following import TrendFollowing
from backtest import Backtest
from optimalization import optimize_strategy
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from PIL import Image  # Přidán import pro zobrazení obrázku

console = Console()

def main_menu():
    """Hlavní menu CLI"""
    with console.screen():
        console.show_cursor(False)  # Skryje kurzor

        while True:
            console.clear()
            console.print(Panel("[bold cyan]📊 Copra_V3 Trading Bot CLI Menu[/bold cyan]", expand=False))

            console.print("[1] 🔍 Spustit Backtesting", style="bold green")
            console.print("[2] ⚙️  Spustit Optimalizaci", style="bold yellow")
            console.print("[3] ❌ Ukončit", style="bold red")

            choice = Prompt.ask("\nVyber možnost", choices=["1", "2", "3"])

            if choice == "1":
                backtest_menu()
            elif choice == "2":
                optimization_menu()
            elif choice == "3":
                console.print("[bold red]Ukončuji program...[/bold red]")
                sys.exit()

def backtest_menu():
    """Menu pro backtesting"""
    while True:
        console.clear()
        console.print(Panel("[bold cyan]📊 Backtesting Menu[/bold cyan]", expand=False))

        console.print("[1] 🔄 Spustit Backtest Mean Reversion", style="bold green")
        console.print("[2] 🔄 Spustit Backtest Trend Following", style="bold blue")
        console.print("[3] 🔙 Zpět na hlavní menu", style="bold red")

        choice = Prompt.ask("\nVyber možnost", choices=["1", "2", "3"])

        if choice in ["1", "2"]:
            run_backtest("mean_reversion" if choice == "1" else "trend_following")
        elif choice == "3":
            return

def run_backtest(strategy_name):
    """Spuštění backtestu pro vybranou strategii"""
    console.clear()
    console.print(Panel(f"[bold cyan]📊 Nastavení Backtestu - {strategy_name.upper()}[/bold cyan]", expand=False))

    symbol = Prompt.ask("Zadej symbol (např. BTCUSDT)", default="BTCUSDT")
    timeframe = Prompt.ask("Zadej timeframe (např. 1h, 4h, 1d)", default="1h")
    candles = int(Prompt.ask("Kolik svíček stáhnout?", default="1000"))
    initial_balance = float(Prompt.ask("Zadej počáteční kapitál", default="10000"))

    strategy = MeanReversion() if strategy_name == "mean_reversion" else TrendFollowing()
    backtest = Backtest(strategy, initial_balance)

    exchange_client = exchange  # Použití exchange.py pro stažení historických dat
    historical_data = exchange_client.get_historical_data(symbol, timeframe, candles)

    # **🔹 OPRAVA – přidání `symbol` a `timeframe` jako argumentů do `run()`**
    results = backtest.run(historical_data, symbol, timeframe)

    display_results(results, strategy_name)

    # **📈 Automaticky zobrazíme graf kapitálu**
    graph_path = results["capital_chart"]
    image = Image.open(graph_path)
    image.show()

    input("\n[Stiskni Enter pro návrat]")

def display_results(results, strategy_name):
    """Zobrazení výsledků backtestu v tabulce"""
    console.clear()
    console.print(Panel(f"[bold cyan]📊 Výsledky Backtestu - {strategy_name.upper()}[/bold cyan]", expand=False))

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Parametr", style="bold cyan")
    table.add_column("Hodnota", justify="right")

    table.add_row("Počet svíček", f"{results['num_candles']}")
    table.add_row("Symbol", f"{results['symbol']}")
    table.add_row("Timeframe", f"{results['timeframe']}")
    table.add_row("Počáteční kapitál", f"${results['initial_balance']}")
    table.add_row("Konečný kapitál", f"${results['final_balance']}")
    table.add_row("Počet obchodů", str(results["trades"]))
    table.add_row("Win Rate", f"{results['win_rate']:.2%}")
    table.add_row("Max Drawdown", f"{results['max_drawdown']:.2f}%")
    table.add_row("Profit Factor", f"{results['profit_factor']:.2f}")
    table.add_row("RRR", f"{results['rrr']:.2f}")
    table.add_row("Průměrný roční výnos", f"{results['annual_return']:.2f}%" if results["annual_return"] is not None else "N/A")
    table.add_row("Sharpe Ratio", f"{results['sharpe_ratio']:.2f}")
    table.add_row("Celkový zisk", f"${results['total_profit']}")
    table.add_row("Celková ztráta", f"${results['total_loss']}")
    table.add_row("Výherní obchody", str(results["total_wins"]))
    table.add_row("Ztrátové obchody", str(results["total_losses"]))
    table.add_row("Průměrný zisk na obchod", f"${results['avg_profit_per_trade']:.2f}")
    table.add_row("Průměrná ztráta na obchod", f"${results['avg_loss_per_trade']:.2f}")
    table.add_row("Testované období", results['test_period'])  # ✅ Oprava – odstraněno `:.2f`

    console.print(table)

def optimization_menu():
    """Menu pro optimalizaci"""
    console.clear()
    console.print(Panel("[bold cyan]⚙️ Optimalizace strategie[/bold cyan]", expand=False))

    console.print("[1] 🔄 Optimalizovat Mean Reversion", style="bold green")
    console.print("[2] 🔄 Optimalizovat Trend Following", style="bold blue")
    console.print("[3] 🔙 Zpět na hlavní menu", style="bold red")

    choice = Prompt.ask("\nVyber možnost", choices=["1", "2", "3"])

    if choice in ["1", "2"]:
        strategy_name = "mean_reversion" if choice == "1" else "trend_following"

        symbol = Prompt.ask("Zadej symbol (např. BTCUSDT)", default="BTCUSDT")
        timeframe = Prompt.ask("Zadej timeframe (např. 1h, 4h, 1d)", default="1h")
        candles = int(Prompt.ask("Kolik svíček stáhnout?", default="10000"))
        initial_balance = float(Prompt.ask("Zadej počáteční kapitál", default="10000"))
        n_trials = int(Prompt.ask("Kolik testů vykonat?", default="50"))
        n_splits = int(Prompt.ask("Kolik Walk-Forward segmentů použít?", default="5"))  # ✅ Přidána možnost zadat segmenty

        optimize_strategy(strategy_name, symbol, timeframe, candles, initial_balance, n_trials, n_splits)

        input("\n[Stiskni Enter pro návrat]")

    elif choice == "3":
        return

if __name__ == "__main__":
    main_menu()
