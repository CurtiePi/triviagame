"""Score.py - This file contains the class definitions for the Datastore
entity Score. This class also includes methods 'to_data_form' and
'to_score_form'."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    score = ndb.IntegerProperty(required=True, default=0)
    num_correct = ndb.IntegerProperty(required=True, default=0)
    num_incorrect = ndb.IntegerProperty(required=True, default=0)
    clues_used = ndb.IntegerProperty(required=True, default=0)

    def to_data_form(self):
        return DataForm(user_name=self.user.get().name, score=self.score,
                        correct_ans=self.num_correct,
                        incorrect_ans=self.num_incorrect,
                        clues_used=self.clues_used)

    def to_score_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         score=self.score)


class DataForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)
    correct_ans = messages.IntegerField(3, required=True)
    incorrect_ans = messages.IntegerField(4, required=True)
    clues_used = messages.IntegerField(5, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    score = messages.IntegerField(2, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class RankForm(messages.Message):
    """ScoreForm for outbound Score information"""
    name = messages.StringField(1, required=True)
    ranking = messages.FloatField(2, required=True)


class RankForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(RankForm, 1, repeated=True)

