import ccxt
import pandas as pd
import time
import sys

# Inicializace Binance API (používáme veřejný přístup pro historická data)
exchange = ccxt.binance()

def get_historical_data(symbol: str, timeframe: str, limit: int = 1000):
    """
    Stáhne historická data pro daný symbol a timeframe z Binance, po dávkách max 1000 svíček.
    
    :param symbol: Symbol páru (např. "BTC/USDT")
    :param timeframe: Timeframe (např. "1m", "5m", "1h", "1d")
    :param limit: Počet svíček, které chceme stáhnout (maximálně 1000 na 1 request)
    :return: DataFrame s historickými daty
    """
    all_candles = []
    since = exchange.milliseconds() - exchange.parse_timeframe(timeframe) * limit * 1000  # Startujeme od času odpovídajícího požadovanému limitu
    total_downloaded = 0  # Počítadlo stažených svíček

    while limit > 0:
        fetch_limit = min(limit, 1000)  # Max 1000 svíček na request
        candles = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=fetch_limit)

        if not candles:
            break  # Binance nevrátila žádná data → konec

        all_candles.extend(candles)
        since = candles[-1][0] + 1  # Posuneme `since` na čas poslední stažené svíčky
        limit -= fetch_limit  # Odečteme stažené svíčky
        total_downloaded += len(candles)  # Aktualizujeme počet stažených svíček

        # LOG: Aktualizace na jednom řádku
        sys.stdout.write(f"\rStahuji svíčky pro test {total_downloaded}/{limit + total_downloaded}")
        sys.stdout.flush()

        time.sleep(0.5)  # Pauza, abychom nezasypali Binance API

    print("\n✅ Stahování dokončeno!")  # Nový řádek po dokončení

    # Převod na pandas DataFrame
    df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")  # Převod na datetime

    return df
