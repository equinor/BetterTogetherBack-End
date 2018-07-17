from sqlalchemy import func, or_, and_
from backend.DB.api import db
from backend.DB.api import tables


# Queries for User
def add_user(user):
    db.session.add(user)
    db.session.commit()


def get_active_users():
    return tables.User.query.filter_by(active=True).all()


def get_all_users():
    return tables.User.query.all()


def get_user_by_username(username):
    return tables.User.query.filter_by(username=username).first()


def delete_user(username):
    user = tables.User.query.filter_by(username=username).first()
    db.session.delete(user)
    db.session.commit()


def disable_user(username):
    tables.User.query.filter_by(username=username).update(
        {'firstname': "Unknown", 'lastname': "User", 'active': False})
    db.session.commit()


def update_user(user):
    tables.User.query.filter_by(username=user.username).update(
        {'active': user.active, 'firstname': user.firstname, 'lastname': user.lastname})
    db.session.commit()


# Queries for pair
def add_pair(pair):
    db.session.add(pair)
    db.session.commit()


def get_pair_history():
    return tables.Pair.query.all()


def get_pair_since_last_reward(reward_type):
    reward_date = db.session.query(
        db.func.max(tables.Reward.date)).filter_by(reward_type=reward_type).first()
    if reward_date[0] is None:
        return get_pair_history()
    else:
        return tables.Pair.query.filter(tables.Pair.date >= reward_date[0]).all()


def get_pairs_with_user(username):
    return db.session.query(tables.Pair).filter(
        or_(tables.Pair.person1 == username, tables.Pair.person2 == username)).all()


def get_pairs_from_date(date):
    return tables.Pair.query.filter(tables.Pair.date >= date).all()


def get_pair(date):
    return tables.Pair.query.filter_by(date=date).first()


def update_pair(pair):
    tables.Pair.query.filter_by(date=pair.date).update(
        {'person1': pair.person1, 'person2': pair.person2})
    db.session.commit()


# Queries for reward
def add_reward(reward):
    db.session.add(reward)
    db.session.commit()


def get_rewards():
    return tables.Reward.query.all()


def get_unused_rewards_count_by_type(reward_type):
    return tables.Reward.query.filter(and_(
        tables.Reward.reward_type == reward_type, tables.Reward.used_reward == 0)).count()


def get_last_reward_type():
    reward = tables.Reward.query(db.func.max(tables.Reward.date)).first()
    return reward.reward_type


def get_last_reward_date():
    reward = tables.Reward.query(db.func.max(tables.Reward.date)).first()
    return reward.date


def get_earliest_unused_reward(reward_type):
    reward = tables.Reward.query.filter(
        and_(tables.Reward.reward_type == reward_type, tables.Reward.used_reward == 0)).first()
    return reward


def use_reward(reward_type):
    reward_date = db.session.query(db.func.min(tables.Reward.date)).filter(and_(
        tables.Reward.reward_type == reward_type, tables.Reward.used_reward == 0)).first()[0]
    if reward_date is None:
        return None
    reward = tables.Reward.query.filter_by(date=reward_date).first()
    reward.used_reward = True
    db.session.commit()
    return reward


# Queries for threshold
def add_threshold(threshold):
    db.session.add(threshold)
    db.session.commit()


def get_threshold(reward_type):
    return tables.Threshold.query.filter_by(reward_type=reward_type).first()


def update_threshold(threshold):
    tables.Threshold.query.filter_by(reward_type=threshold.reward_type).update(
        {'threshold': threshold.threshold})
    db.session.commit()
