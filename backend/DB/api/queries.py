from sqlalchemy import or_, and_
from backend.DB.api.tables import db
from backend.DB.api import tables
from sqlalchemy.exc import IntegrityError


# Queries for User
def add_user(user):
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


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
    deleted_user = tables.User.query.filter_by(username=username).first()
    return deleted_user is None


def update_user(user):
    tables.User.query.filter_by(username=user.username).update(
        {'active': user.active, 'name': user.name})
    db.session.commit()


# Queries for pair
def add_pair(pair):
    try:
        db.session.add(pair)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def get_pair_history():
    return tables.Pair.query.all()


def get_pairs_since_last_reward(reward_type):
    reward_date = db.session.query(
        db.func.max(tables.Reward.date)).filter_by(reward_type=reward_type).first()
    if reward_date[0] is None:
        return get_pair_history()
    else:
        return tables.Pair.query.filter(tables.Pair.date >= reward_date[0]).all()


def get_pairs_since_last_used_reward(reward_type):
    reward_date = db.session.query(
        db.func.max(tables.Reward.date)).filter(and_(
            reward_type == tables.Reward.reward_type, tables.Reward.used_reward)).first()
    if reward_date[0] is None:
        return get_pair_history()
    else:
        return tables.Pair.query.filter(tables.Pair.date >= reward_date[0]).all()


def get_pairs_from_date(date):
    return tables.Pair.query.filter(tables.Pair.date >= date).all()


def get_pair_counts_between_all_users():
    pairs = db.session.query(tables.Pair.person1, tables.Pair.person2, db.func.count(
        tables.Pair.person1)).group_by(tables.Pair.person1, tables.Pair.person2).all()
    counters = []
    for pair in pairs:
        should_add_pair = True
        if pair.person1 is None or pair.person2 is None:
            continue
        for i in range(len(counters)):
            if (pair[0] == counters[i]['target']) and (pair[1] == counters[i]['source']):
                counters[i]['total'] += pair[2]
                should_add_pair = False
        if should_add_pair:
            counters.append({'source': pair[0], 'target': pair[1], 'total': pair[2]})
    return counters


# Queries for reward
def add_reward(reward):
    try:
        db.session.add(reward)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def get_rewards():
    rewards = tables.Reward.query.all()
    return rewards


def use_reward(reward_type):
    reward_date = db.session.query(db.func.min(tables.Reward.date)).filter(and_(
        tables.Reward.reward_type == reward_type, tables.Reward.used_reward == False)).first()[0]
    if reward_date is None:
        return None
    reward = tables.Reward.query.filter_by(date=reward_date).first()
    reward.used_reward = True
    db.session.commit()
    return reward


# Queries for threshold
def add_threshold(threshold):
    try:
        db.session.add(threshold)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()


def get_threshold(reward_type):
    return tables.Threshold.query.filter_by(reward_type=reward_type).first()


def get_all_thresholds():
    return tables.Threshold.query.all()


def update_threshold(threshold):
    tables.Threshold.query.filter_by(reward_type=threshold.reward_type).update(
        {'threshold': threshold.threshold})
    db.session.commit()
