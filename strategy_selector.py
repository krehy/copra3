from mean_reversion import MeanReversion

class StrategySelector:
    def __init__(self):
        self.mean_reversion = MeanReversion()

    def select_strategy(self, historical_data):
        # Prozatím máme jen Mean Reversion, takže ji vždy vrátíme
        return self.mean_reversion
