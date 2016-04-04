"""GameSummary.py - This file contains the class definitions for the Datastore
entity GameSummary. This classes also includes methods 'new_game_summary', 
'to_summary_form', 'to_detail_form' and 'aggregate_data'."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class GameSummary(ndb.Model):
    """Game Summary object"""
    user = ndb.KeyProperty(required=True, kind='User')
    trivia_game = ndb.KeyProperty(required=True, kind='TriviaGame')
    date = ndb.DateProperty(required=True)
    turns = ndb.KeyProperty(kind='Turn', repeated=True)
    score = ndb.IntegerProperty(required=True)

    @classmethod
    def new_game_summary(cls, user, game, date, turns):
        """Creates and returns a new game summary"""

        total_score = 0
        for turn in turns:
            total_score += turn.get().points

        game_summary = GameSummary(user=user,
                                   trivia_game=game,
                                   date=date,
                                   turns=turns,
                                   score=total_score)
        game_summary.put()
        return game_summary

    def to_summary_form(self):
        (score, numCorrect, numIncorrect, clues_used) = self.aggregate_data()

        return GameSummaryForm(user_name=self.user.get().name,
                               date=str(self.date),
                               questions_answered=len(self.turns),
                               correct=numCorrect,
                               incorrect=numIncorrect,
                               clues_used=clues_used,
                               total_score=score)

    def to_detail_form(self):
        detailForms = []

        for turn_key in self.turns:
            turn = turn_key.get()
            question_asked = turn.question_key.get().question
            answer_given = turn.given_answer
            clues_used = turn.clues_used
            if turn.is_correct:
                correct_msg = 'Answered Correctly'
            else:
                correct_msg = 'Answered Incorrectly'
            points_scored = turn.points

            detailForms.append(GameDetailForm(date=str(self.date),
                               question=question_asked,
                               answer=answer_given,
                               clues_used=clues_used,
                               correct=correct_msg,
                               points=points_scored))

        return detailForms

    def aggregate_data(self):
        gameTurns = ndb.get_multi(self.turns)
        score = 0
        numCorrect = 0
        numIncorrect = 0
        clues_used = 0
        for turn in gameTurns:
            score += turn.points
            clues_used += turn.clues_used
            if turn.is_correct:
                numCorrect += 1
            else:
                numIncorrect += 1

        return [score, numCorrect, numIncorrect, clues_used]


class GameSummaryForm(messages.Message):
    """Game Summary Form for outbound game information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    questions_answered = messages.IntegerField(3, required=True)
    correct = messages.IntegerField(4, required=True)
    incorrect = messages.IntegerField(5, required=True)
    clues_used = messages.IntegerField(6, required=True)
    total_score = messages.IntegerField(7, required=True)


class GameSummaryForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(GameSummaryForm, 1, repeated=True)


class GameDetailForm(messages.Message):
    """GameDetailForm for detailed game information"""
    date = messages.StringField(1, required=True)
    question = messages.StringField(2, required=True)
    answer = messages.StringField(3, required=True)
    clues_used = messages.IntegerField(4, required=True, default=0)
    correct = messages.StringField(5, required=True)
    points = messages.IntegerField(6, required=True, default=0)


class GameDetailForms(messages.Message):
    """Return multiple Gaem Detail Forms"""
    user_name = messages.StringField(1, required=True)
    items = messages.MessageField(GameDetailForm, 2, repeated=True)
    total_correct = messages.IntegerField(3, required=True, default=0)
    total_incorrect = messages.IntegerField(4, required=True, default=0)
    total_clues_used = messages.IntegerField(5, required=True, default=0)
    total_points = messages.IntegerField(6, required=True, default=0)

