import datetime
import json
import math
import time
from backend.DB.api import queries
from backend.DB.api.routes import app
from backend.DB.api.tables import db, User, Reward
import unittest

token = "?token=TEST"


class DatabaseTester(unittest.TestCase):

    def setUp(self):
        # Create a new database for each test
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres@localhost:5432/test_db'
        app.config['SECRET_KEY'] = 'TEST'
        app.config['TESTING'] = True
        self.app = app.test_client()
        app.app_context().push()
        db.init_app(app)
        db.create_all()
        # Test users
        data = [
            {'active': True, 'name': 'Per Pål', 'username': 'test1'},
            {'active': True, 'name': 'Per Pål', 'username': 'test2'},
            {'active': True, 'name': 'Per Pål', 'username': 'test3'},
            {'active': True, 'name': 'Per Pål', 'username': 'test4'},
            {'active': True, 'name': 'Per Pål', 'username': 'test5'},
        ]
        for user in data:
            queries.add_user(User(user['username'], user['name']))
        thresholds = [
            {'threshold': 2, 'reward_type': 'pizza'},
            {'threshold': 1, 'reward_type': 'cake'}
        ]
        for threshold in thresholds:
            self.app.post('/api/threshold/add{}'.format(token), data=json.dumps(threshold),
                          content_type='application/json')

    def tearDown(self):
        # Empty db after each test
        db.session.remove()
        db.drop_all()

    def test_db_filled(self):
        # Verify that all users have been added to the db
        rv = self.app.get('/api/user/all{}'.format(token))
        self.assertEqual(5, len(rv.json))
        thres = queries.get_threshold('cake')
        self.assertEqual(1, thres.threshold)
        thres = queries.get_threshold('pizza')
        self.assertEqual(2, thres.threshold)

    def test_delete_user(self):
        pair = {'person1': 'test1', 'person2': 'test2'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
        rv = self.app.delete('/api/user/delete/test1{}'.format(token)).json
        self.assertEqual(rv.get('message'), 'test1 deleted')
        rv = self.app.get('/api/user/all{}'.format(token)).json
        user_json = {'active': 1, 'name': 'Per Pål', 'username': 'test1'}
        self.assertNotIn(user_json, rv)
        rv = self.app.get('/api/pair/all{}'.format(token)).json[0]
        self.assertEqual(None, rv['person1'])
        self.assertEqual('test2', rv['person2'])

    def test_get_active_users(self):
        queries.update_user(User('test2', 'updated', active=False))
        rv = self.app.get('/api/user/active{}'.format(token))
        users = rv.json
        usernames = []
        for user in users:
            usernames.append(user.get('username'))
        self.assertNotIn('test2', usernames)
        self.assertIn('test3', usernames)

    def test_add_and_get_pair(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}
        rv = self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
        json_file = rv.json
        self.assertEqual(pair, json_file)

        rv = self.app.get('/api/pair/all{}'.format(token))
        pairs = rv.json
        output = []
        for pair in pairs:
            output.append(pair.get('date'))
        self.assertIn(date, output)

    def test_add_reward_if_enough_pairs(self):
        pair1 = {'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair1), content_type='application/json')
        rewards = self.app.get('/api/reward/all{}'.format(token)).json
        self.assertEqual(1, len(rewards))

        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair1), content_type='application/json')
        rewards = self.app.get('/api/reward/all{}'.format(token)).json
        self.assertEqual(3, len(rewards))

    def test_get_pair_after_reward(self):
        pair = {'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
        date = math.floor(datetime.datetime.now().timestamp() * 1000)

        queries.add_reward(Reward('pizza'))

        rv = self.app.get('/api/pair/all/after_last_reward/pizza{}'.format(token))
        pairs = rv.json
        self.assertEqual(1, len(pairs))

        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')

        rv = self.app.get('api/pair/all/after_last_reward/pizza{}'.format(token))
        pairs = rv.json
        self.assertEqual(2, len(pairs))

        self.app.put('/api/reward/use/pizza{}'.format(token))
        rv = self.app.get('api/pair/all/after_last_reward/pizza{}'.format(token))
        pairs = rv.json
        self.assertEqual(1, len(pairs))

    def test_get_pair_after_date(self):
        # Test pairs
        pair1 = {'person1': 'test1', 'person2': 'test2'}
        pair2 = {'person1': 'test3', 'person2': 'test4'}
        # Add a pair, get a timestamp after and add second pair
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair1), content_type='application/json')
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair2), content_type='application/json')
        # Get all pairs after the date
        rv = self.app.get(('/api/pair/all/after_date/{}{}'.format(date, token)))
        pairs = rv.json.get('pairs')
        # Check that only the second pair is gotten from the query
        self.assertEqual(1, len(pairs))
        self.assertIn(pair2.get('person1'), pairs[0].get('person1'))

    def test_get_pair_count(self):
        pair1 = {'person1': 'test1', 'person2': 'test2'}
        pair2 = {'person1': 'test2', 'person2': 'test1'}
        pair3 = {'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair1), content_type='application/json')
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair2), content_type='application/json')
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair3), content_type='application/json')
        response = self.app.get('/api/pair/count_pair{}'.format(token)).json
        self.assertEqual(2, len(response))
        self.assertEqual(2, response[0]['total'])
        self.assertEqual(1, response[1]['total'])

    def test_get_reward_count(self):
        queries.add_reward(Reward('pizza'))
        queries.add_reward(Reward('cake'))
        queries.add_reward(Reward('pizza'))

        rewards = self.app.get('/api/reward/all{}'.format(token)).json
        self.assertEqual(3, len(rewards))

    def test_use_reward(self):
        queries.add_reward(Reward('cake'))
        queries.add_reward(Reward('pizza'))
        queries.add_reward(Reward('pizza'))

        self.app.put('/api/reward/use/pizza{}'.format(token))
        rewards = self.app.get('api/reward/all{}'.format(token)).json
        count = 0
        for r in rewards:
            if r['used_reward']:
                count += 1
        self.assertEqual(1, count)

    def test_reward_progress(self):
        result = self.app.get('/api/reward/progress{}'.format(token), content_type='application/json').json
        self.assertNotIn('last_pair', result.keys())
        pair = {'person1': 'test1', 'person2': 'test2'}
        self.app.post('api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
        result = self.app.get('/api/reward/progress{}'.format(token), content_type='application/json').json
        self.assertIn('last_pair', result.keys())

    def test_update_threshold(self):
        self.app.put('/api/threshold/update/pizza/42{}'.format(token))
        threshold = queries.get_threshold('pizza')
        self.assertEqual(42, threshold.threshold)

    def test_wrong_input(self):
        faulty_data = {'wrong': 'this is wrong'}
        response = self.app.post('/api/pair/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)

        self.assertEqual(400, response.status_code)
        response = self.app.post('/api/threshold/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.app.delete('/api/user/delete/not_a_username{}'.format(token))
        self.assertEqual(400, response.status_code)

    def test_wrong_token(self):
        response = self.app.get('/api/user/all?token=wrong_token')
        self.assertEqual(403, response.status_code)
