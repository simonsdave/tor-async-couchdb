"""Integration tests to verify metrics retrieval is working.
Turns out this tests suite is also a pretty good integration
test for the async couchdb framework too:-)

Be warned - this test suite feels complicated.
"""

import httplib
import uuid

import nose.plugins.attrib
import requests
import tornado.testing
import tornado.web

from .. import async_model_actions


class DatabaseCreator(object):
    """This context manager is useful for encapsulating all the logic
    required to setup and teardown a database. Why not just do this in
    a test's setup and teardown methods? Need to be able to parameterize
    the creation.
    """

    _design_doc_template_with_view = (
        '{'
        '    "language": "javascript",'
        '    "views": {'
        '        "%VIEW_NAME%": {'
        '            "map": "function(doc) { if (doc.type.match(/^fruit_v1.0/i)) { emit(doc.fruit_id, null) } }"'
        '        }'
        '    }'
        '}'
    )

    _design_doc_template_with_no_view = (
        '{'
        '    "language": "javascript",'
        '    "shows": {'
        '       "fruitasheading": "function(doc, req) { return \'<h1>\' + doc.fruit + \'</h1>\' }"'
        '    }'
        '}'
    )

    def __init__(self, number_design_docs=1, create=True, delete=True):
        self.create = create
        self.delete = delete
        self.database_url = r"http://127.0.0.1:5984/a%s" % uuid.uuid4().hex

        self.design_docs = {}
        for i in range(0, number_design_docs):
            design_doc_name = "fruit_by_fruit_id_%05d" % i
            if i % 2 == 0:
                design_doc = type(self)._design_doc_template_with_view.replace(
                    "%VIEW_NAME%",
                    design_doc_name)
            else:
                design_doc = type(self)._design_doc_template_with_no_view
            self.design_docs[design_doc_name] = design_doc

    def __enter__(self):
        """Setup the integration tests environment. Specifically:

        -- if there's already a database around with the desired
        name then delete that database
        -- create a temporary database including creating a design doc
        which permits reading persistant instances of Boo
        -- configure the async model I/O classes to use the newly
        created temporary database
        """
        # in case a previous test didn't clean itself up delete database
        # totally ignoring the result
        if self.delete:
            response = requests.delete(self.database_url)

        # create database
        if self.create:
            response = requests.put(self.database_url)
            assert response.status_code == httplib.CREATED

            # install design docs
            for (design_doc_name, design_doc) in self.design_docs.items():
                url = "%s/_design/%s" % (self.database_url, design_doc_name)
                response = requests.put(
                    url,
                    data=design_doc,
                    headers={"Content-Type": "application/json; charset=utf8"})
                assert response.status_code == httplib.CREATED

        # connect async actions to our temp database
        async_model_actions.database = self.database_url

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.delete:
            requests.delete(self.database_url)


class RequestHandler(tornado.web.RequestHandler):
    """The ```DatabaseMetricsIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async metrics action classes.

    Why is this request handler needed? The async health action
    classes need to operate in the context of a Tornado I/O loop.
    """

    get_url_spec = r"/_stats"

    @tornado.web.asynchronous
    def get(self):

        def on_fetch_done(is_ok, view_metrics, aavmr):
            self.set_status(httplib.OK if is_ok else httplib.INTERNAL_SERVER_ERROR)
            self.finish()

        aavmr = async_model_actions.AsyncAllViewMetricsRetriever()
        aavmr.fetch(on_fetch_done)


@nose.plugins.attrib.attr('integration')
class DatabaseMetricsIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        handlers = [
            (
                RequestHandler.get_url_spec,
                RequestHandler
            ),
        ]
        return tornado.web.Application(handlers=handlers)

    def test_all_good(self):
        with DatabaseCreator(number_design_docs=20, create=True, delete=True):
            response = self.fetch(RequestHandler.get_url_spec, method="GET")
            self.assertEqual(response.code, httplib.OK)
