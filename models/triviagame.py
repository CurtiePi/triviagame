"""TriviaGame.py - This file contains the class definitions for the Datastore
entity TriviaGame. This class also includes methods 'new_game', 'to_form',
'end_game', 'record_score', 'get_question_from_pool',
'remove_question_from_pool', 'update_current_score', 'get_latest_turn',
'register_turn', 'get_current_question', and 'clear_game' ."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from question import Question
from gamesummary import GameSummary
from score import Score


class TriviaGame(ndb.Model):
    """Trivia Game object"""
    rounds_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    question_pool = ndb.KeyProperty(kind='Question', repeated=True)
    turn_keys = ndb.KeyProperty(kind='Turn', repeated=True)
    current_question = ndb.KeyProperty(kind='Question')
    current_score = ndb.IntegerProperty(required=True, default=0)

    @classmethod
    def new_game(cls, user, game_rounds):
        """Creates and returns a new game"""

        q = Question.query()
        questions = q.fetch()
        questionKeys = [question.key for question in questions]

        turnKeys = []

        game = TriviaGame(user=user,
                          rounds_remaining=game_rounds,
                          question_pool=questionKeys,
                          turn_keys=turnKeys,
                          game_over=False)
        game.put()
        return game

    def to_form(self, message=None, options=None):
        """Returns a TriviaGameForm representation of the TriviaGame"""
        form = TriviaGameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.rounds_remaining = self.rounds_remaining
        form.current_score = self.current_score
        form.game_over = self.game_over
        form.message = message
        if options:
            form.options = options
        return form

    def end_game(self):
        """Ends the game."""
        self.game_over = True
        self.put()
        # Add the game to the game summary
        game_summary = GameSummary.new_game_summary(self.user,
                                                    self.key,
                                                    date.today(),
                                                    self.turn_keys)
        aggregates = game_summary.aggregate_data()

        self.record_score(aggregates)
        return game_summary

    def record_score(self, aggregate_data):
        score = Score.query().filter(Score.user == self.user).get()
        if score:
            score.score += aggregate_data[0]
            score.num_correct += aggregate_data[1]
            score.num_incorrect += aggregate_data[2]
            score.clues_used += aggregate_data[3]
        else:
            score = Score(user=self.user,
                          score=aggregate_data[0],
                          num_correct=aggregate_data[1],
                          num_incorrect=aggregate_data[2],
                          clues_used=aggregate_data[3])

        score.put()
        return score

    def get_question_from_pool(self):
        """Supply a question key at random from the pool"""
        if len(self.question_pool) == 0:
            return None

        return random.choice(self.question_pool)

    def remove_question_from_pool(self, question_key):
        """Supply a question key at random from the pool"""
        if len(self.question_pool) == 0:
            return None

        removed_key = self.question_pool.remove(question_key)
        self.current_question = question_key
        self.put()
        return removed_key

    def update_current_score(self, points):
        self.current_score += points

    def register_turn(self, turn_key):
        self.turn_keys.append(turn_key)
        self.put()

    def get_latest_turn(self):
        return self.turn_keys[-1]

    def get_current_question(self):
        return self.current_question

    def clear_game(self):
        for turn in self.turn_keys:
            turn.delete()
        self.game_over = True


class TriviaGameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    rounds_remaining = messages.IntegerField(2, required=True)
    current_score = messages.IntegerField(3, required=True)
    user_name = messages.StringField(4, required=True)
    game_over = messages.BooleanField(5, required=True)
    message = messages.StringField(6, required=True)
    options = messages.StringField(7, repeated=True)


class TriviaGameForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(TriviaGameForm, 1, repeated=True)


class NewTriviaGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    rounds = messages.IntegerField(4, default=5)

