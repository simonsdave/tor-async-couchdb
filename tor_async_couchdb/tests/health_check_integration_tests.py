"""Integration tests to verify health checking is working.
Turns out this tests suite is also a pretty good integration
test for the async couchdb framework too:-)

Be warned - this test suite feels complicated.
"""

import httplib
import uuid

import requests
import tornado.testing
import tornado.web

import tor_async_couchdb.async_model_actions


class DatabaseCreator(object):
    """This context manager is useful for encapsulating all the logic
    required to setup and teardown a database. Why not just do this in
    a test's setup and teardown methods? Need to be able to parameterize
    the creation.
    """

    _design_doc_template = (
        '{'
        '    "language": "javascript",'
        '    "views": {'
        '        "%VIEW_NAME%": {'
        '            "map": "function(doc) { if (doc.type.match(/^fruit_v1.0/i)) { emit(doc.fruit_id) } }"'
        '        }'
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
            design_doc = type(self)._design_doc_template.replace(
                "%VIEW_NAME%",
                design_doc_name)
            self.design_docs[design_doc_name] = design_doc

            print "curl %s/_design/%s/_view/%s?include_docs=true" % (
                self.database_url,
                design_doc_name,
                design_doc_name)

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
        tor_async_couchdb.async_model_actions.database = self.database_url

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.delete:
            requests.delete(self.database_url)


class RequestHandler(tornado.web.RequestHandler):
    """The ```HealthCheckIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async health action classes.

    Why is this request handler needed? The async health action
    classes need to operate in the context of a Tornado I/O loop.
    """

    get_url_spec = r"/_health"

    @tornado.web.asynchronous
    def get(self):

        def on_check_done(is_ok, ahc):
            # self.write(json.dumps(self._boo_as_dict(ap.model)))
            self.set_status(httplib.OK if is_ok else httplib.SERVICE_UNAVAILABLE)
            self.finish()

        ahc = tor_async_couchdb.async_model_actions.AsyncCouchDBHealthCheck()
        ahc.check(on_check_done)


class HealthCheckIntegrationTestCase(tornado.testing.AsyncHTTPTestCase):

    def get_app(self):
        handlers = [
            (
                RequestHandler.get_url_spec,
                RequestHandler
            ),
        ]
        return tornado.web.Application(handlers=handlers)

    def test_all_good(self):
        with DatabaseCreator(number_design_docs=5, create=True, delete=True):
            response = self.fetch(RequestHandler.get_url_spec, method="GET")
            self.assertEqual(response.code, httplib.OK)

    def test_should_fail_because_database_does_not_exist(self):
        with DatabaseCreator(number_design_docs=0, create=False, delete=True):
            response = self.fetch(RequestHandler.get_url_spec, method="GET")
            self.assertEqual(response.code, httplib.SERVICE_UNAVAILABLE)
