"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""

import logging
import endpoints
from protorpc import remote, messages, message_types
from google.appengine.api import memcache
from google.appengine.api import taskqueue


from models import User, Question, Turn, TriviaGame, GameSummary, Score

from models import QuestionForm, TriviaQuestionForm, ClueForm, TriviaGameForm,\
    NewTriviaGameForm, GameSummaryForm, GameSummaryForms, GameDetailForm, \
    GameDetailForms, TriviaGameForms, DataForm, ScoreForm, ScoreForms, \
    RankForm, RankForms, StringMessage

from utils import get_by_urlsafe, getFirstKey

NEW_TRIVIA_GAME_REQUEST = endpoints.ResourceContainer(NewTriviaGameForm)

GET_TRIVIA_GAME_REQUEST = endpoints.ResourceContainer(
        urlsafe_trivia_game_key=messages.StringField(1),)

NEW_QUESTION_REQUEST = endpoints.ResourceContainer(QuestionForm)

GET_QUESTION_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,)

GENERIC_GET_REQUEST = endpoints.ResourceContainer(
    message_types.VoidMessage,)

HI_SCORE_GET_REQUEST = endpoints.ResourceContainer(
    result_num=messages.IntegerField(1, required=False, default=0),)

TAKE_TURN_REQUEST = endpoints.ResourceContainer(
    urlsafe_trivia_game_key=messages.StringField(1),
    ans=messages.StringField(2),)

GET_CLUE_REQUEST = endpoints.ResourceContainer(
        urlsafe_trivia_game_key=messages.StringField(1),)

ANSWER_QUESTION_REQUEST = endpoints.ResourceContainer(
    urlsafe_question_key=messages.StringField(1),
    answer=messages.StringField(2),)

USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))

MEMCACHE_CORRECT_ANSWER_AVERAGE = 'CORRECT_ANSWER_AVERAGE'


