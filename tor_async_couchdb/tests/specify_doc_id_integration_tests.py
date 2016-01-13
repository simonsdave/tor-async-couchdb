"""Integration tests to verify .. is working.

Be warned - this test suite feels complicated.
"""

import httplib
import json
import random
import uuid

import nose.plugins.attrib
import requests
import tornado.testing
import tornado.web

from .. import async_model_actions
from ..model import Model

# db names must start with a letter
_database_url = r'http://127.0.0.1:5984/a%s' % uuid.uuid4().hex


class Fruit(Model):

    fruits = [
        'apple',
        'pear',
        'fig',
        'orange',
        'kiwi',
    ]

    _type_name = 'fruit_v1.0'

    def __init__(self, *args, **kwargs):
        Model.__init__(self, *args, **kwargs)

        if 'doc' in kwargs:
            doc = kwargs['doc']
            assert doc['type'] == type(self)._type_name
            self.fruit = doc['fruit']
            return

        self.fruit = random.choice(type(self).fruits)

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv['type'] = type(self)._type_name
        rv['fruit'] = self.fruit
        return rv


class AsyncFruitPersister(async_model_actions.AsyncPersister):

    def __init__(self, fruit, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, fruit, [], async_state)


class AsyncFruitRetriever(async_model_actions.AsyncModelRetrieverByDocumentID):

    def __init__(self, _id, async_state=None):
        async_model_actions.AsyncModelRetrieverByDocumentID.__init__(
            self,
            _id,
            async_state)

    def create_model_from_doc(self, doc):
        print "*" * 256
        return Fruit(doc=doc)


class RequestHandler(tornado.web.RequestHandler):
    """The ```SpecifyDocIdIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async model I/O classes to operate on persistent instances of
    Fruit. Why is this request handler needed? The async model I/O
    classes need to operate in the context of a Tornado I/O loop.
    """
    post_url_spec = r'/fruit/(.+)'

    @tornado.web.asynchronous
    def post(self, command):
        if command == 'create':
            def on_persist_done(is_ok, is_conflict, ap):
                self.write(json.dumps(self._fruit_as_dict(ap.model)))
                self.set_status(httplib.CREATED)
                self.finish()

            json_request_body = json.loads(self.request.body)
            fruit = Fruit(_id=json_request_body['_id'])
            ap = AsyncFruitPersister(fruit)
            ap.persist(on_persist_done)
            return

        if command == 'get':
            def on_fetch_done(is_ok, fruit, abr):
                if fruit is None:
                    self.set_status(httplib.NOT_FOUND)
                    self.finish()
                    return

                self.write(json.dumps(self._fruit_as_dict(fruit)))
                self.set_status(httplib.OK)
                self.finish()

            json_request_body = json.loads(self.request.body)
            abr = AsyncFruitRetriever(json_request_body['_id'])
            abr.fetch(on_fetch_done)
            return

        self.set_status(httplib.NOT_FOUND)
        self.finish()

    def _fruit_as_dict(self, fruit):
        return {
            '_id': fruit._id,
            '_rev': fruit._rev,
            'fruit': fruit.fruit,
        }


@nose.plugins.attrib.attr('integration')
class SpecifyDocIdIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        """Setup the integration tests environment. Specifically,
        create a temporary database including creating a design doc
        which permits reading persistant instances of Fruit
        """
        # in case a previous test didn't clean itself up delete database
        # totally ignoring the result
        response = requests.delete(_database_url)
        # create database
        response = requests.put(_database_url)
        assert response.status_code == httplib.CREATED
        # get async_model_actions using our temp database
        async_model_actions.database = _database_url

    @classmethod
    def tearDownClass(cls):
        # delete database
        # response = requests.delete(_database_url)
        # assert response.status_code == httplib.OK
        pass

    def get_app(self):
        handlers = [
            (
                RequestHandler.post_url_spec,
                RequestHandler
            ),
        ]
        return tornado.web.Application(handlers=handlers)

    def test_all_good_with_service_generating_ids(self):
        # create at least 10 and no more than 15 persistent instances of Fruit
        fruits = [self._create_fruit(_id=uuid.uuid4().hex) for i in range(0, random.randint(10, 15))]

        # for each created Fruit retrieve the persisted Fruit and
        # confirm the created and persisted Fruit are the same
        for fruit in fruits:
            persisted_fruit = self._get_fruit(fruit['_id'])
            self.assertTwoFruitsEqual(fruit, persisted_fruit)

    def _create_fruit(self, _id):
        """Ask the request handler to create a persistent instance of Fruit."""
        body = {
            '_id': _id,
        }
        headers = {
            'content-type': 'application/json',
        }
        response = self.fetch(
            '/fruit/create',
            method='POST',
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.CREATED)
        fruit = json.loads(response.body)
        self.assertEqual(fruit['_id'], _id)
        return fruit

    def _get_fruit(self, _id):
        """Ask the request handler to retrieve a persisted Fruit."""
        body = {
            '_id': _id,
        }
        headers = {
            'content-type': 'application/json',
        }
        response = self.fetch(
            '/fruit/get',
            method='POST',
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        if response.code == httplib.NOT_FOUND:
            return None
        self.assertEqual(response.code, httplib.OK)
        return json.loads(response.body)

    def assertTwoFruitsEqual(self, fruit, other_fruit, expected_underscore_id=None):
        self.assertIsNotNone(fruit)
        self.assertIsNotNone(other_fruit)
        self.assertEqual(fruit['fruit'], other_fruit['fruit'])
        self.assertEqual(fruit['_id'], other_fruit['_id'])
        self.assertEqual(fruit['_rev'], other_fruit['_rev'])
