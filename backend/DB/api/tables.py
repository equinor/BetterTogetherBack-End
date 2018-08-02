import math
import time

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()


class User(db.Model):
    username = db.Column('user_name', db.String, primary_key=True)
    name = db.Column('name', db.String)
    active = db.Column('active', db.Boolean)
    image = db.Column('image', db.String)
    first = relationship('Pair', backref='first', foreign_keys='Pair.person1')
    second = relationship('Pair', backref='second', foreign_keys='Pair.person2')

    def __init__(self, username, name, image='unknown'):
        self.username = username
        self.name = name
        self.image = image
        self.active = True


class Pair(db.Model):
    date = db.Column(db.BigInteger, primary_key=True)
    person1 = db.Column(db.String, ForeignKey('user.user_name'), nullable=True)
    person2 = db.Column(db.String, ForeignKey('user.user_name'), nullable=True)

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
    date = db.Column(db.BigInteger, primary_key=True)
    reward_type = db.Column(db.String)
    used_reward = db.Column(db.Boolean)

    def __init__(self, reward_type, date=None):
        if not date:
            # Pair class requires integer date, not float.
            # Use ms not s to round off to avoid conflicts on primary key
            self.date = math.floor(time.time() * 1000)
        else:
            self.date = date
        self.reward_type = reward_type
        self.used_reward = False
