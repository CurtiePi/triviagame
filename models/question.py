"""Question.py - This file contains the class definitions for the Datastore
entity Question. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class Question(ndb.Model):
    """Question object"""
    value = ndb.IntegerProperty(required=True, default=5)
    question = ndb.TextProperty(required=True)
    answers = ndb.JsonProperty(required=True)
    clues = ndb.TextProperty(repeated=True)

    @classmethod
    def new_question(cls, quest, ans, hints):
        """Creates and returns a new question"""
        triviaQuestion = Question(question=quest,
                                  answers=ans,
                                  clues=hints)
        triviaQuestion.put()
        return triviaQuestion

    def to_form(self):
        """Returns a QuestionForm representation of the Question"""
        form = QuestionForm()
        form.question = self.question

        ansDict = self.answers
        form.correct = ansDict.pop('correct')
        (form.wrong1, form.wrong2, form.wrong3) = ansDict.values()

        clueDict = self.clues

        (form.clue1, form.clue2) = self.clues
        return form

    def to_trivia_form(self):
        """Returns a QuestionForm representation of the Question"""
        form = TriviaQuestionForm()
        form.question = self.question

        answerlist = list(self.answers.values())
        form.answerA = answerlist[0]
        form.answerB = answerlist[1]
        form.answerC = answerlist[2]
        form.answerD = answerlist[3]

        return form

    def is_correct_answer(self, answer):
        """Returns a boolean if the supplied answer is correct"""
        correctAnswer = self.answers.pop('correct')

        if answer == correctAnswer:
            return True

        return False


class QuestionForm(messages.Message):
    """QuestionForm for Question information"""
    question = messages.StringField(1, required=True)
    correct = messages.StringField(2, required=True)
    wrong1 = messages.StringField(3, required=True)
    wrong2 = messages.StringField(4, required=True)
    wrong3 = messages.StringField(5, required=True)
    clue1 = messages.StringField(6, required=True)
    clue2 = messages.StringField(7, required=True)


class TriviaQuestionForm(messages.Message):
    """TriviaQuestionForm for Question information"""
    question = messages.StringField(1, required=True)
    answerA = messages.StringField(2, required=True)
    answerB = messages.StringField(3, required=True)
    answerC = messages.StringField(4, required=True)
    answerD = messages.StringField(5, required=True)


class ClueForm(messages.Message):
    """ClueForm for Question information"""
    clue = messages.StringField(1, required=True)

