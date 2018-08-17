from backend.DB.api import queries
from backend.DB.api.tables import db
from flask import jsonify, request, abort, render_template, Flask
import os
from flask_apscheduler import APScheduler

from backend.DB.api.tables import User, Pair, Reward, Threshold
from backend.slack import slackbot


def update_users():
    with app.app_context():
        users = queries.get_all_users()
        active_users = queries.get_active_users()
        slack_users = slackbot.get_persons_from_slack()
        # update and add users from slack
        for slack_user in slack_users:
            if not any(user.username == slack_user['username'] for user in users):
                queries.add_user(User(slack_user['username'], slack_user['name'], slack_user['image']))
            else:
                user = User(slack_user['username'], slack_user['name'], slack_user['image'])
                user.active = True
                queries.update_user(user)
        #set users to inactive if they are not present in slack users
        for user in active_users:
            if not any(user.username == u['username'] for u in slack_users):
                user.active = False
                queries.update_user(user)


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}'.format(
    os.environ.get('POSTGRES_USERNAME'), os.environ.get('POSTGRES_PASSWORD'), os.environ.get('POSTGRES_HOSTNAME'))
app.config['SECRET_KEY'] = os.environ.get('BT_TOKEN')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JOBS'] = [{
    'id': 'user-update',
    'replace_existing': True,
    'func': update_users,
    'trigger': 'interval',
    'hours': 2,
}]
app.config['SCHEDULER_API_ENABLED'] = True


@app.before_request
def verify_token():
    if app.config['SECRET_KEY'] is None:
        abort(403)
    token = request.args.get('token')
    if token is None:
        abort(403)
    if token != app.config['SECRET_KEY']:
        abort(403)


@app.route('/')
def graph_display():
    token = request.args.get('token')
    return render_template('graph_display.html', token=token)


def format_users(users):
    output = []
    for user in users:
        output.append(
            {'username': user.username, 'name': user.name,
             'image': user.image, 'active': user.active})
    return jsonify(output)


@app.route('/api/reward/progress')
def status_data():
    status = {"cake_count": len(queries.get_pairs_since_last_used_reward("cake")),
              "pizza_count": len(queries.get_pairs_since_last_used_reward("pizza")),
              "pizza_thres": queries.get_threshold("pizza").threshold,
              "cake_thres": queries.get_threshold("cake").threshold,
              }
    pairs = queries.get_pair_history()
    if len(pairs) > 0:
        last_pair = pairs[-1]
        status['last_pair'] = [last_pair.person1, last_pair.person2]
    return jsonify(status)


@app.route('/api/user/all', methods=['GET'])
def get_all_users():
    users = queries.get_all_users()
    return format_users(users)


@app.route('/api/user/active', methods=['GET'])
def get_active_users():
    users = queries.get_active_users()
    return format_users(users)


@app.route('/api/user/delete/<username>', methods=['DELETE'])
def delete_user(username):
    user = queries.get_user_by_username(username)
    if user is None:
        abort(400)
    if queries.delete_user(user.username):
        return jsonify({'message': user.username + ' deleted'})
    abort(400)


def format_pairs(pairs):
    output = []
    for pair in pairs:
        user_data = {'person1': pair.person1, 'person2': pair.person2, 'date': pair.date}
        output.append(user_data)
    return output


@app.route('/api/pair/add', methods=['POST'])
def add_pair():
    pair_json = request.get_json()

    if pair_json is None:
        abort(400)
    if all(k not in pair_json.keys() for k in ('person1', 'person2')):
        abort(400)

    if 'date' not in pair_json:
        pair = Pair(pair_json['person1'], pair_json['person2'])
        queries.add_pair(pair)
        check_for_reward()
        return jsonify({'person1': pair.person1, 'person2': pair.person2, 'date': pair.date})
    pair = Pair(pair_json['person1'], pair_json['person2'], pair_json['date'])
    queries.add_pair(pair)
    check_for_reward()

    return jsonify(format_pairs([pair])[0])


def check_for_reward():
    thresholds = queries.get_all_thresholds()
    for t in thresholds:
        if t.threshold <= len(queries.get_pairs_since_last_reward(t.reward_type)):
            queries.add_reward(Reward(t.reward_type))


@app.route('/api/pair/all', methods=['GET'])
def get_all_pairs():
    pairs = queries.get_pair_history()
    output = format_pairs(pairs)
    return jsonify(output)


@app.route('/api/pair/all/after_date/<date>', methods=['GET'])
def get_pairs_since_date(date):
    pairs = queries.get_pairs_from_date(date)
    return jsonify({'pairs': format_pairs(pairs)})


@app.route('/api/pair/all/after_last_reward/<reward_type>', methods=['GET'])
def get_pairs_since_last_used_reward(reward_type):
    pairs = queries.get_pairs_since_last_used_reward(reward_type)
    return jsonify(format_pairs(pairs))


@app.route('/api/pair/count_pair/<date>', methods=['GET'])
def get_pair_count_between_all_users(date):
    counters = queries.get_pair_counts_between_all_users(date)
    return jsonify(counters)


def format_rewards(rewards):
    output = []
    for reward in rewards:
        output.append({'reward_type': reward.reward_type,
                       'date': reward.date, 'used_reward': reward.used_reward})
    return jsonify(output)


@app.route('/api/reward/all', methods=['GET'])
def get_all_rewards():
    rewards = queries.get_rewards()
    return format_rewards(rewards)


@app.route('/api/reward/use/<reward_type>', methods=['PUT'])
def use_reward(reward_type):
    return format_rewards([queries.use_reward(reward_type)])


@app.route('/api/threshold/add', methods=['POST'])
def add_threshold():
    thres_json = request.get_json()

    if thres_json is None:
        abort(400)
    if all(k not in thres_json.keys() for k in ('reward_type', 'threshold')):
        abort(400)

    threshold = Threshold(thres_json['reward_type'], thres_json['threshold'])
    queries.add_threshold(threshold)
    return jsonify([{'reward_type': threshold.reward_type, 'threshold': threshold.threshold}])


@app.route('/api/threshold/update/<reward_type>/<threshold>', methods=['PUT'])
def update_threshold(reward_type, threshold):
    thresh = queries.get_threshold(reward_type)
    thresh.threshold = threshold
    queries.update_threshold(thresh)
    return jsonify({'reward_type': thresh.reward_type, 'threshold': thresh.threshold})


def set_up_db():
    # db.drop_all()
    db.create_all()
    update_users()
    threshold1 = Threshold('pizza', 13)
    threshold2 = Threshold('cake', 7)

    queries.add_threshold(threshold1)
    queries.add_threshold(threshold2)


if __name__ == '__main__':
    app.app_context().push()
    db.init_app(app)
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    set_up_db()
    app.run(host='0.0.0.0', port=80)
