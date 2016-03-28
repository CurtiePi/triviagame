# triviagame
TriviaGame is a game application that presents questions to a user to answer
like a regular trivia game.

SETUP

TriviaGame allows anyone to imput trivia questions to be answered later. The
questions are entered using the create_question method, which will be explained
in the API section of the document. 

Each question is made up of the question, 1 correct answer, 3 wrong answers and
2 clues.

Users are registered to play via the create_user method.


HOW TO PLAY
----------

Step 1.

Create a trivia game via the new_trivia_game method. You will be asked to 
enter the name of a registered player, and the number of rounds you wish to 
play. There is one question per round.

When you create the game, you should get an game key which you will use to
continue playing.

Step 2.

Now that you have created the trivia game, you must get the game using the 
get_trivia_game method which expects the game key as an input parameter.

Once you get the game you will be presented with your first question.

Step 3a.

Now the game has started, you use the take_turn method to answer the question
presented to you. This method also expects the game key an input parameter as
well as the answer to the question.

Upon entering the answer, you will be informed whether you were correct or not,
and then presented with the next question.

When you have exhausted your allotment of rounds you will be informed that the
game is over.

Step 3b.

If you cannot answer a question immediately, you can opt to use the get_clue
method to get a clue. It also expects the game key as a parameter.

You can use a maximum of 2 clues, after which you will be informed that you are
out of clues

Scoring.

A correct answer is worth a base 5 points. 
A correct answer using one clue is 3 points.
A correct answer using two clues is 1 point.
An incorrect answer is worth 0 points.

You score is an accumulation of all the points you earn answering questions.

AFTER THE GAME

-------------

After you have finished answering the last question you will be presented with
a message saying the game is over and the current score.

You can get a summary of you game using the get_trivia_game_history method,
which takes the game key as an input parameter. There you will see your answers
for each question as well as how many clues were used and points you earned.

You can also get a summary of all the games you have played with the
get_user_trivia_game_summary method.

If you want more detailed game listings you can use the 
get_user_trivia_game_detailed method.

Both of the above methods take the user name as a parameter.

CANCELLING A GAME

-----------------

If you do not wish to finish a game you can cancel it with the
cancel_trivia_game method. Note you can only use this for active games.

OTHER

-----

You can always get your cumulative score with the get_user_score method, which
takes the user name as an input parameter

If you wish to see the high scorers you can use the get_high_scores method,
which requires no parameters.

The rankings can be gotten via the get_rankings method, no parameters necessary.
The rankings are based on score, ratio of correct answers to number of
questions asked and the number of clues used.

API

------

OBJECTS
-------

User

Maintains the users who are registered to play. May have an email associated
but not always.

Fields
 - name:             text
 - email:            text


Question
Stores the questions, possible answers and clues for the game. It has a form
associated with it and its methods populate the forms.

Fields
- value:             integer
- question:          text
- answers:           json
- clues:             text     - repeatable

-- associated forms: QuestionForm, TriviaQuestionForm, ClueForm
-- methods:
  new_question: CLASS METHOD instantiates a new Question object
  to_form : populates QuestionForm
  to_trivia_form: populates TriviaQuestionForm
  is_correct_answer: determines if an answer is the correct answer


TriviaGame
Maintains the status of the TriviaGame by registering Turns and selecting
question for the turn. Also creates a GameSummary object for when the game
ends and clears out game information when the game is cancelled. 
   
Fields
 - rounds_remaining: integer
 - game_over:        boolean
 - user:             key: User
 - question_pool:    key: Question - repeatable
 - turn_keys:        key: Turn     - repeatable
 - current_question: key: Question
 - current_score:    integer

-- associated forms: TriviaGameForm, TriviaGameForms
-- methods:
   new_game: CLASS METHOD  creates a new TriviaGame object
   to_form: populates the TriviaGameForm
   end_game: Updates the game status to over and creates a GameSummary object
   record_score: Tallies a user score across all game. Called by end_game
   get_question_from_pool: selects a Question key from a pool of keys
   remove_question_from_pool: removes a Question key from the pool of keys
   update_current_score: keeps track of the score for the current game
   register_turn: registers a Turn object with the game
   get_latest_turn: getter method for the current turn
   get_current_question: getter method for the current question
   clear_game: removes all information for this TriviaGame


Turn

Repository of all information regarding a turn in the TriviaGame.

Fields
- game_key:          key: TriviaGame
- user_key:          key: User
- question_key:      key: Question
- given_answer:      text
- clues_used:        integer
- points:            integer
- is_correct:        boolean
- is_finished:       boolean

-- associated forms:
-- methods:
   new_turn: CLASS METHOD instantiates a new Turn object
   setCorrectAnswer: sets whether the question was answered correctly or not
   setFinished: sets whether the turn is over (the question has been answered)
   usedClue: increments the number of clues used
   setPoints: sets the points earned this turn
   setAnswerGiven: records the anwser given by the player (correct or not)


GameSummary

Maintains information about a game that has been completed. Primarily
uses Turns objects to populate forms with that information

Fields
 - user:             key: User
 - trivia_game:      key: TriviaGame
 - date:             date
 - turns:            key: Turn     - repeatable
 - score:            integer

-- associated forms: GameSummaryForm, GameDetailForm, GameSummaryForms
                     GameDetailForms
-- methods
   new_game_summary: CLASS METHOD instantiates a new GameSummary object
   to_summary_form: populates a GameSummaryForm
   to_detail_form: populates a GameDetailForm
   aggregate_data: aggregates data over all the Turns object contained in this
                   object.


