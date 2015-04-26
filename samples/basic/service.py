#!/usr/bin/env python
"""This service implements a simple RESTful service that
demonstrates how tor-async-couchdb was intended to be used.
"""

import datetime
import httplib
import json
import logging
import optparse
import random
import time
import uuid

import dateutil.parser
import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions
from tor_async_couchdb.model import Model

_logger = logging.getLogger(__name__)


def _utc_now():
    return datetime.datetime.utcnow().replace(tzinfo=dateutil.tz.tzutc())


class Fruit(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if "doc" in kwargs:
            doc = kwargs["doc"]
            self.fruit_id = doc["fruit_id"]
            self.fruit = doc["fruit"]
            self.created_on = dateutil.parser.parse(doc["created_on"])
            self.updated_on = dateutil.parser.parse(doc["updated_on"])
            return

        self.fruit_id = kwargs["fruit_id"]
        self.fruit = kwargs["fruit"]
        utc_now = _utc_now()
        self.created_on = utc_now
        self.updated_on = utc_now

    def as_doc_for_store(self):
        rv = Model.as_doc_for_store(self)
        rv["type"] = "fruit_v1.0"
        rv["fruit_id"] = self.fruit_id
        rv["fruit"] = self.fruit
        rv["created_on"] = self.created_on.isoformat()
        rv["updated_on"] = self.updated_on.isoformat()
        return rv

    def change_fruit(self, fruit):
        self.fruit = fruit
        self.updated_on = _utc_now()

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


class AsyncFruitDeleter(async_model_actions.AsyncDeleter):

    def __init__(self, fruit, async_state=None):
        async_model_actions.AsyncDeleter.__init__(self, fruit, async_state)


class AsyncFruitsRetriever(async_model_actions.AsyncModelsRetriever):

    def __init__(self, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "fruit_by_fruit_id",
            async_state)

    def create_model_from_doc(self, doc):
        return Fruit(doc=doc)


class RequestHandler(tornado.web.RequestHandler):

    def fruit_as_dict_for_response_body(self, fruit):
        return {
            "_id": fruit._id,
            "_rev": fruit._rev,
            "fruit_id": fruit.fruit_id,
            "fruit": fruit.fruit,
            "created_on": fruit.created_on.isoformat(),
            "updated_on": fruit.updated_on.isoformat(),
        }


class MultipleResourcesRequestHandler(RequestHandler):

    url_spec = r"/v1.0/fruits"

    @tornado.web.asynchronous
    def post(self):
        def on_persist_done(is_ok, is_conflict, ap):
            fruit = ap.model
            self.write(json.dumps(self.fruit_as_dict_for_response_body(fruit)))
            self.set_status(httplib.CREATED)
            self.finish()

        fruit = Fruit(fruit_id=uuid.uuid4().hex, fruit=Fruit.get_random_fruit())

        ap = AsyncFruitPersister(fruit)
        ap.persist(on_persist_done)

    @tornado.web.asynchronous
    def get(self):
        def on_fetch_done(is_ok, fruits, absr):
            if not is_ok:
                self.set_status(httplib.INTERNAL_SERVER_ERROR)
                self.finish()
                return

            dicts = [self.fruit_as_dict_for_response_body(fruit) for fruit in fruits]
            self.write(json.dumps(dicts))
            self.set_status(httplib.OK)
            self.finish()

        absr = AsyncFruitsRetriever()
        absr.fetch(on_fetch_done)


class SingleResourceRequestHandler(RequestHandler):

    url_spec = r"/v1.0/fruits/([^/]+)"

    @tornado.web.asynchronous
    def get(self, fruit_id):
        def on_fetch_done(is_ok, fruit, abr):
            if fruit is None:
                self.set_status(httplib.NOT_FOUND)
                self.finish()
                return

            self.write(json.dumps(self.fruit_as_dict_for_response_body(fruit)))
            self.set_status(httplib.OK)
            self.finish()

        abr = AsyncFruitRetriever(fruit_id)
        abr.fetch(on_fetch_done)

    @tornado.web.asynchronous
    def put(self, fruit_id):
        abr = AsyncFruitRetriever(fruit_id)
        abr.fetch(self._put_on_fetch_done)

    def _put_on_fetch_done(self, is_ok, fruit, abr):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
            self.finish()
            return

        fruit.change_fruit(type(fruit).get_random_fruit(fruit.fruit))

        afp = AsyncFruitPersister(fruit)
        afp.persist(self._put_on_async_persist_done)

    def _put_on_async_persist_done(self, is_ok, is_conflict, afp):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        self.write(json.dumps(self.fruit_as_dict_for_response_body(afp.model)))
        self.set_status(httplib.OK)
        self.finish()

    @tornado.web.asynchronous
    def delete(self, fruit_id):
        abr = AsyncFruitRetriever(fruit_id)
        abr.fetch(self._delete_on_fetch_done)

    def _delete_on_fetch_done(self, is_ok, fruit, abr):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
            self.finish()
            return

        afp = AsyncFruitDeleter(fruit)
        afp.delete(self._delete_on_async_delete_done)

    def _delete_on_async_delete_done(self, is_ok, is_conflict, afp):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        self.set_status(httplib.OK)
        self.finish()


class CommandLineParser(optparse.OptionParser):

    def __init__(self):
        description = (
            "This service implements a simple RESTful service that "
            "demonstrates how tor-async-couchdb was intended to be "
            "used."
        )
        optparse.OptionParser.__init__(
            self,
            "usage: %prog [options]",
            description=description)

        default = 8445
        help = "port - default = %s" % default
        self.add_option(
            "--port",
            action="store",
            dest="port",
            default=default,
            type="int",
            help=help)

        default = "127.0.0.1"
        help = "ip - default = %s" % default
        self.add_option(
            "--ip",
            action="store",
            dest="ip",
            default=default,
            type="string",
            help=help)

        default = r"http://127.0.0.1:5984/tor_async_couchdb_sample_basic"
        help = "database - default = %s" % default
        self.add_option(
            "--database",
            action="store",
            dest="database",
            default=default,
            type="string",
            help=help)


if __name__ == "__main__":
    clp = CommandLineParser()
    (clo, cla) = clp.parse_args()

    logging.Formatter.converter = time.gmtime   # remember gmt = utc
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format="%(asctime)s.%(msecs)03d+00:00 %(levelname)s %(module)s %(message)s")

    async_model_actions.database = clo.database

    handlers = [
        (
            MultipleResourcesRequestHandler.url_spec,
            MultipleResourcesRequestHandler
        ),
        (
            SingleResourceRequestHandler.url_spec,
            SingleResourceRequestHandler
        ),
    ]

    settings = {
    }

    app = tornado.web.Application(handlers=handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(port=clo.port, address=clo.ip)

    _logger.info(
        "service started and listening on http://%s:%d talking to database %s",
        clo.ip,
        clo.port,
        clo.database)

    tornado.ioloop.IOLoop.instance().start()
