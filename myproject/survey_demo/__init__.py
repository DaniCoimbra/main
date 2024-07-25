from otree.api import *
import random
import pandas as pd
import json

class C(BaseConstants):
    NAME_IN_URL = 'survey_demo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 8
    INVESTMENTS_FILE = '_static/Investments.csv'
    R_FILE = '_static/R.csv'

investments = None
R = None

class Subsession(BaseSubsession):
    investments = models.LongStringField()
    R = models.LongStringField()

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    risk = models.IntegerField(
        choices=[(i, f'{i}') for i in range(11)],
        widget=widgets.RadioSelectHorizontal
    )
    lottery_return = models.FloatField(initial=0)
    risky_return = models.FloatField(initial=0)
    risk_free_return = models.FloatField(initial=0)
    investment_amount = models.FloatField(initial=0)
    risk_free_investment = models.FloatField(initial=0)
    cumulative_return = models.FloatField(initial=0)
    lottery_round = models.IntegerField(initial=1)

# FUNCTIONS
def creating_session(subsession: Subsession):
    investments_df = pd.read_csv(C.INVESTMENTS_FILE)
    R_df = pd.read_csv(C.R_FILE)

    R_df = R_df.loc[:, (R_df != 0).any(axis=0)]

    # JSON strings
    subsession.investments = json.dumps(investments_df.values.tolist())
    subsession.R = json.dumps(R_df.values.tolist())

def calculate_lottery_return(player: Player):
    investments = json.loads(player.subsession.investments)
    R = json.loads(player.subsession.R)
    
    # Investment ammount
    risk_level = player.risk
    investment_amount = investments[risk_level][player.lottery_round - 1]
    
    # Random return from R
    column_values = [row[player.lottery_round - 1] for row in R if row[player.lottery_round - 1] != 0]
    random_return = random.choice(column_values)

    # Risky and Risk Free Returns
    risky_return = investment_amount * random_return
    risk_free_return = (100 - investment_amount) * (1 + 0.03 if player.lottery_round % 2 == 1 else 0.10)
    
    player.investment_amount = investment_amount
    player.risk_free_investment = 100 - investment_amount
    player.risky_return = risky_return
    player.risk_free_return = risk_free_return
    player.lottery_return = risky_return + risk_free_return
    
    player.cumulative_return += player.lottery_return
    
    return investment_amount, random_return

# PAGES
class RiskSelection(Page):
    form_model = 'player'
    form_fields = ['risk']

    @staticmethod
    def vars_for_template(player: Player):
        risks = [{'i': i, 'investment': i * 10} for i in range(11)]
        return {
            'risks': risks,
            'previous_risk': player.risk if player.lottery_round > 1 else None
        }

class Lottery(Page):
    @staticmethod
    def vars_for_template(player: Player):
        investment_amount, random_return = calculate_lottery_return(player)
        return {
            'lottery_round': player.lottery_round,
            'investment_amount': investment_amount,
            'risk_free_investment': player.risk_free_investment,
            'random_return': random_return,
            'risk_free_rate': 3 if player.lottery_round % 2 == 1 else 10,
            'lottery_type': 'A' if player.lottery_round <= 4 else 'B',
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        calculate_lottery_return(player)
        player.lottery_round += 1

class LotteryResults(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'investment_amount': player.investment_amount,
            'risk_free_investment': player.risk_free_investment,
            'risky_return': player.risky_return,
            'risk_free_return': player.risk_free_return,
            'total_return': player.lottery_return,
            'cumulative_return': player.cumulative_return,
            'risk_free_rate': 3 if player.lottery_round % 2 == 1 else 10,
        }

class Result(Page):
    @staticmethod
    def vars_for_template(player: Player):
        return {
            'cumulative_return': player.cumulative_return,
        }

page_sequence = [RiskSelection, Lottery, LotteryResults, Lottery, LotteryResults, Result, 
                 RiskSelection, Lottery, LotteryResults, Lottery, LotteryResults, Result,
                ]
