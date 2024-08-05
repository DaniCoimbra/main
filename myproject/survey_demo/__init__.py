from otree.api import *
import random
import pandas as pd
import json

class C(BaseConstants):
    NAME_IN_URL = 'survey_demo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 8
    DISTRIBUTION_FILE = '_static/distributions.csv'
    INVESTMENT_MATRIX_FILE = '_static/InvestmentMatrix_0234.csv'

investments = None
R = None

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
    risk_free_investment = models.FloatField(initial=0)
    cumulative_return = models.FloatField(initial=0)
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
        'mu10sigma25rf0', 'mu10sigma25rf2', 'mu10sigma25rf3', 'mu10sigma25rf4',
        'mu10sigma15rf0', 'mu10sigma15rf2', 'mu10sigma15rf3', 'mu10sigma15rf4',
        'mu13sigma25rf0', 'mu13sigma25rf2', 'mu13sigma25rf3', 'mu13sigma25rf4',
        'mu13sigma15rf0', 'mu13sigma15rf2', 'mu13sigma15rf3', 'mu13sigma15rf4'
    ]

    column_name = column_names[(player.lottery_round - 1) % len(column_names)]
    risky_investment = investment_matrix[column_name][investment_amount]

    risk_free_investment = 100 - risky_investment

    distribution_columns = ['a', 'b', 'c', 'd']
    distribution_column = distribution_columns[(player.lottery_round - 1) % len(distribution_columns)]
    random_return = random.choice(distributions[distribution_column])
    
    # Calculate returns
    risky_return = risky_investment * random_return
    risk_free_rate = int(column_name.split('rf')[-1]) / 100
    risk_free_return = (risk_free_investment) * (1 + risk_free_rate)
    
    player.risky_return = risky_return
    player.risk_free_return = risk_free_return
    player.lottery_return = risky_return + risk_free_return - 100
    
    player.cumulative_return += player.lottery_return

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
    print(f"Total Lottery Return: {player.lottery_return}")
    print(f"Cumulative Return: {player.cumulative_return}")
    print("\n")
    
    return risky_investment, random_return, risk_free_investment, risk_free_rate

# PAGES
class InvestmentSelection(Page):
    form_model = 'player'
    form_fields = ['investment_amount']

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'previous_investment': player.investment_amount if player.lottery_round > 1 else None
        }

class Lottery(Page):
    @staticmethod
    def vars_for_template(player: Player):
        risky_investment, random_return, risk_free_investment, risk_free_rate = calculate_lottery_return(player)
        lottery_types = ['A', 'B', 'C', 'D']
        lottery_type = lottery_types[(player.lottery_round - 1) % len(lottery_types)]
        return {
            'lottery_round': player.lottery_round,
            'risky_investment': risky_investment,
            'risk_free_investment': risk_free_investment,
            'random_return': "{:.2f}".format(random_return * 100),
            'risk_free_rate': risk_free_rate * 100,
            'lottery_type': lottery_type,
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.lottery_round += 1

class LotteryResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'investment_amount': player.investment_amount,
            'lottery_return': player.lottery_return,
            'cumulative_return': player.cumulative_return,
        }

class Result(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'cumulative_return': player.cumulative_return,
        }

page_sequence = [
    InvestmentSelection, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    Lottery, LotteryResults, 
    InvestmentSelection,
    Result
]
