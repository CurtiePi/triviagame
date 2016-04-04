"""string.py - This file contains the class definitions for the Datastore
entity String."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

