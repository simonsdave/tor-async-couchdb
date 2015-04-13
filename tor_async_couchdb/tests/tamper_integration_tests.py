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
import requests
import tornado.testing
import tornado.web

from .. import async_model_actions
from .. import tamper
from ..model import Model

_user_store_url = r"http://127.0.0.1:5984/davewashere"

# curl http://127.0.0.1:5984/davewashere/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
_design_doc_name = "boo_by_boo_id"
_design_doc = (
    '{'
    '    "language": "javascript",'
    '    "views": {'
    '        "%VIEW_NAME%": {'
    '            "map": "function(doc) { if (doc.type.match(/^boo_v1.0/i)) { emit(doc.boo_id) } }"'
    '        }'
    '    }'
    '}'
)
_design_doc = _design_doc.replace("%VIEW_NAME%", _design_doc_name)


class Boo(Model):

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
            fruit = fruits[random.randint(0, len(fruits)) - 1]
            if but_not_this_fruit is None or (but_not_this_fruit is not None and but_not_this_fruit != fruit):
                return fruit

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if "doc" in kwargs:
            doc = kwargs["doc"]
            self.boo_id = doc["boo_id"]
            self.fruit = doc["fruit"]
            return

        self.boo_id = kwargs["boo_id"]
        self.fruit = type(self).get_random_fruit()

    def as_dict_for_store(self):
        rv = Model.as_dict_for_store(self)
        rv["type"] = "boo_v1.0"
        rv["boo_id"] = self.boo_id
        rv["fruit"] = self.fruit
        return rv


class AsyncBooPersister(async_model_actions.AsyncPersister):

    def __init__(self, boo, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, boo, [], async_state)


class AsyncBooRetriever(async_model_actions.AsyncModelRetriever):

    def __init__(self, boo_id, async_state=None):
        async_model_actions.AsyncModelRetriever.__init__(
            self,
            "boo_by_boo_id",
            boo_id,
            async_state)

    def create_model_from_doc(self, doc):
        return Boo(doc=doc)


class AsyncBoosRetriever(async_model_actions.AsyncModelsRetriever):

    def __init__(self, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "boo_by_boo_id",
            async_state)

    def create_model_from_doc(self, doc):
        return Boo(doc=doc)


class RequestHandler(tornado.web.RequestHandler):
    """The ```TamperingIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async model I/O classes to operate on persistent instances of
    Boo. Why is this request handler needed? The async model I/O
    classes need to operate in the context of a Tornado I/O loop.
    """

    post_url_spec = r"/boo/(.+)"

    @tornado.web.asynchronous
    def post(self, command):

        if command == "create":
            def on_persist_done(is_ok, is_conflict, ap):
                self.write(json.dumps(self._boo_as_dict(ap.model)))
                self.set_status(httplib.CREATED)
                self.finish()

            boo = Boo(boo_id=uuid.uuid4().hex)
            ap = AsyncBooPersister(boo)
            ap.persist(on_persist_done)
            return

        if command == "get":
            def on_fetch_done(is_ok, boo, abr):
                if boo is None:
                    self.set_status(httplib.NOT_FOUND)
                    self.finish()
                    return

                self.write(json.dumps(self._boo_as_dict(boo)))
                self.set_status(httplib.OK)
                self.finish()

            json_request_body = json.loads(self.request.body)
            boo_id = json_request_body.get("boo_id", None)
            assert boo_id is not None
            abr = AsyncBooRetriever(boo_id)
            abr.fetch(on_fetch_done)
            return

        if command == "get_all":
            def on_fetch_done(is_ok, boos, absr):
                assert boos is not None
                dicts = [self._boo_as_dict(boo) for boo in boos]
                self.write(json.dumps(dicts))
                self.set_status(httplib.OK)
                self.finish()

            absr = AsyncBoosRetriever()
            absr.fetch(on_fetch_done)
            return

        self.set_status(httplib.NOT_FOUND)
        self.finish()

    def _boo_as_dict(self, boo):
        return {
            "_id": boo._id,
            "_rev": boo._rev,
            "boo_id": boo.boo_id,
            "fruit": boo.fruit,
        }


class TamperingIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    @classmethod
    def setUpClass(cls):
        """Setup the integration tests environment. Specifically:

        -- create a temporary database including creating a design doc
        which permits reading persistant instances of Boo
        -- create a tampering signer
        -- configure the async model I/O classes to use the newly
        created tampering signer and temporary database

        """
        # in case a previous test didn't clean itself up delete database
        # totally ignoring the result
        response = requests.delete(_user_store_url)
        # create database
        response = requests.put(_user_store_url)
        assert response.status_code == httplib.CREATED

        # install design doc
        url = "%s/_design/%s" % (_user_store_url, _design_doc_name)
        response = requests.put(
            url,
            data=_design_doc,
            headers={"Content-Type": "application/json; charset=utf8"})
        assert response.status_code == httplib.CREATED

        # get async_model_actions using our temp database
        async_model_actions.user_store = _user_store_url

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
        response = requests.delete(_user_store_url)
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
            persisted_boo = self._get_boo(boo.boo_id)
            self.assertTwoBoosEqual(boo, persisted_boo)

        self.assertTwoCollectionsOfBoosAreEqual(
            boos,
            self._get_all_boos())

        # select one of the Boo's @ random, retrieve the persisted verison
        # of the Boo, tamper with it by changing its fruit and confirm the Boo
        # is no longer retrievable
        boo = boos.pop(random.randint(0, len(boos) - 1))
        self._change_boo_fruit_and_persist(boo)

        self.assertIsNone(self._get_boo(boo.boo_id))
        self.assertTwoCollectionsOfBoosAreEqual(
            boos,
            self._get_all_boos())

        # select one of the Boo's @ random, retrieve the persisted verison
        # of the Boo, tamper with it by removing the Boo's signature
        boo = boos.pop(random.randint(0, len(boos) - 1))
        self._remove_boo_signature_and_persist(boo)

        self.assertIsNone(self._get_boo(boo.boo_id))
        self.assertTwoCollectionsOfBoosAreEqual(
            boos,
            self._get_all_boos())

        # select one of the Boo's @ random, retrieve the persisted verison
        # of the Boo, tamper with it by changing the Boo's signature
        boo = boos.pop(random.randint(0, len(boos) - 1))
        self._change_boo_signature_and_persist(boo)

        self.assertIsNone(self._get_boo(boo.boo_id))
        self.assertTwoCollectionsOfBoosAreEqual(
            boos,
            self._get_all_boos())

    def _create_boo(self):
        """Ask the request handler to create a persistent instance of Boo."""
        body = {
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/boo/create",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.CREATED)
        return Boo(doc=json.loads(response.body))

    def _get_boo(self, boo_id):
        """Ask the request handler to retrieve a persisted Boo."""
        body = {
            "boo_id": boo_id,
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/boo/get",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        if response.code == httplib.NOT_FOUND:
            return None
        self.assertEqual(response.code, httplib.OK)
        return Boo(doc=json.loads(response.body))

    def _get_all_boos(self):
        """Ask the request handler to retrieve all persisted Boos."""
        body = {
        }
        headers = {
            "content-type": "application/json; charset=utf-8",
        }
        response = self.fetch(
            "/boo/get_all",
            method="POST",
            headers=tornado.httputil.HTTPHeaders(headers),
            body=json.dumps(body))
        self.assertEqual(response.code, httplib.OK)
        docs = json.loads(response.body)
        boos = [Boo(doc=doc) for doc in docs]
        return boos

    def _change_boo_fruit_and_persist(self, boo):
        self.assertIsNotNone(boo)

        url = '%s/%s' % (_user_store_url, boo._id)

        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        doc = response.json()
        self.assertIsNotNone(doc)
        fruit = doc.get("fruit", None)
        self.assertIsNotNone(fruit)

        new_fruit = Boo.get_random_fruit(fruit)
        self.assertIsNotNone(new_fruit)
        self.assertNotEqual(fruit, new_fruit)
        doc["fruit"] = new_fruit

        response = requests.put(
            url,
            data=json.dumps(doc),
            headers={"Content-Type": "application/json; charset=utf8"})
        self.assertEqual(response.status_code, httplib.CREATED)

    def _remove_boo_signature_and_persist(self, boo):
        self.assertIsNotNone(boo)

        url = '%s/%s' % (_user_store_url, boo._id)

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

    def _change_boo_signature_and_persist(self, boo):
        self.assertIsNotNone(boo)

        url = '%s/%s' % (_user_store_url, boo._id)

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

    def assertTwoBoosEqual(self, boo, other_boo):
        self.assertIsNotNone(boo)
        self.assertIsNotNone(other_boo)
        self.assertEqual(boo.boo_id, other_boo.boo_id)
        self.assertEqual(boo.fruit, other_boo.fruit)
        self.assertEqual(boo._id, other_boo._id)
        self.assertEqual(boo._rev, other_boo._rev)

    def assertTwoCollectionsOfBoosAreEqual(self, boos, other_boos):
        self.assertIsNotNone(boos)
        self.assertIsNotNone(other_boos)
        self.assertEqual(len(boos), len(other_boos))

        boos_dict = {boo.boo_id: boo for boo in boos}
        other_boos_dict = {boo.boo_id: boo for boo in other_boos}

        # two boo's can't have the same boo_id
        self.assertEqual(len(boos), len(boos_dict))
        self.assertEqual(len(other_boos), len(other_boos_dict))

        for boo in boos:
            other_boo = other_boos_dict.get(boo.boo_id, None)
            self.assertIsNotNone(other_boo)
            self.assertTwoBoosEqual(boo, other_boo)
