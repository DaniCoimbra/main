from otree.api import *
import random
import pandas as pd
import json

import itertools
import math

from survey_demo.lottery import L

class C(BaseConstants):
    NAME_IN_URL = 'survey_demo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1
    DISTRIBUTION_FILE = '_static/distributions.csv'
    INVESTMENT_MATRIX_FILE = '_static/InvestmentMatrix_0234.csv'
    TREATMENTS = ['treatment_1', 'treatment_2', 'treatment_3']

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
    risky_investment = models.FloatField(initial=0)
    risk_free_investment = models.FloatField(initial=0)
    lottery_round = models.IntegerField(initial=1)
    lotteries = models.LongStringField(initial='[]')
    treatment = models.StringField(initial="")
    chosen_lotteries = models.LongStringField(initial='[]')

# FUNCTIONS
def creating_session(subsession: Subsession):
    import random
    
    # Assign treatment to each participant
    players = subsession.get_players()
    num_players = len(players)
    treatments = C.TREATMENTS
    num_treatments = len(treatments)

    num_players_per_treatment = math.ceil(num_players / num_treatments)
    treatment_list = treatments * num_players_per_treatment

    random.shuffle(treatment_list)

    treatment_list = treatment_list[:num_players]
    
    # Assign treatments to players
    for player, treatment in zip(players, treatment_list):
        player.treatment = treatment
        print('Assigned treatment:', player.treatment)

    # Read files
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

    lottery = L(distribution_column, risk_free_rate, random_return, mean, std_dv, risky_investment, outcome)

    if player.lotteries:
        existing_lotteries = json.loads(player.lotteries)
    else:
        existing_lotteries = []

    existing_lotteries.append(lottery.__dict__)
    
    # Serialize and store back in the player model
    player.lotteries = json.dumps(existing_lotteries)

# PAGES
class Intro(Page):
    @staticmethod
    def is_displayed(player: Player):
        return player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return {}
    
class InvestmentSelection(Page):
    form_model = 'player'
    form_fields = ['investment_amount']

    @staticmethod
    def is_displayed(player: Player):
        # Show InvestmentSelection only for the appropriate rounds
        if player.treatment == 'treatment_2' and player.lottery_round % 2 == 1:
            return True
        elif player.treatment == 'treatment_3' and player.lottery_round % 4 == 1:
            return True
        elif player.treatment == 'treatment_1':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        return {
            'previous_investment': player.investment_amount if player.lottery_round > 1 else None,
        }

    
class Calibration(Page):
    @staticmethod
    def is_displayed(player: Player):
        # Show InvestmentSelection only for the appropriate rounds
        if player.treatment == 'treatment_2' and player.lottery_round % 2 == 1:
            return True
        elif player.treatment == 'treatment_3' and player.lottery_round % 4 == 1:
            return True
        elif player.treatment == 'treatment_1':
            return True
        return False
    @staticmethod
    def vars_for_template(player: Player):
        return {}
    

class Lottery(Page):
    @staticmethod
    def vars_for_template(player: Player):
        if len(json.loads(player.lotteries)) < player.lottery_round:
            calculate_lottery_return(player)
        else:
            print("Skipping")
        lottery_types = ['A', 'B', 'C', 'D']
        lottery_type = lottery_types[(player.lottery_round - 1) % len(lottery_types)]
        lottery = json.loads(player.lotteries)[player.lottery_round-1]
        return {
            'round': player.lottery_round,
            'lottery_type': lottery_type,
            'risk_free_rate': round(lottery.get('rf_rate'), 2),
            'mean': round(lottery.get('mean'), 2),
            'std_dv': round(lottery.get('std_dv'), 2),
            'risky_investment': round(lottery.get('risk'), 2),
            'risk_free_investment': round(lottery.get('risk_free'), 2),
        }
    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.lottery_round += 1
    
