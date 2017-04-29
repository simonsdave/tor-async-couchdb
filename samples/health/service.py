#!/usr/bin/env python
"""This app tier service demonstrates how to use tor-async-couchdb
as part of implementing an app tier /_health endpoint.
"""

import httplib
import logging
import optparse
import re
import signal
import sys
import time

import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions
from tor_async_couchdb.async_model_actions import AsyncCouchDBHealthCheck

_logger = logging.getLogger(__name__)


class HealthRequestHandler(tornado.web.RequestHandler):

    _true_reg_ex = re.compile(
        "^(true|t|y|yes|1)$",
        re.IGNORECASE)

    _false_reg_ex = re.compile(
        "^(false|f|n|no|0)$",
        re.IGNORECASE)

    url_spec = r"/v1.0/_health"

    @tornado.web.asynchronous
    def get(self):
        is_quick = self._is_quick()
        if is_quick is None:
            self.set_status(httplib.BAD_REQUEST)
            self.finish()
            return

        if is_quick:
            self._write_response(True)
            return

        acdbhc = AsyncCouchDBHealthCheck()
        acdbhc.check(self._get_on_acdbhc_check_done)

    def _get_on_acdbhc_check_done(self, is_ok, acdbhc):
        self._write_response(is_ok)

    def _write_response(self, is_ok):
        location = "%s://%s%s%s" % (
            self.request.protocol,
            self.request.host,
            self.request.path,
            "?%s" % self.request.query if self.request.query else '',
        )

        body = {
            "status": "green" if is_ok else "red",
            "links": {
                "self": {
                    "href": location,
                },
            },
        }

        self.write(body)

        self.set_header("location", location)

        self.set_status(httplib.OK if is_ok else httplib.SERVICE_UNAVAILABLE)
        self.finish()

    def _is_quick(self):
        arg_value = self.get_argument("quick", "y")

        if type(self)._true_reg_ex.match(arg_value):
            return True

        if type(self)._false_reg_ex.match(arg_value):
            return False

        return None


class CommandLineParser(optparse.OptionParser):

    def __init__(self):
        description = (
            "This app tier service demonstrates how to use tor-async-couchdb"
            "as part of implementing an app tier /_health endpoint."
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
            HealthRequestHandler.url_spec,
            HealthRequestHandler
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