@endpoints.api(name='trivia', version='v1')
class TriviaApi(remote.Service):
    """Trivia API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()

        # Create an associated Score for this user

        score = Score(user=user.key)
        score.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @staticmethod
    def _getPlayerReminder(game, name):

        clues_used = game.get_latest_turn().get().clues_used

        q_key = game.get_current_question()
        question = q_key.get()
        (ansA, ansB, ansC, ansD) = list(question.answers.values())

        body = "Hi {},\n".format(name)
        body += "You started a trivia game, but you haven't "
        body += "answered a quesion in over an hour.\n"
        body += "Why not come back and try to finish your "
        body += "game, you can always ask for a clue "
        body += "if you need one.\n"
        body += "If you really don't want to finish, you "
        body += "can cancel. \n"

        body += "Here is where your game stands: "
        body += "Question: {}".format(question.question)
        body += "A.{}\nB.{}\nC.{}\nD.{}\n".format(ansA, ansB, ansC, ansD)
        body += "You have used {} clues\n".format(clues_used)
        body += "You have {} more questions\n".format(game.rounds_remaining)

        return body

    @staticmethod
    def _cache_average_correct_per_game():
        """Populates memcache with the average correct answers per game"""
        games = TriviaGame.query(TriviaGame.game_over == True).fetch()
        if games:
            correct_count = 0
            count = len(games)
            for game in games:
                turns = game.turn_keys
                total_correct_answers = sum([turn.get().is_correct
                                            for turn in turns])
            average = float(total_correct_answers)/count
            memcache.set(MEMCACHE_CORRECT_ANSWER_AVERAGE,
                         'Average correct answer      \
                         per game: {:.2f}'.format(average))

    @endpoints.method(request_message=NEW_TRIVIA_GAME_REQUEST,
                      response_message=TriviaGameForm,
                      path='triviagame',
                      name='new_trivia_game',
                      http_method='POST')
    def new_triva_game(self, request):
        """Creates new trivia game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        game = TriviaGame.new_game(user.key, request.rounds)

        # Use a task queue to update the average correct answers per game.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_correct_per_game')

        return game.to_form('Good luck playing the Trivia Game!')

    @endpoints.method(request_message=GET_TRIVIA_GAME_REQUEST,
                      response_message=TriviaGameForm,
                      path='triviagame/{urlsafe_trivia_game_key}',
                      name='get_trivia_game',
                      http_method='GET')
    def get_trivia_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_trivia_game_key, TriviaGame)
        if game:
            user_key = game.user
            question_key = game.get_question_from_pool()

            if question_key:
                if len(game.turn_keys) == 0:
                    # Create a new turn
                    turn = Turn.new_turn(game.key, user_key, question_key)
                    game.remove_question_from_pool(question_key)
                    game.register_turn(turn.key)

                # Get a question object
                question = get_by_urlsafe(question_key.urlsafe(), Question)
                return game.to_form(question.question,
                                    question.answers.values())
            else:
                game.clear_game()
                g_form = game.to_form('No available questions, Game aborted!')
                game.key.delete()
                return g_form
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=TAKE_TURN_REQUEST,
                      response_message=TriviaGameForm,
                      path='triviagame/{urlsafe_trivia_game_key}/answer/{ans}',
                      name='take_turn',
                      http_method='PUT')
    def take_turn(self, request):
        """ Take turn by answering a question in the triviagame"""
        # Get the game in question
        game = get_by_urlsafe(request.urlsafe_trivia_game_key, TriviaGame)

        if game.game_over:
            return game.to_form('Game already over!')

        game.rounds_remaining -= 1

        turn_key = game.get_latest_turn()
        turn = get_by_urlsafe(turn_key.urlsafe(), Turn)

        question = get_by_urlsafe(turn.question_key.urlsafe(), Question)

        if question.is_correct_answer(request.ans):
            result = "You are correct. "
            turn.set_correct_answer()
            points = question.value
            if turn.clues_used != 0:
                points -= 2**turn.clues_used

            turn.set_points(points)
            game.update_current_score(points)
        else:
            result = "You are not correct. "

        turn.set_answer_given(request.ans)
        turn.set_finished()
        turn.put()

        if game.rounds_remaining < 1:
            game.end_game()
            return game.to_form(result + ' Game over!')
        else:
            user_key = game.user
            question_key = game.get_question_from_pool()
            if question_key:
                # Create a new turn
                turn = Turn.new_turn(game.key, user_key, question_key)
                game.remove_question_from_pool(question_key)
                game.register_turn(turn.key)

                # Get a question object
                question = get_by_urlsafe(question_key.urlsafe(), Question)
                game.put()
                message = result + question.question
                return game.to_form(message, question.answers.values())
            else:
                game.end_game()
                return game.to_form(result + ' No more questions, Game Over!')

    @endpoints.method(request_message=NEW_QUESTION_REQUEST,
                      response_message=QuestionForm,
                      path='question/create',
                      name='create_question',
                      http_method='POST')
    def create_question(self, request):
        """Creates a question that can be used in the trivia game"""

        question = request.question
        answers = {'correct': request.correct,
                   'wrong1': request.wrong1,
                   'wrong2': request.wrong2,
                   'wrong3': request.wrong3}

        clues = [request.clue1, request.clue2]

        newQuestion = Question.new_question(question, answers, clues)

        return newQuestion.to_form()

    @endpoints.method(request_message=GET_CLUE_REQUEST,
                      response_message=StringMessage,
                      path='triviagame/{urlsafe_trivia_game_key}/clue',
                      name='get_clue',
                      http_method='GET')
    def get_clue(self, request):
        """Retrieve a clue for a question."""
        game = get_by_urlsafe(request.urlsafe_trivia_game_key, TriviaGame)
        if game:
            if game.game_over:
                return StringMessage(message='Game already over!')

            turn_key = game.get_latest_turn()
            turn = get_by_urlsafe(turn_key.urlsafe(), Turn)

            question = get_by_urlsafe(turn.question_key.urlsafe(), Question)
            if turn.clues_used < 2:
                clue = question.clues[turn.clues_used]
                turn.used_clue()
                turn.put()
            else:
                clue = 'You have used up all of your clues!'

            return StringMessage(message=clue)

        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_QUESTION_REQUEST,
                      response_message=TriviaQuestionForm,
                      path='question/retrieve',
                      name='get_question',
                      http_method='GET')
    def get_question(self, request):
        """Retrieve a question."""
        q = Question.query()
        question = q.get()

        if question:
            return question.to_trivia_form()
        else:
            raise endpoints.NotFoundException('No question not found!')

    @endpoints.method(request_message=ANSWER_QUESTION_REQUEST,
                      response_message=StringMessage,
                      path='question/{urlsafe_question_key}/answer/{answer}',
                      name='answer_question',
                      http_method='POST')
    def answer_question(self, request):
        """Answer a question and check correctness"""
        wsqk = request.urlsafe_question_key
        question = get_by_urlsafe(wsqk, Question)

        if question.is_correct_answer(request.answer):
            result = "is correct."
        else:
            result = "is not correct."

        return StringMessage(message='Your answer to {} {}!'.format(
                question.question, result))

    @endpoints.method(request_message=GET_TRIVIA_GAME_REQUEST,
                      response_message=GameDetailForms,
                      path='triviagame/{urlsafe_trivia_game_key}/details',
                      name='get_trivia_game_history',
                      http_method='GET')
    def get_trivia_game_history(self, request):
        """Retrieve the history for one completed game"""
        game = get_by_urlsafe(request.urlsafe_trivia_game_key, TriviaGame)
        if game:
            q = GameSummary.query()
            game_summary = q.filter(GameSummary.trivia_game == game.key).get()

            if game_summary:
                aggregates = game_summary.aggregate_data()

                return GameDetailForms(user_name=game_summary.user.get().name,
                                       items=game_summary.to_detail_form(),
                                       total_correct=aggregates[1],
                                       total_incorrect=aggregates[2],
                                       total_clues_used=aggregates[3],
                                       total_points=aggregates[0])

            else:
                raise endpoints.NotFoundException('Game not found!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameSummaryForms,
                      path='triviagame/user/{user_name}/summary',
                      name='get_user_trivia_game_summary',
                      http_method='GET')
    def get_user_trivia_game_summary(self, request):
        """Returns a summary of an individual User's games. This
           includes the user name, date, number of questions answered,
           number answered correctly and incorrectly, the number of clues
           used and the total score for the game."""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        sums = GameSummary.query(GameSummary.user == user.key)
        return GameSummaryForms(items=[smy.to_summary_form() for smy in sums])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GameDetailForms,
                      path='triviagame/user/{user_name}/detail',
                      name='get_user_trivia_game_detail',
                      http_method='GET')
    def get_user_trivia_game_detail(self, request):
        """Returns a detailed listing of an individual User's games. This
           includes all questions for each game, the given answer for each
           question, whether the given answer correct or not, how many clues
           were used to answer each question, how many points were awarded
           for each question and the date for the question. """
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        items = []
        data = [0, 0, 0, 0]
        summaries = GameSummary.query(GameSummary.user == user.key)
        for summary in summaries:
            items.extend(summary.to_detail_form())
            data = [x + y for x, y in zip(data, summary.aggregate_data())]

        return GameDetailForms(user_name=user.name, items=items,
                               total_correct=data[1],
                               total_incorrect=data[2],
                               total_clues_used=data[3],
                               total_points=data[0])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=TriviaGameForms,
                      path='triviagame/user/{user_name}/active',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Returns the active games of a user"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')

        games = TriviaGame.query()                        \
            .filter(TriviaGame.user == user.key)     \
            .filter(TriviaGame.game_over == False).fetch()

        items = []
        for game in games:
            question = game.get_current_question().get()
            question_asked = question.question
            answers = question.answers.values()

            items.append(game.to_form(question_asked, answers))

        return TriviaGameForms(items=items)

    @endpoints.method(request_message=GET_TRIVIA_GAME_REQUEST,
                      response_message=StringMessage,
                      path='triviagame/{urlsafe_trivia_game_key}/cancel',
                      name='cancel_trivia_game',
                      http_method='DELETE')
    def cancel_trivia_game(self, request):
        """Cancel an active game."""
        game = get_by_urlsafe(request.urlsafe_trivia_game_key, TriviaGame)
        if game:
            if game.game_over:
                return StringMessage(message='Game is over, cannot cancel!')

            game.clear_game()
            game.key.delete()

            return StringMessage(message='Game cancelled!')

        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForm,
                      path='scores/user/{user_name}',
                      name='get_user_score',
                      http_method='GET')
    def get_user_score(self, request):
        """Returns an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        score = Score.query(Score.user == user.key).get()
        if score:
            return score.to_score_form()
        else:
            raise endpoints.NotFoundException('Score not found!')

    @endpoints.method(request_message=HI_SCORE_GET_REQUEST,
                      response_message=ScoreForms,
                      path='scores/highscores/{result_num}',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Retrieve the high scores to date."""
        sq = Score.query().order(-Score.score)

        if request.result_num > 0:
            scores = sq.fetch(limit=request.result_num)
        else:
            scores = sq.fetch()

        return ScoreForms(items=[score.to_score_form() for score in scores])

    @endpoints.method(request_message=GENERIC_GET_REQUEST,
                      response_message=RankForms,
                      path='user/rankings',
                      name='get_rankings',
                      http_method='GET')
    def get_rankings(self, request):
        """Retrieve the user rankings to date."""
        s = Score.query()
        scores = s.order(-Score.score).order(Score.clues_used).fetch()

        ranks = []
        for score in scores:
            name = score.user.get().name
            denominator = float(score.num_correct + score.num_incorrect)
            factor = score.num_correct/denominator
            rank = round((10 * score.score * factor)) - score.clues_used
            tup = (name, rank)
            ranks.append(tup)

        ranks = sorted(ranks, reverse=True, key=getFirstKey)

        rankings = [RankForm(name=rank[0], ranking=rank[1]) for rank in ranks]

        return RankForms(items=rankings)


api = endpoints.api_server([TriviaApi])

