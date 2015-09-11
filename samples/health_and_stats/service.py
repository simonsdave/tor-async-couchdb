#!/usr/bin/env python
"""This service implements a simple RESTful service that
demonstrates how tor-async-couchdb's health check capability
was intended to be used.
"""

import httplib
import logging
import optparse
import re
import time

import tornado.httpserver
import tornado.web

from tor_async_couchdb import async_model_actions

_logger = logging.getLogger(__name__)

_true_reg_ex = re.compile(
    "^(true|t|y|yes|1)$",
    re.IGNORECASE)

_false_reg_ex = re.compile(
    "^(false|f|n|no|0)$",
    re.IGNORECASE)


class RequestHandler(tornado.web.RequestHandler):

    url_spec = r"/v1.0/_health"

    @tornado.web.asynchronous
    def get(self):
        acdbhc = async_model_actions.AsyncCouchDBHealthCheck()
        acdbhc.check(self._get_on_acdbhc_check_done)

    def _get_on_acdbhc_check_done(self, is_ok, database_metrics, acdbhc):
        location = "%s://%s%s" % (
            self.request.protocol,
            self.request.host,
            self.request.path,
        )
        body = {
            "status": self._color(is_ok),
            "links": {
                "self": {
                    "href": location,
                },
            },
        }

        if database_metrics:
            body['details'] = {
                "database": {
                    # "status": self._color(is_ok),
                    "docCount": database_metrics.doc_count,
                    "dataSize": database_metrics.data_size,
                    "diskSize": database_metrics.disk_size,
                    "fragmentation": database_metrics.fragmentation,
                    "designDocs": {
                    }
                }
            }
            for design_doc_metrics in database_metrics.design_doc_metrics:
                body["details"]["database"]["designDocs"][design_doc_metrics.design_doc] = {
                    "dataSize": design_doc_metrics.data_size,
                    "diskSize": design_doc_metrics.disk_size,
                    "fragmentation": design_doc_metrics.fragmentation,
                }

        self.write(body)

        self.set_header("location", location)

        self.set_status(httplib.OK if is_ok else httplib.SERVICE_UNAVAILABLE)
        self.finish()

    def _color(self, is_ok):
        return "green" if is_ok else "red"

    def _is_quick(self):
        arg_value = self.get_argument("quick", "y")

        if _true_reg_ex.match(arg_value):
            return True

        if _false_reg_ex.match(arg_value):
            return False

        return None


class CommandLineParser(optparse.OptionParser):

    def __init__(self):
        description = (
            "This service implements a simple RESTful service that "
            "demonstrates how tor-async-couchdb's health check "
            "capability was intended to be used."
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
            RequestHandler.url_spec,
            RequestHandler
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
