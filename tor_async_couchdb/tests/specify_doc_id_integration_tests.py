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

_database_url = r"http://127.0.0.1:5984/davewashere"

# curl http://127.0.0.1:5984/davewashere/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
_design_doc_name = 'boo_by_boo_id'
_type_name = 'boo_v1.0'
_design_doc = (
    '{'
    '    "language": "javascript",'
    '    "views": {'
    '        "%VIEW_NAME%": {'
    '            "map": "function(doc) { if (doc.type.match(/^%TYPE_NAME%/i)) { emit(doc.boo_id) } }"'
    '        }'
    '    }'
    '}'
)
_design_doc = _design_doc.replace("%VIEW_NAME%", _design_doc_name)
_design_doc = _design_doc.replace("%TYPE_NAME%", _type_name)


class Boo(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if 'doc' in kwargs:
            doc = kwargs['doc']
            assert doc['type'] == _type_name
            self.boo_id = doc['boo_id']
            self.fruit = doc['fruit']
            return

        self.boo_id = kwargs['boo_id']
        fruits = [
            'apple',
            'pear',
            'fig',
            'orange',
            'kiwi',
        ]
        self.fruit = random.choice(fruits)

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv['type'] = _type_name
        rv['boo_id'] = self.boo_id
        rv['fruit'] = self.fruit
        return rv


class AsyncBooPersister(async_model_actions.AsyncPersister):

    def __init__(self, boo, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, boo, [], async_state)


class AsyncBooRetriever(async_model_actions.AsyncModelRetriever):

    def __init__(self, boo_id, async_state=None):
        async_model_actions.AsyncModelRetriever.__init__(
            self,
            'boo_by_boo_id',
            boo_id,
            async_state)

    def create_model_from_doc(self, doc):
        return Boo(doc=doc)


class RequestHandler(tornado.web.RequestHandler):
    """The ```SpecifyDocIdIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async model I/O classes to operate on persistent instances of
    Boo. Why is this request handler needed? The async model I/O
    classes need to operate in the context of a Tornado I/O loop.
    """
    post_url_spec = r'/boo/(.+)'

    @tornado.web.asynchronous
    def post(self, command):
        if command == 'create':
            def on_persist_done(is_ok, is_conflict, ap):
                self.write(json.dumps(self._boo_as_dict(ap.model)))
                self.set_status(httplib.CREATED)
                self.finish()

            boo = Boo(boo_id=uuid.uuid4().hex)
            ap = AsyncBooPersister(boo)
            ap.persist(on_persist_done)
            return

        if command == 'get':
            def on_fetch_done(is_ok, boo, abr):
                if boo is None:
                    self.set_status(httplib.NOT_FOUND)
                    self.finish()
                    return

                self.write(json.dumps(self._boo_as_dict(boo)))
                self.set_status(httplib.OK)
                self.finish()

            json_request_body = json.loads(self.request.body)
            boo_id = json_request_body['boo_id']
            abr = AsyncBooRetriever(boo_id)
            abr.fetch(on_fetch_done)
            return

        self.set_status(httplib.NOT_FOUND)
        self.finish()

    def _boo_as_dict(self, boo):
        return {
            '_id': boo._id,
            '_rev': boo._rev,
            'boo_id': boo.boo_id,
            'fruit': boo.fruit,
        }


@nose.plugins.attrib.attr('integration')
class SpecifyDocIdIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        """Setup the integration tests environment. Specifically,
        create a temporary database including creating a design doc
        which permits reading persistant instances of Boo
        """
        # in case a previous test didn't clean itself up delete database
        # totally ignoring the result
        response = requests.delete(_database_url)
        # create database
        response = requests.put(_database_url)
        assert response.status_code == httplib.CREATED

        # install design doc
        url = '%s/_design/%s' % (_database_url, _design_doc_name)
        response = requests.put(
            url,
            data=_design_doc,
            headers={'Content-Type': 'application/json'})
        assert response.status_code == httplib.CREATED

        # get async_model_actions using our temp database
        async_model_actions.database = _database_url

    @classmethod
    def tearDownClass(cls):
        # delete database
        response = requests.delete(_database_url)
        assert response.status_code == httplib.OK

    def get_app(self):
        handlers = [
            (
                RequestHandler.post_url_spec,
                RequestHandler
            ),
        ]
        return tornado.web.Application(handlers=handlers)

    def test_all_good(self):
        # create at least 10 and no more than 15 persistent instances of Boo
        boos = [self._create_boo() for i in range(0, random.randint(10, 15))]

        # for each created Boo retrieve the persisted Boo and
        # confirm the created and persisted Boo are the same
        for boo in boos:
            persisted_boo = self._get_boo(boo['boo_id'])
            self.assertTwoBoosEqual(boo, persisted_boo)

    def _create_boo(self):
        """Ask the request handler to create a persistent instance of Boo."""
        body = {
        }
        headers = {
            'content-type': 'application/json',
        }
        response = self.fetch(
            '/boo/create',
            method='POST',
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.CREATED)
        return json.loads(response.body)

    def _get_boo(self, boo_id):
        """Ask the request handler to retrieve a persisted Boo."""
        body = {
            'boo_id': boo_id,
        }
        headers = {
            'content-type': 'application/json',
        }
        response = self.fetch(
            '/boo/get',
            method='POST',
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        if response.code == httplib.NOT_FOUND:
            return None
        self.assertEqual(response.code, httplib.OK)
        return json.loads(response.body)

    def assertTwoBoosEqual(self, boo, other_boo):
        self.assertIsNotNone(boo)
        self.assertIsNotNone(other_boo)
        self.assertEqual(boo['boo_id'], other_boo['boo_id'])
        self.assertEqual(boo['fruit'], other_boo['fruit'])
        self.assertEqual(boo['_id'], other_boo['_id'])
        self.assertEqual(boo['_rev'], other_boo['_rev'])
