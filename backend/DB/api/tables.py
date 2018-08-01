import time

from sqlalchemy import ForeignKey
import math

from sqlalchemy.orm import relationship

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.engine import Engine
from sqlalchemy import event


db = SQLAlchemy()


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class User(db.Model):
    username = db.Column('user_name', db.String, primary_key=True)
    name = db.Column('name', db.String)
    active = db.Column('active', db.Integer)
    image = db.Column('image', db.String)

    def __init__(self, username, name, image='unknown'):
        self.username = username
        self.name = name
        self.image = image
        self.active = True


class Pair(db.Model):
    date = db.Column(db.Integer, primary_key=True)
    person1 = db.Column(db.String, ForeignKey(User.username))
    person2 = db.Column(db.String, ForeignKey(User.username))
    user1 = relationship("User", cascade="all,delete", foreign_keys=[person1])
    user2 = relationship("User", cascade="all,delete", foreign_keys=[person2])

    def __eq__(self, other):
        return ((self.person1 == other.person1 and self.person2 == other.person2) or
                (self.person1 == other.person2 and self.person2 == other.person1))

    def __init__(self, person1, person2, date=None):
        if date is None:
            # Pair class requires integer date, not float.
            # Use ms not s to round off to avoid conflicts on primary key
            self.date = math.floor(time.time() * 1000)
        else:
            self.date = date
        self.person1 = person1
        self.person2 = person2


class Threshold(db.Model):
    reward_type = db.Column(db.String, primary_key=True)
    threshold = db.Column(db.Integer)

    def __init__(self, reward_type, threshold):
        self.reward_type = reward_type
        self.threshold = threshold


class Reward(db.Model):
    date = db.Column(db.Integer, primary_key=True)
    reward_type = db.Column(db.String)
    used_reward = db.Column(db.Integer)

    def __init__(self, reward_type, date=None):
        if not date:
            # Pair class requires integer date, not float.
            # Use ms not s to round off to avoid conflicts on primary key
            self.date = math.floor(time.time() * 1000)
        else:
            self.date = date
        self.reward_type = reward_type
        self.used_reward = False
