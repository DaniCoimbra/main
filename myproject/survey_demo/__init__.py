from otree.api import *


class C(BaseConstants):
    NAME_IN_URL = 'survey_demo'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    risk = models.IntegerField(
        choices=[(i, f'{i}') for i in range(11)],
        widget=widgets.RadioSelectHorizontal
    )


# FUNCTIONS
# PAGES
class RiskSelection(Page):
    form_model = 'player'
    form_fields = ['risk']

class Querie(Page):
    form_model = 'player'


page_sequence = [RiskSelection, Querie]
