import datetime
import json
import math
import time

from backend.DB.api.routes import app
from backend.DB.api.tables import db
import unittest

token = "?token=TEST"


class DatabaseTester(unittest.TestCase):

    def setUp(self):
        # Create a new database for each test
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SECRET_KEY'] = 'TEST'
        app.config['TESTING'] = True
        self.app = app.test_client()
        app.app_context().push()
        db.init_app(app)
        db.create_all()
        # Test users
        data = [
            {'active': 1, 'name': 'Per Pål', 'username': 'test1'},
            {'active': 1, 'name': 'Per Pål', 'username': 'test2'},
            {'active': 1, 'name': 'Per Pål', 'username': 'test3'},
            {'active': 1, 'name': 'Per Pål', 'username': 'test4'},
            {'active': 1, 'name': 'Per Pål', 'username': 'test5'},
        ]
        for user in data:
            self.app.post('/api/user/add{}'.format(token), data=json.dumps(user), content_type='application/json')
        thresholds = [
            {'threshold': 52, 'reward_type': 'pizza'},
            {'threshold': 40, 'reward_type': 'cake'}
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
        thres = self.app.get('api/threshold/get/cake{}'.format(token))
        self.assertEqual(40, thres.json[0]['threshold'])
        thres = self.app.get('api/threshold/get/pizza{}'.format(token))
        self.assertEqual(52, thres.json[0]['threshold'])

    def test_disable_and_update_user(self):

        user = {'username': 'test2', 'name': 'updated', 'active': 0}
        rv = self.app.put(
            '/api/user/update{}'.format(token), data=json.dumps(user),
            content_type='application/json')
        self.assertFalse(rv.json[0].get('active'))

    def test_delete_user(self):
        rv = self.app.delete('/api/user/delete/test1{}'.format(token))
        self.assertEqual(rv.json.get('message'), 'test1 deleted')
        rv = self.app.get('/api/user/all{}'.format(token))
        user_json = {'active': 1, 'name': 'Per Pål', 'username': 'test1'}
        self.assertNotIn(user_json, rv.json)

    def test_get_active_users(self):
        data = {'username': 'test2', 'name': 'updated', 'active': False}
        self.app.put('/api/user/update{}'.format(token), data=json.dumps(data), content_type='application/json')
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

    def test_get_pair_with_user(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}

        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')

        rv = self.app.get('/api/pair/with_user/test1{}'.format(token))
        self.assertIn(pair, rv.json.get('pairs'))

        rv = self.app.get('/api/pair/with_user/test2{}'.format(token))
        self.assertNotIn(pair, rv.json.get('pairs'))

    def test_get_pair_after_reward(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        reward = {'reward_type': 'pizza', 'date': date}
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward), content_type='application/json')
        rv = self.app.get('/api/pair/all/after_last_reward/pizza{}'.format(token))
        pairs = rv.json
        self.assertEqual(0, len(pairs))
        pair = {'date': date, 'person1': 'test1', 'person2': 'test3'}
        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
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

    def test_update_pair(self):
        date = math.floor(datetime.datetime.now().timestamp() * 1000)
        pair1 = {'person1': 'test1', 'person2': 'test2', 'date': date}

        self.app.post('/api/pair/add{}'.format(token), data=json.dumps(pair1), content_type='application/json')

        pair1 = {'person1': 'test3', 'person2': 'test2'}

        self.app.put(('/api/pair/at_date/update/{}{}'.format(date, token)),
                     data=json.dumps(pair1), content_type='application/json')

        rv = self.app.get('/api/pair/at_date/get/{}{}'.format(date, token))
        self.assertEqual('test3', rv.json.get('person1'))

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
        reward1 = {'reward_type': 'pizza'}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward3), content_type='application/json')

        rewards = self.app.get('/api/reward/all{}'.format(token)).json
        self.assertEqual(3, len(rewards))
        count = self.app.get('api/reward/unused/pizza{}'.format(token)).json
        self.assertEqual(2, count)
        count = self.app.get('api/reward/unused/cake{}'.format(token)).json
        self.assertEqual(1, count)

    def test_use_reward(self):
        reward1 = {'reward_type': 'pizza'}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward3), content_type='application/json')

        self.app.put('/api/reward/use/pizza{}'.format(token))
        count = self.app.get('/api/reward/unused/pizza{}'.format(token)).json

        self.assertEqual(1, count)

    def test_get_earliest_unused_reward(self):
        date = math.floor(time.time() * 1000)

        reward1 = {'reward_type': 'pizza', 'date': date}
        reward2 = {'reward_type': 'cake'}
        reward3 = {'reward_type': 'pizza'}

        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward1), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward2), content_type='application/json')
        self.app.post('/api/reward/add{}'.format(token), data=json.dumps(reward3), content_type='application/json')

        reward = self.app.get('/api/reward/unused/earliest/pizza{}'.format(token)).json[0]

        self.assertEqual(reward['date'], date)

    def test_reward_progress(self):
        result = self.app.get('/api/reward/progress{}'.format(token), content_type='application/json').json
        self.assertNotIn('last_pair', result.keys())
        pair = {'person1': 'test1', 'person2': 'test2'}
        self.app.post('api/pair/add{}'.format(token), data=json.dumps(pair), content_type='application/json')
        result = self.app.get('/api/reward/progress{}'.format(token), content_type='application/json').json
        self.assertIn('last_pair', result.keys())

    def test_update_threshold(self):
        updated_info = {'threshold': 42}
        self.app.put('/api/threshold/update/pizza{}'.format(token),
                     data=json.dumps(updated_info), content_type='application/json')
        threshold = self.app.get('/api/threshold/get/pizza{}'.format(token)).json[0].get('threshold')
        self.assertEqual(42, threshold)

    def test_wrong_input(self):
        faulty_data = {'wrong': 'this is wrong'}
        response = self.app.post('/api/user/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.app.post('/api/pair/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.app.post('/api/reward/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.app.post('/api/threshold/add{}'.format(token),
                                 data=json.dumps(faulty_data), content_type='application/json')
        self.assertEqual(400, response.status_code)
        response = self.app.delete('/api/user/delete/not_a_username{}'.format(token))
        self.assertEqual(400, response.status_code)

    def test_wrong_token(self):
        response = self.app.get('/api/user/all?token=wrong_token')
        self.assertEqual(403, response.status_code)
