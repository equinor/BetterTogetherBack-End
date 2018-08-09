from backend.DB.api import queries
from backend.DB.api.tables import db
from flask import jsonify, request, abort, render_template, Flask
import os

from backend.DB.api.tables import User, Pair, Reward, Threshold
from backend.slack import slackbot

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://{}:{}@{}'.format(
    os.environ.get('POSTGRES_USERNAME'), os.environ.get('POSTGRES_PASSWORD'), os.environ.get('POSTGRES_HOSTNAME'))
app.config['SECRET_KEY'] = os.environ.get('BT_TOKEN')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


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
    status = {"cake_count": len(queries.get_pairs_since_last_reward("cake")),
              "pizza_count": len(queries.get_pairs_since_last_reward("pizza")),
              "pizza_thres": queries.get_threshold("pizza").threshold,
              "cake_thres": queries.get_threshold("cake").threshold,
              "unused_cake": queries.get_unused_rewards_count_by_type("cake"),
              "unused_pizza": queries.get_unused_rewards_count_by_type("pizza"),
              }
    pairs = queries.get_pair_history()
    if len(pairs) > 0:
        last_pair = pairs[-1]
        status['last_pair'] = [last_pair.person1, last_pair.person2]
    return jsonify(status)


@app.route('/api/user/add', methods=['POST'])
def add_user():
    user_json = request.get_json()

    if user_json is None:
        abort(400)
    if all(k not in user_json.keys() for k in ('username', 'name')):
        abort(400)

    username = user_json['username']
    name = user_json['name']
    user = User(username, name)
    queries.add_user(user)
    return format_users([user])


@app.route('/api/user/all', methods=['GET'])
def get_all_users():
    users = queries.get_all_users()
    return format_users(users)


@app.route('/api/user/active', methods=['GET'])
def get_active_users():
    users = queries.get_active_users()
    return format_users(users)


@app.route('/api/user/get/<username>', methods=['GET'])
def get_user(username):
    user = queries.get_user_by_username(username)
    return format_users([user])


@app.route('/api/user/update', methods=['PUT'])
def update_user():
    user_json = request.get_json()

    if user_json is None:
        abort(400)
    if all(k not in user_json.keys() for k in ('username', 'name', 'active')):
        abort(400)

    user = queries.get_user_by_username(user_json['username'])
    if user is None:
        abort(400)

    user.name = user_json['name']
    user.active = user_json['active']
    queries.update_user(user)
    return format_users([user])


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
        if t.threshold == len(queries.get_pairs_since_last_reward(t.reward_type)):
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


@app.route('/api/pair/with_user/<username>', methods=['GET'])
def get_pairs_with_user(username):
    pairs = queries.get_pairs_containing_user(username)
    return jsonify({'pairs': format_pairs(pairs)})


@app.route('/api/pair/all/after_last_reward/<reward_type>', methods=['GET'])
def get_pairs_since_last_reward(reward_type):
    pairs = queries.get_pairs_since_last_reward(reward_type)
    return jsonify(format_pairs(pairs))


@app.route('/api/pair/count_pair', methods=['GET'])
def get_pair_count_between_all_users():
    counters = queries.get_pair_counts_between_all_users()
    return jsonify(counters)


@app.route('/api/pair/at_date/get/<date>', methods=['GET'])
def get_pair(date):
    return jsonify(format_pairs([queries.get_pair(date)])[0])


@app.route('/api/pair/at_date/update/<date>', methods=['PUT'])
def update_pair(date):
    pair_json = request.get_json()

    if pair_json is None:
        abort(400)
    if all(k not in pair_json.keys() for k in ('person1', 'person2')):
        abort(400)

    pair = [Pair(pair_json['person1'], pair_json['person2'], date)]
    queries.update_pair(pair[0])
    return jsonify(format_pairs(pair)[0])


def format_rewards(rewards):
    output = []
    for reward in rewards:
        output.append({'reward_type': reward.reward_type,
                       'date': reward.date, 'used_reward': reward.used_reward})
    return jsonify(output)


@app.route('/api/reward/add', methods=['POST'])
def add_reward():
    reward_json = request.get_json()

    if reward_json is None or 'reward_type' not in reward_json:
        abort(400)

    if 'date' not in reward_json:
        reward = Reward(reward_json['reward_type'].lower())
    else:
        reward = Reward(reward_json['reward_type'].lower(), reward_json['date'])
    if 'used_reward' in reward_json:
        reward.used_reward = reward_json['used_reward']
    queries.add_reward(reward)
    return format_rewards([reward])


@app.route('/api/reward/all', methods=['GET'])
def get_all_rewards():
    rewards = queries.get_rewards()
    return format_rewards(rewards)


@app.route('/api/reward/unused/<reward_type>', methods=['GET'])
def get_unused_reward_count(reward_type):
    count = queries.get_unused_rewards_count_by_type(reward_type.lower())
    return jsonify(count)


@app.route('/api/reward/unused/earliest/<reward_type>', methods=['GET'])
def get_earliest_unused_reward(reward_type):
    return format_rewards([queries.get_earliest_unused_reward(reward_type)])


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


@app.route('/api/threshold/get/<reward_type>', methods=['GET'])
def get_threshold(reward_type):
    threshold = queries.get_threshold(reward_type)
    if threshold is None:
        return jsonify([])
    return jsonify([{'reward_type': threshold.reward_type, 'threshold': threshold.threshold}])


@app.route('/api/threshold/update/<reward_type>', methods=['PUT'])
def update_threshold(reward_type):
    thres_json = request.get_json()

    if thres_json is None or 'threshold' not in thres_json:
        abort(400)

    threshold = queries.get_threshold(reward_type)
    threshold.threshold = thres_json['threshold']
    queries.update_threshold(threshold)
    return jsonify({'reward_type': threshold.reward_type, 'threshold': threshold.threshold})


def set_up_db():
    app.app_context().push()
    db.init_app(app)
    db.create_all()
    persons = slackbot.get_persons_from_slack()
    for person in persons:
        queries.add_user(User(person['username'], person['name'], person['image']))
    threshold1 = Threshold('pizza', 50)
    threshold2 = Threshold('cake', 42)

    queries.add_threshold(threshold1)
    queries.add_threshold(threshold2)


if __name__ == '__main__':
    set_up_db()
    app.run(host='0.0.0.0', port=80)