Score

Maintains the countable information for a user over all games.

Fields
 - user:             key: User
 - score:            integer
 - num_correc:       integer
 - num_incorrect:    integer
 - clues_used:       integer

-- associated forms: ScoreForm, ScoreForms, RankForm, RankForms, DataForm
-- methods
   to_data_form: populates the DataForm with all information
   to_score_form: poputlate the ScoreForm with score information


METHODS
-----------
create_user
- params:
    user_name
    email
- descripion: 
    Creates a user object. Will check if a user with that name already exists
    and raise and exception accordingly.
- response:
    StringMessage

new_triva_game
- params:
    rounds
    user_name
- description:
    Creates a new trivia game with the specified number of rounds for the 
    user identified in the request paramter. The game is a TriviaGame object.
- response:
    TriviaGameForm

get_trivia_game
- params:
    urlsafe_trivia_game_key
- description:
    Retrieves a TriviaGame object based on the urlsafe_trivia_game_key and 
    checks if the game is over. If not it intiates the game by grabbing a
    grabbing a quesiton from the games question pool and creating a Turn
    object. It then registers the turn with the game. In its response it
    presents the first question to be answered.
- response:
    TriviaGameForm

take_turn
- params:
    urlsafe_trivia_game_key
    ans
- description
    Checks if the game is still active and if so checks the answer for the 
    question for correctness against the Question object for this turn. If the
    answer is correct points are awards, factoring in the number of clues used.
    If the answer is incorrect no points are awarded. After the answer is
    checked, a new question os taken from the question pool and a new Turn
    object is created and registered with the game. It response with the game
    status and a new question.
- response:
    TriviaGameForm

get_clue
- params:
    urlsafe_trivia_game_key
- description:
    Retrieves a clue from the current question object stored in the TriviaGame
    object. It checks to see that a clue is only asked for twice, afterwards 
    a message is given that the user has no more clues remaining.
- response:
    StringMessage

create_question
- params:
    question
    correct
    wrong1
    wrong2
    wrong3
    clue1
    clue2
- description:
    Creates a Question object, which is basically a question with 4 possible
    answers, only one of which is correct. The will also contain 2 clues to
    help answer the question.
- response:
    QuestionForm

get_question
- params:
- description:
    Test method to confirm that a Question object was being stored in the
    datastore. May be modified later for a more practical use
- response:
  TriviaQuestionForm

answer_question
- params:
    urlsafe_question_key
    answer
- description:
    Test method to confirm that a Question object could be retireved from the
    datastore and answered. May be modified later for a more practical use.
- response:
  StringMessage

get_trivia_game_history
- params:
    urlsafe_trivia_game_key
- description:
    Retrieves the detailed game history for a completed game. The game is
    retrieved by the urlsafe_trivia_game_key and the information for the game
    is retrieved from the GameSummary object for the game request.
- response:
    GameDetailForms

get_user_trivia_game_summary
- params:
    user_name
- description:
    Retrieves a summary of all of an individual user's games. Displays basic
    information stored in the GameSummary object, such as the score, number of
    clues used and date.
- response:
    GameSummaryForms

get_user_trivia_game_detail
- params:
    user_name
- description:
    Retrieves details of all of an individual user's games. Displays detailed
    information stored in the GameSummary object, such as the question asked,
    the answer given, number of clues used.
- response:
    GameDetailForms

get_user_games
- params:
    user_name
- description:
    Retrieves the active games of the user specified in the request. Checks
    all the game objects for which this user is the key and checks if the game
    is over, if not, it is presented for review
- response:
    TriviaGameForms

cancel_trivia_game
- params:
    urlsafe_trivia_game_key
- description:
    Cancels the trivia game specified in the request parameter. This is done
    by removing the Turn objects associated with this game, then removing the 
    game itself. Will not cancel games that have already been completed.
- respnse:
   StringMessage

get_user_score
- params:
    user_name
- description:
    Retrieves the cumulative score of all games for the user specified in the
    request parameter.
- response:
    ScoreForm

get_high_scores
- params:
- description:
    Retrieves all the score objects for all the users sorted in descending 
    order.
- response:
    ScoreForms

get_rankings
- params:
- description:
    Retrieves all the score objects for all the users sorted in descending 
    order. Then using the information in those objects, specifically score,
    number of correct answers, and number of clues used it determines a 
    player ranking. 10 * (score * correct answers/total questions) - clues_used
    The rankings are then sorted and presented to user.
- response:
    ScoreForms

 _getPlayerReminder  STATIC METHOD
- params:
    TriviaGame
    name
- description:
    Builds out the message body for the cron job task SendReminderEmail.
    Using the TriviaGame object and name it personalizes a message to remind 
    the user they have not finished a game. Also it includes game status info.
- response
   String

_cache_average_correct_per_game  STATIC METHOD
- params:
- description:
    A queued task that calculates the average number of correct answers
    per game as a percentage and stores a string message with the result
    in memcache
- response

CRONS

SendReminderEmail
- description:
   This class's get method is called every hour to check to see what games 
   have not been finished. If it finds the games, and the associated user
   has a registered email address, then an emial is sent to the user to 
   remind them to finish game, along with information on the current status
   of the game

TASKQUEUE

UpdateAverageCorrectPerGame
- description
    This class's post method is called when the get_trivia_game method places
    it on the task queue. It calls the cache_average_correct_per_game method
