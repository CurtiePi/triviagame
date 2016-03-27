"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()

class TriviaGame(ndb.Model):
    """Trivia Game object"""
    rounds_remaining = ndb.IntegerProperty(required=True, default=5)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    question_pool = ndb.KeyProperty(kind='Question', repeated=True)
    turn_keys = ndb.KeyProperty(kind='Turn', repeated=True)
    current_question = ndb.KeyProperty(kind='Question')

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
        score = Score.query().filter(Score.user==self.user).get()
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
        self.current_question=question_key
        self.put()
        return removed_key

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

class TriviaGameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    rounds_remaining = messages.IntegerField(2, required=True)
    user_name = messages.StringField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)
    options = messages.StringField(6, repeated=True)

class TriviaGameForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(TriviaGameForm, 1, repeated=True)

class NewTriviaGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    rounds = messages.IntegerField(4, default=5)


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
                                   score = total_score)
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
        #form.urlsafe_key = self.key.urlsafe()
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
        #form.urlsafe_key = self.key.urlsafe()
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
    question= messages.StringField(1, required=True)
    correct = messages.StringField(2, required=True)
    wrong1 = messages.StringField(3, required=True)
    wrong2 = messages.StringField(4, required=True)
    wrong3 = messages.StringField(5, required=True)
    clue1 = messages.StringField(6, required=True)
    clue2 = messages.StringField(7, required=True)

class TriviaQuestionForm(messages.Message):
    """TriviaQuestionForm for Question information"""
    question= messages.StringField(1, required=True)
    answerA = messages.StringField(2, required=True)
    answerB = messages.StringField(3, required=True)
    answerC = messages.StringField(4, required=True)
    answerD = messages.StringField(5, required=True)

class ClueForm(messages.Message):
    """ClueForm for Question information"""
    clue = messages.StringField(1, required=True)

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
        """Creates and returns a new question"""
        triviaGameTurn = Turn(game_key=game,
                              user_key=user,
                              question_key=question)
        triviaGameTurn.put()
        return triviaGameTurn

    def setCorrectAnswer(self):
        self.is_correct = True

    def setFinished(self):
        self.is_finished = True

    def usedClue(self):
        self.clues_used += 1

    def setPoints(self, pts):
        self.points = pts

    def setAnswerGiven(self, answer):
        self.given_answer = answer

class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    score = ndb.IntegerProperty(required=True)
    num_correct = ndb.IntegerProperty(required=True)
    num_incorrect = ndb.IntegerProperty(required=True)
    clues_used = ndb.IntegerProperty(required=True)

    def to_data_form(self):
        return DataForm(user_name=self.user.get().name, score=self.score,
                         correct_ans=self.num_correct,
                         incorrect_ans=self.num_incorrect,
                         clues_used = self.clues_used)

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

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
