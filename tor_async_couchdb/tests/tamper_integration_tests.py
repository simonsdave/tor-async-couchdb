"""Integration tests to verify tamper detection is working.
Turns out this tests suite is also a pretty good integration
test for the async couchdb framework too:-)

Be warned - this test suite feels complicated.
"""

import httplib
import json
import shutil
import tempfile
import random
import uuid

from keyczar import keyczar
from keyczar import keyczart
import nose.plugins.attrib
import requests
import tornado.testing
import tornado.web

from .. import async_model_actions
from .. import tamper
from ..model import Model

_database_url = r"http://127.0.0.1:5984/davewashere"

# curl http://127.0.0.1:5984/davewashere/_design/fruit_by_fruit_id/_view/fruit_by_fruit_id?include_docs=true
_design_doc_name = "fruit_by_fruit_id"
_design_doc = (
    '{'
    '    "language": "javascript",'
    '    "views": {'
    '        "%VIEW_NAME%": {'
    '            "map": "function(doc) { if (doc.type.match(/^fruit_v1.0/i)) { emit(doc.fruit_id) } }"'
    '        }'
    '    }'
    '}'
)
_design_doc = _design_doc.replace("%VIEW_NAME%", _design_doc_name)


class Fruit(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if "doc" in kwargs:
            doc = kwargs["doc"]
            self.fruit_id = doc["fruit_id"]
            self.fruit = doc["fruit"]
            return

        self.fruit_id = kwargs["fruit_id"]
        self.fruit = type(self).get_random_fruit()

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv["type"] = "fruit_v1.0"
        rv["fruit_id"] = self.fruit_id
        rv["fruit"] = self.fruit
        return rv

    @classmethod
    def get_random_fruit(cls, but_not_this_fruit=None):
        fruits = [
            "apple",
            "pear",
            "fig",
            "orange",
            "kiwi",
        ]
        while True:
            fruit = random.choice(fruits)
            if but_not_this_fruit is None:
                return fruit
            if but_not_this_fruit != fruit:
                return fruit


class AsyncFruitPersister(async_model_actions.AsyncPersister):

    def __init__(self, fruit, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, fruit, [], async_state)


class AsyncFruitRetriever(async_model_actions.AsyncModelRetriever):

    def __init__(self, fruit_id, async_state=None):
        async_model_actions.AsyncModelRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            fruit_id,
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class AsyncFruitsRetriever(async_model_actions.AsyncModelsRetriever):

    def __init__(self, start_key, end_key, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            start_key,
            end_key,
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class RequestHandler(tornado.web.RequestHandler):
    """The ```TamperingIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async model I/O classes to operate on persistent instances of
    Fruit. Why is this request handler needed? The async model I/O
    classes need to operate in the context of a Tornado I/O loop.
    """

    post_url_spec = r"/fruit/(.+)"

    @tornado.web.asynchronous
    def post(self, command):

        if command == "create":
            def on_persist_done(is_ok, is_conflict, ap):
                self.write(json.dumps(self._fruit_as_dict(ap.model)))
                self.set_status(httplib.CREATED)
                self.finish()

            fruit = Fruit(fruit_id=uuid.uuid4().hex)
            ap = AsyncFruitPersister(fruit)
            ap.persist(on_persist_done)
            return

        if command == "get":
            def on_fetch_done(is_ok, fruit, abr):
                if fruit is None:
                    self.set_status(httplib.NOT_FOUND)
                    self.finish()
                    return

                self.write(json.dumps(self._fruit_as_dict(fruit)))
                self.set_status(httplib.OK)
                self.finish()

            json_request_body = json.loads(self.request.body)
            fruit_id = json_request_body.get("fruit_id", None)
            assert fruit_id is not None
            abr = AsyncFruitRetriever(fruit_id)
            abr.fetch(on_fetch_done)
            return

        if command == "get_all":
            def on_fetch_done(is_ok, fruits, absr):
                assert fruits is not None
                dicts = [self._fruit_as_dict(fruit) for fruit in fruits]
                self.write(json.dumps(dicts))
                self.set_status(httplib.OK)
                self.finish()

            absr = AsyncFruitsRetriever(start_key=None, end_key=None)
            absr.fetch(on_fetch_done)
            return

        self.set_status(httplib.NOT_FOUND)
        self.finish()

    def _fruit_as_dict(self, fruit):
        return {
            "_id": fruit._id,
            "_rev": fruit._rev,
            "fruit_id": fruit.fruit_id,
            "fruit": fruit.fruit,
        }


@nose.plugins.attrib.attr('integration')
class TamperingIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        """Setup the integration tests environment. Specifically:

        -- create a temporary database including creating a design doc
        which permits reading persistant instances of Fruit
        -- create a tampering signer
        -- configure the async model I/O classes to use the newly
        created tampering signer and temporary database

        """
        # in case a previous test didn't clean itself up delete database
        # totally ignoring the result
        response = requests.delete(_database_url)
        # create database
        response = requests.put(_database_url)
        assert response.status_code == httplib.CREATED

        # install design doc
        url = "%s/_design/%s" % (_database_url, _design_doc_name)
        response = requests.put(
            url,
            data=_design_doc,
            headers={"Content-Type": "application/json; charset=utf8"})
        assert response.status_code == httplib.CREATED

        # get async_model_actions using our temp database
        async_model_actions.database = _database_url

        # create a tampering signer and get async_model_actions using it
        tampering_dir_name = tempfile.mkdtemp()

        keyczart.Create(
            tampering_dir_name,
            "some purpose",
            keyczart.keyinfo.SIGN_AND_VERIFY)
        keyczart.AddKey(
            tampering_dir_name,
            keyczart.keyinfo.PRIMARY)
        tampering_signer = keyczar.Signer.Read(tampering_dir_name)

        shutil.rmtree(tampering_dir_name, ignore_errors=True)

        # get async_model_actions using our tampering signer
        async_model_actions.tampering_signer = tampering_signer

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
        # create at least 10 and no more than 15 persistent instances of Fruit
        fruits = [self._create_fruit() for i in range(0, random.randint(10, 15))]

        # for each created Fruit retrieve the persisted Fruit and
        # confirm the created and persisted Fruit are the same
        for fruit in fruits:
            persisted_fruit = self._get_fruit(fruit.fruit_id)
            self.assertTwoFruitsEqual(fruit, persisted_fruit)

        self.assertTwoCollectionsOfFruitsAreEqual(
            fruits,
            self._get_all_fruits())

        # select one of the Fruit's @ random, retrieve the persisted verison
        # of the Fruit, tamper with it by changing its fruit and confirm the Fruit
        # is no longer retrievable
        fruit = fruits.pop(random.randint(0, len(fruits) - 1))
        self._change_fruit_fruit_and_persist(fruit)

        self.assertIsNone(self._get_fruit(fruit.fruit_id))
        self.assertTwoCollectionsOfFruitsAreEqual(
            fruits,
            self._get_all_fruits())

        # select one of the Fruit's @ random, retrieve the persisted verison
        # of the Fruit, tamper with it by removing the Fruit's signature
        fruit = fruits.pop(random.randint(0, len(fruits) - 1))
        self._remove_fruit_signature_and_persist(fruit)

        self.assertIsNone(self._get_fruit(fruit.fruit_id))
        self.assertTwoCollectionsOfFruitsAreEqual(
            fruits,
            self._get_all_fruits())

        # select one of the Fruit's @ random, retrieve the persisted verison
        # of the Fruit, tamper with it by changing the Fruit's signature
        fruit = fruits.pop(random.randint(0, len(fruits) - 1))
        self._change_fruit_signature_and_persist(fruit)

        self.assertIsNone(self._get_fruit(fruit.fruit_id))
        self.assertTwoCollectionsOfFruitsAreEqual(
            fruits,
            self._get_all_fruits())

    def _create_fruit(self):
        """Ask the request handler to create a persistent instance of Fruit."""
        body = {
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/fruit/create",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.CREATED)
        return Fruit(doc=json.loads(response.body))

    def _get_fruit(self, fruit_id):
        """Ask the request handler to retrieve a persisted Fruit."""
        body = {
            "fruit_id": fruit_id,
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/fruit/get",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        if response.code == httplib.NOT_FOUND:
            return None
        self.assertEqual(response.code, httplib.OK)
        return Fruit(doc=json.loads(response.body))

    def _get_all_fruits(self):
        """Ask the request handler to retrieve all persisted Fruits."""
        body = {
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/fruit/get_all",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.OK)
        docs = json.loads(response.body)
        fruits = [Fruit(doc=doc) for doc in docs]
        return fruits

    def _change_fruit_fruit_and_persist(self, fruit):
        self.assertIsNotNone(fruit)

        url = '%s/%s' % (_database_url, fruit._id)

        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        doc = response.json()
        self.assertIsNotNone(doc)
        fruit = doc.get("fruit", None)
        self.assertIsNotNone(fruit)

        new_fruit = Fruit.get_random_fruit(fruit)
        self.assertIsNotNone(new_fruit)
        self.assertNotEqual(fruit, new_fruit)
        doc["fruit"] = new_fruit

        response = requests.put(
            url,
            data=json.dumps(doc),
            headers={"Content-Type": "application/json; charset=utf8"})
        self.assertEqual(response.status_code, httplib.CREATED)

    def _remove_fruit_signature_and_persist(self, fruit):
        self.assertIsNotNone(fruit)

        url = '%s/%s' % (_database_url, fruit._id)

        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        doc = response.json()
        self.assertIsNotNone(doc)

        self.assertTrue(tamper._tampering_sig_prop_name in doc)
        del doc[tamper._tampering_sig_prop_name]

        response = requests.put(
            url,
            data=json.dumps(doc),
            headers={"Content-Type": "application/json; charset=utf8"})
        self.assertEqual(response.status_code, httplib.CREATED)

    def _change_fruit_signature_and_persist(self, fruit):
        self.assertIsNotNone(fruit)

        url = '%s/%s' % (_database_url, fruit._id)

        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        doc = response.json()
        self.assertIsNotNone(doc)

        self.assertTrue(tamper._tampering_sig_prop_name in doc)
        doc[tamper._tampering_sig_prop_name] = "dave"

        response = requests.put(
            url,
            data=json.dumps(doc),
            headers={"Content-Type": "application/json; charset=utf8"})
        self.assertEqual(response.status_code, httplib.CREATED)

    def assertTwoFruitsEqual(self, fruit, other_fruit):
        self.assertIsNotNone(fruit)
        self.assertIsNotNone(other_fruit)
        self.assertEqual(fruit.fruit_id, other_fruit.fruit_id)
        self.assertEqual(fruit.fruit, other_fruit.fruit)
        self.assertEqual(fruit._id, other_fruit._id)
        self.assertEqual(fruit._rev, other_fruit._rev)

    def assertTwoCollectionsOfFruitsAreEqual(self, fruits, other_fruits):
        self.assertIsNotNone(fruits)
        self.assertIsNotNone(other_fruits)
        self.assertEqual(len(fruits), len(other_fruits))

        fruits_dict = {fruit.fruit_id: fruit for fruit in fruits}
        other_fruits_dict = {fruit.fruit_id: fruit for fruit in other_fruits}

        # two fruit's can't have the same fruit_id
        self.assertEqual(len(fruits), len(fruits_dict))
        self.assertEqual(len(other_fruits), len(other_fruits_dict))

        for fruit in fruits:
            other_fruit = other_fruits_dict.get(fruit.fruit_id, None)
            self.assertIsNotNone(other_fruit)
            self.assertTwoFruitsEqual(fruit, other_fruit)
