#!/usr/bin/env python
"""This app tier service demonstrates how to use tor-async-couchdb
as part of implementing an app tier /_metrics endpoint.
"""

import httplib
import logging
import optparse
import signal
import sys
import time

import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions
from tor_async_couchdb.async_model_actions import AsyncDatabaseMetricsRetriever

_logger = logging.getLogger(__name__)


class MetricsRequestHandler(tornado.web.RequestHandler):

    url_spec = r"/v1.0/_metrics"

    @tornado.web.asynchronous
    def get(self):
        adbmr = AsyncDatabaseMetricsRetriever()
        adbmr.fetch(self._on_adbmr_fetch_done)

    def _on_adbmr_fetch_done(self, is_ok, database_metrics, adbmr):
        location = "%s://%s%s" % (
            self.request.protocol,
            self.request.host,
            self.request.path,
        )
        body = {
            "links": {
                "self": {
                    "href": location,
                },
            },
        }

        if database_metrics:
            body['database'] = {
                "docCount": database_metrics.doc_count,
                "dataSize": database_metrics.data_size,
                "diskSize": database_metrics.disk_size,
                "fragmentation": database_metrics.fragmentation,
                "views": {
                }
            }
            for view_metrics in database_metrics.view_metrics:
                body["database"]["views"][view_metrics.design_doc] = {
                    "dataSize": view_metrics.data_size,
                    "diskSize": view_metrics.disk_size,
                    "fragmentation": view_metrics.fragmentation,
                }

        self.write(body)

        self.set_header("location", location)

        self.set_status(httplib.OK if is_ok else httplib.SERVICE_UNAVAILABLE)
        self.finish()


class CommandLineParser(optparse.OptionParser):

    def __init__(self):
        description = (
            "This app tier service demonstrates how to use tor-async-couchdb"
            "as part of implementing an app tier /_metrics endpoint."
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


def _sigint_handler(signal_number, frame):
    assert signal_number == signal.SIGINT
    _logger.info("Shutting down ...")
    sys.exit(0)


if __name__ == "__main__":
    clp = CommandLineParser()
    (clo, cla) = clp.parse_args()

    logging.Formatter.converter = time.gmtime   # remember gmt = utc
    logging.basicConfig(
        level=logging.INFO,
        datefmt="%Y-%m-%dT%H:%M:%S",
        format="%(asctime)s.%(msecs)03d+00:00 %(levelname)s %(module)s %(message)s")

    async_model_actions.database = clo.database

    signal.signal(signal.SIGINT, _sigint_handler)

    handlers = [
        (
            MetricsRequestHandler.url_spec,
            MetricsRequestHandler
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

    tornado.ioloop.IOLoop.instance().start()
