#!/usr/bin/env python

"""main.py - This file contains handlers that are called by taskqueue and/or
cronjobs."""
import logging

import webapp2
from google.appengine.api import mail, app_identity
from api import TriviaApi

from models import User


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email about games.
        Called every hour using a cron job"""
        app_id = app_identity.get_application_id()
        users = User.query(User.email != None)
        games = TriviaGame.query(TriviaGame.game_over == False)
        for game in games:
            user = game.user.get()
            if user.email != None:
                subject = 'A freindly reminder!'
                body = TriviaApi._getPlayerReminder(game, user.name)
                # This will send test emails, the arguments to send_mail are:
                # from, to, subject, body
                mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                               user.email,
                               subject,
                               body)


class UpdateAverageCorrectPerGame(webapp2.RequestHandler):
    def post(self):
        """Update game average coorect in memcache."""
        TriviaApi._cache_average_correct_per_game()
        self.response.set_status(204)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
    ('/tasks/cache_average_correct_per_game', UpdateAverageCorrectPerGame),
], debug=True)
