from backend.DB.api import app, db
from backend.DB.api.tables import Threshold, User
from backend.DB.api import queries

from backend.slack import slackbot

db.create_all()
db.init_app(app)
persons = slackbot.get_persons_from_slack()
for person in persons:
    queries.add_user(User(person['username'], person['name'], person['image']))
threshold1 = Threshold('pizza', 50)
threshold2 = Threshold('cake', 42)
queries.add_threshold(threshold1)
queries.add_threshold(threshold2)
