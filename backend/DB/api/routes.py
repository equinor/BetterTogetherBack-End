from backend.DB.api import app, db, queries
from flask import jsonify, request, abort

from backend.DB.api.tables import User, Pair, Reward, Threshold


@app.route('/')
def hello_world():
    return 'Hello World'


@app.route('/api/user/add', methods=['POST'])
def add_user():
    r = request.get_json()

    if r is None or 'username' not in r or 'firstname' not in r or 'lastname' not in r:
        abort(400)

    username = r['username']
    firstname = r['firstname']
    lastname = r['lastname']
    user = User(username, firstname, lastname)
    queries.add_user(user)
    return jsonify(
        {'username': user.username, 'firstname': user.firstname, 'lastname': user.lastname})


@app.route('/api/user/all', methods=['GET'])
def get_all_users():
    users = queries.get_all_users()
    output = []
    for user in users:
        user_data = {'username': user.username, 'firstname': user.firstname, 'lastname': user.lastname,
                     'active': user.active}
        output.append(user_data)
    return jsonify({'users': output})


@app.route('/api/user/active', methods=['GET'])
def get_active_users():
    users = queries.get_active_users()
    output = []
    for user in users:
        user_data = {'username': user.username, 'firstname': user.firstname, 'lastname': user.lastname,
                     'active': user.active}
        output.append(user_data)
    return jsonify({'users': output})


@app.route('/api/user/get/<username>', methods=['GET'])
def get_user(username):
    user = queries.get_user_by_username(username)
    return jsonify(
        {'username': user.username,
         'firstname': user.firstname,
         'lastname': user.lastname,
         'active': user.active})


@app.route('/api/user/update/<username>', methods=['PUT'])
def update_user(username):
    user = queries.get_user_by_username(username)
    r = request.get_json()

    if r is None or 'firstname' not in r or 'lastname' not in r or 'active' not in r:
        abort(400)

    user.firstname = r['firstname']
    user.lastname = r['lastname']
    user.active = r['active']
    queries.update_user(user)
    return jsonify(
        {'username': user.username,
         'firstname': user.firstname,
         'lastname': user.lastname,
         'active': user.active})


@app.route('/api/user/delete/<username>', methods=['DELETE'])
def delete_user(username):
    user = queries.get_user_by_username(username)
    queries.delete_user(user.username)
    return jsonify({'message': user.username + ' deleted'})


def format_pairs(pairs):
    output = []
    for pair in pairs:
        user_data = {'person1': pair.person1, 'person2': pair.person2, 'date': pair.date}
        output.append(user_data)
    return output


@app.route('/api/pair/add', methods=['POST'])
def add_pair():
    r = request.get_json()

    if r is None or 'person1' not in r or 'person2' not in r:
        abort(400)

    if 'date' not in r:
        pair = Pair(r['person1'], r['person2'])
        queries.add_pair(pair)
        return jsonify({'person1': pair.person1, 'person2': pair.person2, 'date': pair.date})
    pair = Pair(r['person1'], r['person2'], r['date'])
    queries.add_pair(pair)
    return jsonify(format_pairs([pair])[0])


@app.route('/api/pair/all', methods=['GET'])
def get_all_pairs():
    pairs = queries.get_pair_history()
    output = format_pairs(pairs)
    return jsonify({'pairs': output})


@app.route('/api/pair/all/after_date/<date>', methods=['GET'])
def get_pairs_since_date(date):
    pairs = queries.get_pairs_from_date(date)
    return jsonify({'pairs': format_pairs(pairs)})


@app.route('/api/pair/with_user/<username>', methods=['GET'])
def get_pairs_with_user(username):
    pairs = queries.get_pairs_with_user(username)
    return jsonify({'pairs': format_pairs(pairs)})


@app.route('/api/pair/all/after_last_reward/<reward_type>', methods=['GET'])
def get_pairs_since_last_reward(reward_type):
    pairs = queries.get_pair_since_last_reward(reward_type)
    return jsonify({'pairs': format_pairs(pairs)})


@app.route('/api/pair/at_date/get/<date>', methods=['GET'])
def get_pair(date):
    return jsonify(format_pairs([queries.get_pair(date)])[0])


@app.route('/api/pair/at_date/update/<date>', methods=['PUT'])
def update_pair(date):
    r = request.get_json()

    if r is None or 'person1' not in r or 'person2' not in r:
        abort(400)

    pair = [Pair(r['person1'], r['person2'], date)]
    queries.update_pair(pair[0])
    return jsonify(format_pairs(pair)[0])


def format_rewards(rewards):
    output = []
    for reward in rewards:
        output.append({'reward_type': reward.reward_type, 'date': reward.date})
    return jsonify({'rewards': output})


@app.route('/api/reward/add', methods=['POST'])
def add_reward():
    r = request.get_json()

    if r is None or 'reward_type' not in r:
        abort(400)

    if 'date' not in r:
        reward = Reward(r['reward_type'])
    else:
        reward = Reward(r['reward_type'], r['date'])
    queries.add_reward(reward)
    return jsonify({'reward_type': reward.reward_type, 'date': reward.date})


@app.route('/api/reward/all', methods=['GET'])
def get_all_rewards():
    rewards = queries.get_rewards()
    return format_rewards(rewards)


@app.route('/api/reward/unused/<reward_type>', methods=['GET'])
def get_unused_reward_count(reward_type):
    count = queries.get_unused_rewards_count_by_type(reward_type)
    return jsonify({'num_rewards': count})


@app.route('/api/reward/unused/earliest/<reward_type>', methods=['GET'])
def get_earliest_unused_reward(reward_type):
    return format_rewards([queries.get_earliest_unused_reward(reward_type)])


@app.route('/api/reward/use/<reward_type>', methods=['PUT'])
def use_reward(reward_type):
    return format_rewards([queries.use_reward(reward_type)])


@app.route('/api/threshold/add', methods=['POST'])
def add_threshold():
    r = request.get_json()

    if r is None or 'reward_type' not in r or 'threshold' not in r:
        abort(400)

    threshold = Threshold(r['reward_type'], r['threshold'])
    queries.add_threshold(threshold)
    return jsonify({'reward_type': threshold.reward_type, 'threshold': threshold.threshold})


@app.route('/api/threshold/get/<reward_type>', methods=['GET'])
def get_threshold(reward_type):
    threshold = queries.get_threshold(reward_type)
    return jsonify({'reward_type': threshold.reward_type, 'threshold': threshold.threshold})


@app.route('/api/threshold/update/<reward_type>', methods=['PUT'])
def update_threshold(reward_type):
    r = request.get_json()

    if r is None or 'threshold' not in r:
        abort(400)

    threshold = queries.get_threshold(reward_type)
    threshold.threshold = r['threshold']
    queries.update_threshold(threshold)
    return jsonify({'reward_type': threshold.reward_type, 'threshold': threshold.threshold})


if __name__ == '__main__':
    db.create_all()
    db.init_app(app)
    app.run(host='0.0.0.0', port=app.config.get("PORT", 5000))
