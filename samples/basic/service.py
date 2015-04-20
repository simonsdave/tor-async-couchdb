#!/usr/bin/env python
"""...
"""

import httplib
import logging
import json
import random
import time
import uuid

import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions
from tor_async_couchdb.model import Model


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

    def as_dict_for_store(self):
        rv = Model.as_dict_for_store(self)
        rv["type"] = "fruit_v1.0"
        rv["fruit_id"] = self.fruit_id
        rv["fruit"] = self.fruit
        return rv

    def choose_new_random_fruit(self):
        self.fruit = type(self).get_random_fruit(self.fruit)

    @classmethod
    def get_random_fruit(cls, but_not_this_fruit=None):
        fruits = ["apple", "pear", "fig", "orange", "kiwi"]
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

    def __init__(self, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class RequestHandler(tornado.web.RequestHandler):

    def fruit_as_dict(self, fruit):
        return {
            "_id": fruit._id,
            "_rev": fruit._rev,
            "fruit_id": fruit.fruit_id,
            "fruit": fruit.fruit,
        }


class CollectionsRequestHandler(RequestHandler):

    url_spec = r"/v1.0/fruits"

    @tornado.web.asynchronous
    def post(self):
        def on_persist_done(is_ok, is_conflict, ap):
            self.write(json.dumps(self.fruit_as_dict(ap.model)))
            self.set_status(httplib.CREATED)
            self.finish()

        fruit = Fruit(fruit_id=uuid.uuid4().hex)
        ap = AsyncFruitPersister(fruit)
        ap.persist(on_persist_done)

    @tornado.web.asynchronous
    def get(self):
        def on_fetch_done(is_ok, fruits, absr):
            if not is_ok:
                self.set_status(httplib.INTERNAL_SERVER_ERROR)
                self.finish()
                return

            dicts = [self.fruit_as_dict(fruit) for fruit in fruits]
            self.write(json.dumps(dicts))
            self.set_status(httplib.OK)
            self.finish()

        absr = AsyncFruitsRetriever()
        absr.fetch(on_fetch_done)


class IndividualsRequestHandler(RequestHandler):

    url_spec = r"/v1.0/fruits/([^/]+)"

    @tornado.web.asynchronous
    def get(self, fruit_id):
        def on_fetch_done(is_ok, fruit, abr):
            if fruit is None:
                self.set_status(httplib.NOT_FOUND)
                self.finish()
                return

            self.write(json.dumps(self.fruit_as_dict(fruit)))
            self.set_status(httplib.OK)
            self.finish()

        abr = AsyncFruitRetriever(fruit_id)
        abr.fetch(on_fetch_done)

    @tornado.web.asynchronous
    def put(self, fruit_id):
        abr = AsyncFruitRetriever(fruit_id)
        abr.fetch(self._put_on_fetch_done)

    def _put_on_fetch_done(self, is_ok, fruit, abr):
        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
            self.finish()
            return

        fruit.choose_new_random_fruit()

        afp = AsyncFruitPersister(fruit)
        afp.persist(self._put_on_async_persist_done)

    def _put_on_async_persist_done(self, is_ok, is_conflict, afp):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        self.write(json.dumps(self.fruit_as_dict(afp.model)))
        self.set_status(httplib.OK)
        self.finish()


if __name__ == "__main__":

    # configure logging
    logging.Formatter.converter = time.gmtime # remember gmt = utc
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format="%(asctime)s.%(msecs)03d+00:00 %(levelname)s %(module)s %(message)s")

    # get async_model_actions using our temp database
    async_model_actions.database = r"http://127.0.0.1:5984/tor_async_couchdb_sample_basic"

    handlers = [
        (
            CollectionsRequestHandler.url_spec,
            CollectionsRequestHandler
        ),
        (
            IndividualsRequestHandler.url_spec,
            IndividualsRequestHandler
        ),
    ]

    settings = {
    }

    app = tornado.web.Application(handlers=handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(port=2525, address="127.0.0.1")

    tornado.ioloop.IOLoop.instance().start()
