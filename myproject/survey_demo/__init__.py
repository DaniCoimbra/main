from otree.api import *
import random
import pandas as pd
import json

from survey_demo.lottery import L

class C(BaseConstants):
    NAME_IN_URL = 'survey_demo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 8
    DISTRIBUTION_FILE = '_static/distributions.csv'
    INVESTMENT_MATRIX_FILE = '_static/InvestmentMatrix_0234.csv'

investments = None
R = None

lotteries = []

class Subsession(BaseSubsession):
    distributions = models.LongStringField()
    investment_matrix = models.LongStringField()

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    investment_amount = models.IntegerField(initial=0, min=0, max=100)
    lottery_return = models.FloatField(initial=0)
    risky_return = models.FloatField(initial=0)
    risk_free_return = models.FloatField(initial=0)
    risky_investment = models.FloatField(initial=0)
    risk_free_investment = models.FloatField(initial=0)
    lottery_round = models.IntegerField(initial=1)

# FUNCTIONS
def creating_session(subsession: Subsession):
    investments_df = pd.read_csv(C.INVESTMENT_MATRIX_FILE)
    distributions_df = pd.read_csv(C.DISTRIBUTION_FILE)

    # JSON strings
    subsession.distributions = json.dumps(distributions_df.to_dict(orient='list'))
    subsession.investment_matrix = json.dumps(investments_df.to_dict(orient='list'))

def calculate_lottery_return(player: Player):
    distributions = json.loads(player.subsession.distributions)
    investment_matrix = json.loads(player.subsession.investment_matrix)

    
    investment_amount = player.investment_amount
    
    column_names = [
        'mu10sigma25rf0','mu10sigma25rf2','mu10sigma25rf3','mu10sigma25rf4',
        'mu10sigma15rf0','mu10sigma15rf2','mu10sigma15rf3','mu10sigma15rf4',
        'mu13sigma25rf0','mu15sigma25rf2','mu15sigma25rf3','mu15sigma25rf4',
        'mu13sigma15rf0','mu13sigma15rf2','mu13sigma15rf3','mu13sigma15rf4'
    ]

    column_name = column_names[(player.lottery_round - 1) % len(column_names)]
    risky_investment = min(100, float(investment_matrix[column_name][investment_amount]))

    risk_free_investment = 100 - risky_investment

    distribution_columns = ['A', 'B', 'C', 'D']
    distribution_column = distribution_columns[(player.lottery_round - 1) % len(distribution_columns)]
    random_return = random.choice(distributions[distribution_column])
    
    mean = int(column_name.split('mu')[1].split('sigma')[0])
    std_dv = int(column_name.split('sigma')[1].split('rf')[0])

    # Calculate returns
    risky_return = risky_investment * random_return
    risk_free_rate = int(column_name.split('rf')[-1]) / 100
    risk_free_return = (risk_free_investment) * (1 + risk_free_rate)

    outcome = risky_return + risk_free_return
    
    player.risky_investment = risky_investment
    player.risk_free_investment = risk_free_investment
    player.risky_return = risky_return
    player.risk_free_return = risk_free_return
    player.lottery_return = outcome
    
    # debug info
    print(f"Round {player.lottery_round} - Investment Amount: {100}")
    print(f"Risky Investment: {risky_investment}")
    print(f"Risk-Free Investment: {risk_free_investment}")
    print(f"Selected Column: {column_name}")
    print(f"Distribution Column: {distribution_column}")
    print(f"Random Return: {random_return}")
    print(f"Risk-Free Rate: {risk_free_rate}")
    print(f"Risky Return: {risky_return}")
    print(f"Risk-Free Return: {risk_free_return}")
    print(f"Total Return: {player.lottery_return}")
    print("\n")

    lotteries.append(L(distribution_column, risk_free_rate, random_return, mean, std_dv, risky_investment, outcome))    
    
    return mean, std_dv, risk_free_rate

# PAGES
class Intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return {}
    
class Calibration(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {}
    
class InvestmentSelection(Page):
    form_model = 'player'
    form_fields = ['investment_amount']

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'previous_investment': player.investment_amount if player.lottery_round > 1 else None,
        }

class Lottery(Page):
    @staticmethod
    def vars_for_template(player: Player):
        mean, std_dv, rf = calculate_lottery_return(player)
        lottery_types = ['A', 'B', 'C', 'D']
        lottery_type = lottery_types[(player.lottery_round - 1) % len(lottery_types)]
        return {
            'round': player.lottery_round,
            'lottery_type': lottery_type,
            'risk_free_rate': round(rf * 100, 2),
            'mean': round(mean, 2),
            'std_dv': round(std_dv, 2),
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.lottery_round += 1

class LotteryResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'round': player.lottery_round - 1,
            'lottery_type': lotteries[-1].type,
            'risk_free_rate': lotteries[-1].rf_rate,
            'mean': round(lotteries[-1].mean, 2),
            'std_dv': round(lotteries[-1].std_dv, 2),
            'risky_investment': round(lotteries[-1].risk, 2),
            'risk_free_investment': round(100 - lotteries[-1].risk, 2),
        }

class Result(Page):
    @staticmethod
    def vars_for_template(player: Player):
        lottery_4 = lotteries.pop()
        lottery_3 = lotteries.pop()
        lottery_2 = lotteries.pop()
        lottery_1 = lotteries.pop()

        return {
            'lottery_1_risky': round(lottery_1.risk, 2),
            'lottery_1_rf': round(100 - lottery_1.risk, 2),
            'lottery_1_random': round(lottery_1.random, 2),
            'lottery_1_outcome': round(lottery_1.outcome, 2),

            'lottery_2_risky': round(lottery_2.risk, 2),
            'lottery_2_rf': round(100 - lottery_2.risk, 2),
            'lottery_2_random': round(lottery_2.random, 2),
            'lottery_2_outcome': round(lottery_2.outcome, 2),

            'lottery_3_risky': round(lottery_3.risk, 2),
            'lottery_3_rf': round(100 - lottery_3.risk, 2),
            'lottery_3_random': round(lottery_3.random, 2),
            'lottery_3_outcome': round(lottery_3.outcome, 2),

            'lottery_4_risky': round(lottery_4.risk, 2),
            'lottery_4_rf': round(100 - lottery_4.risk, 2),
            'lottery_4_random': round(lottery_4.random, 2),
            'lottery_4_outcome': round(lottery_4.outcome, 2),

            'cumulative_return': round(lottery_1.outcome + lottery_2.outcome + lottery_3.outcome + lottery_4.outcome, 2)
        }

page_sequence = [
    Intro,
    
    InvestmentSelection, 
    Calibration,
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Result,
    
    InvestmentSelection, 
    Calibration,
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Result,
    
    InvestmentSelection, 
    Calibration,
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Result,
    
    InvestmentSelection, 
    Calibration,
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Result,
]
