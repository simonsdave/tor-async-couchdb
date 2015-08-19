#!/usr/bin/env python
"""This service implements a simple RESTful service that
demonstrates how tor-async-couchdb was intended to be used.
"""

import httplib
import json
import logging
import optparse
import time

import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions
from async_actions import AsyncFruitsRetriever
from async_actions import AsyncFruitRetriever
from async_actions import AsyncFruitCreator
from async_actions import AsyncFruitDeleter
from async_actions import AsyncFruitUpdater

_logger = logging.getLogger(__name__)


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
        afc = AsyncFruitCreator()
        afc.create(self._post_on_create_done)

    def _post_on_create_done(self, is_ok, fruit, afc):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return
        self.write(json.dumps(self.fruit_as_dict_for_response_body(fruit)))
        self.set_status(httplib.CREATED)
        self.finish()

    @tornado.web.asynchronous
    def get(self):
        afr = AsyncFruitsRetriever()
        afr.fetch(self._get_on_fetch_done)

    def _get_on_fetch_done(self, is_ok, fruits, afr):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        dicts = [self.fruit_as_dict_for_response_body(fruit) for fruit in fruits]
        self.write(json.dumps(dicts))
        self.set_status(httplib.OK)
        self.finish()


class SingleResourceRequestHandler(RequestHandler):

    url_spec = r"/v1.0/fruits/([^/]+)"

    @tornado.web.asynchronous
    def get(self, fruit_id):
        afr = AsyncFruitRetriever(fruit_id)
        afr.fetch(self._get_on_fetch_done)

    def _get_on_fetch_done(self, is_ok, fruit, afr):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
            self.finish()
            return

        self.write(json.dumps(self.fruit_as_dict_for_response_body(fruit)))
        self.set_status(httplib.OK)
        self.finish()

    @tornado.web.asynchronous
    def put(self, fruit_id):
        afu = AsyncFruitUpdater(fruit_id)
        afu.update(self._put_on_update_done)

    def _put_on_update_done(self, is_ok, fruit, afu):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
            self.finish()
            return

        self.write(json.dumps(self.fruit_as_dict_for_response_body(fruit)))
        self.set_status(httplib.OK)
        self.finish()

    @tornado.web.asynchronous
    def delete(self, fruit_id):
        afd = AsyncFruitDeleter(fruit_id)
        afd.delete(self._delete_on_delete_done)

    def _delete_on_delete_done(self, is_ok, fruit, afd):
        if not is_ok:
            self.set_status(httplib.INTERNAL_SERVER_ERROR)
            self.finish()
            return

        if fruit is None:
            self.set_status(httplib.NOT_FOUND)
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

        default = r"http://127.0.0.1:5984/tor_async_couchdb_sample"
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

    client = "tornado.curl_httpclient.CurlAsyncHTTPClient"
    tornado.httpclient.AsyncHTTPClient.configure(client)

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

    async_model_actions.Conflict.start_conflict_resolution()

    tornado.ioloop.IOLoop.instance().start()
