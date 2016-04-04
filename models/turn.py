"""turn.py - This file contains the class definitions for the Datastore
entity Turns. This classes also includes methods 'new_turn', 'set_correct_answer', 
'set_finished', 'used_clue', 'set_anwer_given'  and 'set_points'."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class Turn(ndb.Model):
    """Turn object"""
    game_key = ndb.KeyProperty(required=True, kind='TriviaGame')
    user_key = ndb.KeyProperty(required=True, kind='User')
    question_key = ndb.KeyProperty(required=True, kind='Question')
    given_answer = ndb.TextProperty(required=True, default='')
    clues_used = ndb.IntegerProperty(default=0)
    points = ndb.IntegerProperty(required=True, default=0)
    is_correct = ndb.BooleanProperty(required=True, default=False)
    is_finished = ndb.BooleanProperty(required=True, default=False)

    @classmethod
    def new_turn(cls, game, user, question):
        # Creats a new Turn object
        triviaGameTurn = Turn(game_key=game,
                              user_key=user,
                              question_key=question)
        triviaGameTurn.put()
        return triviaGameTurn

    def set_correct_answer(self):
        self.is_correct = True

    def set_finished(self):
        self.is_finished = True

    def used_clue(self):
        self.clues_used += 1

    def set_points(self, pts):
        self.points = pts

    def set_answer_given(self, answer):
        self.given_answer = answer

