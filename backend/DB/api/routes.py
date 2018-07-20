from backend.DB.api import app, db, queries
from flask import jsonify, request, abort

from backend.DB.api.tables import User, Pair, Reward, Threshold


@app.route('/')
def hello_world():
    return 'Hello World'


def format_users(users):
    output = []
    for user in users:
        output.append(
            {'username': user.username, 'name': user.name, 'image': user.image, 'active': user.active})
    return jsonify(output)


@app.route('/api/user/add', methods=['POST'])
def add_user():
    r = request.get_json()

    if r is None or 'username' not in r or 'name' not in r:
        abort(400)

    username = r['username']
    name = r['name']
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
    r = request.get_json()

    if r is None or 'username' not in r or 'name' not in r or 'active' not in r:
        abort(400)

    user = queries.get_user_by_username(r['username'])
    if user is None:
        abort(400)

    user.name = r['name']
    user.active = r['active']
    queries.update_user(user)
    return format_users([user])


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
    return jsonify(output)


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
    return jsonify(format_pairs(pairs))


@app.route('/api/pair/count_pairs/', methods=['GET'])
def get_pair_count_between_all_users():
    counters = queries.get_pair_count_between_all_users()
    return jsonify(counters)


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
        output.append({'reward_type': reward.reward_type, 'date': reward.date, 'used_reward': reward.used_reward})
    return jsonify(output)


@app.route('/api/reward/add', methods=['POST'])
def add_reward():
    r = request.get_json()

    if r is None or 'reward_type' not in r:
        abort(400)

    if 'date' not in r:
        reward = Reward(r['reward_type'].lower())
    else:
        reward = Reward(r['reward_type'].lower(), r['date'])
    if 'used_reward' in r:
        reward.used_reward = r['used_reward']
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
    r = request.get_json()

    if r is None or 'reward_type' not in r or 'threshold' not in r:
        abort(400)

    threshold = Threshold(r['reward_type'], r['threshold'])
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
    r = request.get_json()

    if r is None or 'threshold' not in r:
        abort(400)

    threshold = queries.get_threshold(reward_type)
    threshold.threshold = r['threshold']
    queries.update_threshold(threshold)
    return jsonify({'reward_type': threshold.reward_type, 'threshold': threshold.threshold})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config.get("PORT", 5000))
