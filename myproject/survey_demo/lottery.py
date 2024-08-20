class L:
    def __init__(self, type, risk_free_rate, random_return, mean, std_dv, risky_investment, outcome):
        self.type = type
        self.rf_rate = risk_free_rate
        self.random = random_return
        self.mean = mean
        self.std_dv = std_dv
        self.risk = risky_investment
        self.risk_free = 100 - risky_investment
        self.outcome = outcome