import datetime
import json
import math

from api import app, db
import unittest

from api import routes, tables
from api.tables import Reward


class DatabaseTester(unittest.TestCase):

    def setUp(self):
        # Create a new database for each test
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['TESTING'] = True
        self.app = app.test_client()
        db.create_all()
        # Test users
        data = [
            {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test1'},
            {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test2'},
            {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test3'},
            {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test4'},
            {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test5'},
        ]
        for user in data:
            self.app.post('/api/user', data=json.dumps(user), content_type='application/json')

    def tearDown(self):
        # Empty db after each test
        db.session.remove()
        db.drop_all()

    def test_db_filled(self):
        # Verify that all users have been added to the db
        rv = self.app.get('/api/user/all')
        self.assertEqual(5, len(rv.json.get('users')))

    def test_disable_and_update_user(self):

        user = {'username': 'test2', 'firstname': 'updated', 'lastname': 'user', 'active': 0}
        rv = self.app.put(
            '/api/user/test2', data=json.dumps(user),
            content_type='application/json')
        self.assertFalse(rv.json.get('active'))

    def test_delete_user(self):
        rv = self.app.delete('/api/user/test1')
        self.assertEqual(rv.json.get('message'), 'test1 deleted')
        rv = self.app.get('/api/user/all')
        user_json = {'active': 1, 'firstname': 'per', 'lastname': 'pål', 'username': 'test1'}
        self.assertNotIn(user_json, rv.json.get('users'))

    def test_get_active_users(self):
        data = {'firstname': 'updated', 'lastname': 'user', 'active': False}
        self.app.put('/api/user/test2', data=json.dumps(data), content_type='application/json')
        rv = self.app.get('/api/user/active')
        users = rv.json.get('users')
        usernames = []
        for user in users:
            usernames.append(user.get('username'))
        self.assertNotIn('test2', usernames)
        self.assertIn('test3', usernames)

    def test_add_and_get_pair(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}
        rv = self.app.post('/api/pair', data=json.dumps(pair), content_type='application/json')
        json_file = rv.json
        self.assertEqual(pair, json_file)

        rv = self.app.get('/api/pair/all')
        pairs = rv.json.get('pairs')
        output = []
        for pair in pairs:
            output.append(pair.get('date'))
        self.assertIn(date, output)

    def test_get_pair_with_user(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}

        self.app.post('/api/pair', data=json.dumps(pair), content_type='application/json')

        rv = self.app.get('/api/pair/user/test1')
        self.assertIn(pair, rv.json.get('pairs'))

        rv = self.app.get('/api/pair/user/test2')
        self.assertNotIn(pair, rv.json.get('pairs'))

    def test_get_pair_after_reward(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        reward = {'reward_type': 'pizza', 'date': date}
        self.app.post('/api/reward', data=json.dumps(reward), content_type='application/json')
        print(self.app.get('/api/reward/all').json)
        rv = self.app.get('api/pair/rewtype/pizza')
        pairs = rv.json.get('pairs')
        self.assertEqual(0, len(pairs))
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair', data=json.dumps(pair), content_type='application/json')
        rv = self.app.get('api/pair/rewtype/pizza')
        pairs = rv.json.get('pairs')
        self.assertEqual(1, len(pairs))

    def test_get_pair_after_date(self):
        # Test pairs
        pair1 = {'person1': 'test1', 'person2': 'test2'}
        pair2 = {'person1': 'test3', 'person2': 'test4'}
        # Add a pair, get a timestamp after and add second pair
        self.app.post('/api/pair/', data=json.dumps(pair1), content_type='application/json')
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        self.app.post('/api/pair', data=json.dumps(pair2), content_type='application/json')
        # Get all pairs after the date
        rv = self.app.get(('/api/pair/all/date/%d' % date))
        pairs = rv.json.get('pairs')
        # Check that only the second pair is gotten from the query
        self.assertEqual(1, len(pairs))
        self.assertIn(pair2.get('person1'), pairs[0].get('person1'))

    def test_update_pair(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair1 = {'person1': 'test1', 'person2': 'test2', 'date': date}

        self.app.post('/api/pair', data=json.dumps(pair1), content_type='application/json')

        pair1 = {'person1': 'test3', 'person2': 'test2'}
        path = '/api/pair/date/%d' % date

        self.app.put(path, data=json.dumps(pair1), content_type='application/json')

        rv = self.app.get(path)
        self.assertEqual('test3', rv.json.get('person1'))

    def test_get_rewards(self):
        reward1 = {'reward_type': 'pizza'}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward', data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward3), content_type='application/json')

        rewards = self.app.get('/api/reward/all').json.get('rewards')
        self.assertEqual(3, len(rewards))
        rewards = self.app.get('api/reward/pizza').json.get('rewards')
        self.assertEqual(2, len(rewards))
        rewards = self.app.get('api/reward/cake').json.get('rewards')
        self.assertEqual(1, len(rewards))

    def test_use_reward(self):
        reward1 = {'reward_type': 'pizza'}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward', data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward3), content_type='application/json')

        self.app.put('/api/reward/pizza/use')
        rewards = self.app.get('/api/reward/pizza').json.get('rewards')

        self.assertEqual(1, len(rewards))

    def test_get_earliest_unused_reward(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)

        reward1 = {'reward_type': 'pizza', 'date': date}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward', data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward', data=json.dumps(reward3), content_type='application/json')

        reward = self.app.get('/api/reward/pizza/earliest').json.get('rewards')[0]

        self.assertEqual(reward['date'], date)

    def test_add_threshold(self):
        threshold = {'threshold': 50, 'reward_type': 'pizza'}
        self.app.post('/api/threshold', data=json.dumps(threshold), content_type='application/json')
        self.assertEqual(True, False)