class Result(Page):
    @staticmethod
    def is_displayed(player: Player):
        if player.treatment == 'treatment_2' and player.lottery_round % 2 == 1:
            return True
        elif player.treatment == 'treatment_3' and player.lottery_round % 4 == 1:
            return True
        elif player.treatment == 'treatment_1':
            return True
        return False

    @staticmethod
    def vars_for_template(player: Player):
        lotteries = json.loads(player.lotteries) if player.lotteries else []

        round_index = player.lottery_round - 2
        if round_index < 0:
            round_index = 0
        
        # Determine the number of lotteries to display based on the treatment
        if player.treatment == 'treatment_1':
            display_count = 1
        elif player.treatment == 'treatment_2':
            display_count = 2
        elif player.treatment == 'treatment_3':
            display_count = 4
        else:
            display_count = 0

        # Calculate the correct range for the lotteries to display
        if round_index < display_count - 1:
            last_lotteries = lotteries[:round_index + 1]
        else:
            last_lotteries = lotteries[round_index - display_count + 1:round_index + 1]

        # Prepare the lottery data for the template
        lottery_data = {}
        for i in range(display_count):
            index = -display_count + i
            lottery = last_lotteries[index]
            lottery_data[f'lottery_{i+1}_risky'] = round(lottery.get('risk', 0), 2)
            lottery_data[f'lottery_{i+1}_rf'] = round(lottery.get('risk_free', 0), 2)
            lottery_data[f'lottery_{i+1}_random'] = round(lottery.get('random', 0), 2)
            lottery_data[f'lottery_{i+1}_outcome'] = round(lottery.get('outcome', 0), 2)

        # Calculate cumulative return
        cumulative_return = sum(lottery_data[f'lottery_{i+1}_outcome'] for i in range(display_count))
        # player.investment_return.append(cumulative_return)
        current_round = round_index + 1
        round_numbers = [current_round - i for i in reversed(range(display_count))]

        return {
            **lottery_data,
            'lottery_size': len(last_lotteries),
            'cumulative_return': round(cumulative_return, 2),
            'round_numbers': round_numbers,  # Pass round numbers as a list
        }

class End(Page):
    @staticmethod
    def vars_for_template(player: Player):
        # Load the lotteries from the player
        lotteries = json.loads(player.lotteries) if player.lotteries else []
        chosen_lotteries = json.loads(player.chosen_lotteries) if player.chosen_lotteries else []

        # Define block sizes based on treatment
        if player.treatment == 'treatment_1':
            block_size = 1
            num_blocks = 4
        elif player.treatment == 'treatment_2':
            block_size = 2
            num_blocks = 2
        elif player.treatment == 'treatment_3':
            block_size = 4
            num_blocks = 1

        if not player.chosen_lotteries or player.chosen_lotteries.strip() == '[]':
            chosen_indexes = []
            chosen_lotteries = []

            # Choose blocks based on the treatment
            if player.treatment == 'treatment_1':
                chosen_indexes = random.sample(range(len(lotteries)), num_blocks)
            elif player.treatment == 'treatment_2':
                block_indexes = random.sample(range(len(lotteries) // block_size), num_blocks)
                chosen_indexes = [i * block_size + j for i in block_indexes for j in range(block_size)]
            elif player.treatment == 'treatment_3':
                block_indexes = random.sample(range(len(lotteries) // block_size), num_blocks)
                chosen_indexes = [i * block_size + j for i in block_indexes for j in range(block_size)]

            # Ensure we do not exceed the total number of lotteries
            chosen_indexes = sorted(set(chosen_indexes))
            if len(chosen_indexes) > len(lotteries):
                chosen_indexes = sorted(range(len(lotteries)))

            # Collect the chosen lotteries
            chosen_lotteries = [lotteries[i] for i in chosen_indexes]

            # Save chosen lotteries to the player object
            player.chosen_lotteries = json.dumps(chosen_lotteries)
        
        else:
            chosen_lotteries = json.loads(player.chosen_lotteries)
            # Derive chosen indexes from chosen lotteries
            chosen_indexes = [lotteries.index(lottery) for lottery in chosen_lotteries]

        # Prepare the lottery data
        lottery_data = {}
        for i, lottery in enumerate(chosen_lotteries):
            lottery_data[f'lottery_{i+1}_risky'] = round(lottery.get('risk', 0), 2)
            lottery_data[f'lottery_{i+1}_rf'] = round(lottery.get('risk_free', 0), 2)
            lottery_data[f'lottery_{i+1}_random'] = round(lottery.get('random', 0), 2)
            lottery_data[f'lottery_{i+1}_outcome'] = round(lottery.get('outcome', 0), 2)
        
        cumulative_return = sum(lottery_data[f'lottery_{i+1}_outcome'] for i in range(len(chosen_lotteries)))
        payoff = cumulative_return * 0.02
        lottery_size = len(chosen_lotteries)

        # Return the chosen lotteries and their data to the template
        return {
            **lottery_data,
            'num_blocks': num_blocks,
            'lottery_size': lottery_size,
            'chosen_indexes': chosen_indexes,
            'blocks_indices': sorted(set(i // block_size for i in chosen_indexes)),
            'cumulative_return': round(cumulative_return, 2),
            'payoff': round(payoff, 2),
        }

page_sequence = [
    Intro,
    
    InvestmentSelection, Calibration, Lottery, Result,
    InvestmentSelection, Calibration, Lottery, Result,
    InvestmentSelection, Calibration, Lottery, Result,
    InvestmentSelection, Calibration, Lottery, Result,

    
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,

    
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,

    
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,
    # InvestmentSelection, Calibration, Lottery, LotteryResults, Result,    

    End,
]

