from backend.DB.api.routes import app
from backend.DB.api.tables import Threshold, User, db
from backend.DB.api import queries

from backend.slack import slackbot


def main():
    db.init_app(app)
    app.app_context().push()
    db.create_all()
    persons = slackbot.get_persons_from_slack()
    for person in persons:
        queries.add_user(User(person['username'], person['name'], person['image']))
    threshold1 = Threshold('pizza', 50)
    threshold2 = Threshold('cake', 42)

    queries.add_threshold(threshold1)
    queries.add_threshold(threshold2)


if __name__ == '__main__':
    main()
