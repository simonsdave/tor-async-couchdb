"""This module contains a collection of classes that implement
Tornado async actions against CouchDB.
"""

import httplib
import json
import logging
import re
import urllib

import tornado.httputil
import tornado.httpclient
import tornado.ioloop

import tamper


_logger = logging.getLogger("async_actions.%s" % __name__)

"""```database``` points to a CouchDB database. By default it
points to a local CouchDB database. It is expected that the
service's mainline will update this configuration.
"""
database = "http://127.0.0.1:5984/database"

"""If not None, ```tampering_signer``` is the keyczar signer
used to enforce tampering proofing of the CouchDB database.
"""
tampering_signer = None

"""If CouchDB requires basic authentication in order
to access it then set ```username``` and ```password``` to
appropriate non-None values.
"""
username = None
password = None

"""Certificate validation will be performned if ```validate_cert```
is ```True``` and we're interacting with CouchDB over TLS/SSL (ie
```database``` points to a URL starting with https).
This config option is very useful when CouchDB self-signed certs.
"""
validate_cert = True


def _fragmentation(data_size, disk_size):
    """Think of the fragmentation metric is that it's
    a measure of the % of the database or view that's used
    to store old documents and their associated metadata.

    See
    https://wiki.apache.org/couchdb/Compaction
    and
    http://docs.couchdb.org/en/latest/config/compaction.html#compaction-daemon-rules
    for details on fragmentation calculation.
    """
    if data_size is None or disk_size is None:
        return None
    fragmentation = ((disk_size - float(data_size)) / disk_size) * 100.0
    return int(round(fragmentation, 0))


class CouchDBAsyncHTTPRequest(tornado.httpclient.HTTPRequest):
    """```CouchDBAsyncHTTPRequest``` extends ```tornado.httpclient.HTTPRequest```
    adding ...
    """

    def __init__(self, path, method, body_as_dict):
        assert not path.startswith('/')

        url = "%s/%s" % (database, path)

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "charset=utf8",
        }

        if body_as_dict is not None:
            if tampering_signer:
                tamper.sign(tampering_signer, body_as_dict)
            body = json.dumps(body_as_dict)
            headers["Content-Type"] = "application/json; charset=utf8"
        else:
            body = None

        auth_mode = "basic" if username or password else None

        tornado.httpclient.HTTPRequest.__init__(
            self,
            url,
            method=method,
            body=body,
            headers=tornado.httputil.HTTPHeaders(headers),
            validate_cert=validate_cert,
            auth_mode=auth_mode,
            auth_username=username,
            auth_password=password)


class CouchDBAsyncHTTPClient(object):
    """```CouchDBAsyncHTTPClient``` wraps
    ```tornado.httpclient.AsyncHTTPClient``` by adding standardized
    logging of error messages and calculating LCP response times
    for subsequent use in performance analysis and health monitoring.
    """

    def __init__(self,
                 expected_response_code,
                 create_model_from_doc,
                 expect_one_document=False):
        object.__init__(self)

        self.expected_response_code = expected_response_code
        self.create_model_from_doc = create_model_from_doc
        self.expect_one_document = expect_one_document

        self._callback = None

    def fetch(self, request, callback):
        """fetch() is perhaps not the best name but it matches
        the key method in the async HTTP client classs:-).
        """
        assert self._callback is None
        self._callback = callback

        http_client = tornado.httpclient.AsyncHTTPClient()
        http_client.fetch(
            request,
            callback=self._on_http_client_fetch_done)

    def _on_http_client_fetch_done(self, response):
        #
        # write a message to the log which can be easily parsed
        # by performance analysis tools and used to understand
        # performance bottlenecks.
        #
        # http://tornado.readthedocs.org/en/latest/httpclient.html#response-objects
        # explains that the time_info attribute of a tornado response
        # object contains timing details of the phases of a request which
        # is available when using the cURL http client. a description
        # of these timing details can be found at
        # http://curl.haxx.se/libcurl/c/curl_easy_getinfo.html#TIMES
        #
        fmt = (
            "CouchDB took {request_time:.2f} ms to respond "
            "with {http_response_code:d} to '{http_method}' "
            "against >>>{url}<<< - timing detail: "
            "q={queue:.2f} ms n={namelookup:.2f} ms "
            "c={connect:.2f} ms p={pretransfer:.2f} ms "
            "s={starttransfer:.2f} ms t={total:.2f} ms r={redirect:.2f} ms"
        )
        msg_format_args = {
            "request_time": response.request_time * 1000,
            "http_response_code": response.code,
            "http_method": response.request.method,
            "url": response.effective_url,
        }

        def add_time_info_to_msg_format_args(key):
            msg_format_args[key] = response.time_info.get(key, 0) * 1000

        add_time_info_to_msg_format_args("queue")
        add_time_info_to_msg_format_args("namelookup")
        add_time_info_to_msg_format_args("connect")
        add_time_info_to_msg_format_args("pretransfer")
        add_time_info_to_msg_format_args("starttransfer")
        add_time_info_to_msg_format_args("total")
        add_time_info_to_msg_format_args("redirect")

        msg = fmt.format(**msg_format_args)

        _logger.info(msg)

        #
        # check for errors ...
        #
        if response.code != self.expected_response_code:
            if response.code == httplib.CONFLICT:
                self._call_callback(False, True)
                return

            fmt = (
                "CouchDB responded to %s on %s "
                "with HTTP response %d but expected %d"
            )
            _logger.error(
                fmt,
                response.request.method,
                response.effective_url,
                response.code,
                self.expected_response_code)
            self._call_callback(False, False)
            return

        if response.error:
            _logger.error(
                "CouchDB responded to %s on %s with error '%s'",
                response.request.method,
                response.effective_url,
                response.error)
            self._call_callback(False, False)
            return

        #
        # process response body ...
        #

        #
        # CouchDB always returns response.body (a string) - let's convert the
        # body to a dict so we can operate on it more effectively
        #
        response_body = json.loads(response.body) if response.body else {}

        #
        # the response body either contains a bunch of documents that
        # need to be converted to model objects or a single document
        #
        if not self.create_model_from_doc:
            self._call_callback(
                True,               # is_ok
                False,              # is_conflict
                response_body,
                response_body.get("id", None),
                response_body.get("rev", None))
            return

        if self.expect_one_document:
            model = self._check_doc_for_tampering_and_if_ok_create_model(response_body)
            self._call_callback(
                model is not None,
                False,              # is_conflict
                model)
            return

        models = []
        for row in response_body.get("rows", []):
            doc = row.get("doc", {})
            model = self._check_doc_for_tampering_and_if_ok_create_model(doc)
            if model is not None:
                models.append(model)

        self._call_callback(
            True,                   # is_ok
            False,                  # is_conflict
            models)

    def _check_doc_for_tampering_and_if_ok_create_model(self, doc):
        if tampering_signer:
            if not tamper.verify(tampering_signer, doc):
                _logger.error(
                    "tampering detected in doc '%s'",
                    doc["_id"])
                return None
        return self.create_model_from_doc(doc)

    def _call_callback(self,
                       is_ok,
                       is_conflict,
                       model_models_or_response_body=None,
                       _id=None,
                       _rev=None):
        assert self._callback is not None
        self._callback(
            is_ok,
            is_conflict,
            model_models_or_response_body,
            _id,
            _rev,
            self)
        self._callback = None


class AsyncAction(object):
    """Abstract base class for all async actions."""

    def __init__(self, async_state):
        object.__init__(self)

        self.async_state = async_state


class AsyncModelRetrieverByDocumentID(AsyncAction):
    """Async'ly retrieve a model from the CouchDB database
    by document ID.
    """

    def __init__(self, document_id, async_state):
        AsyncAction.__init__(self, async_state)

        self.document_id = document_id

        self._callback = None

    def fetch(self, callback):
        assert self._callback is None
        self._callback = callback

        request = CouchDBAsyncHTTPRequest(self.document_id, 'GET', None)

        cac = CouchDBAsyncHTTPClient(
            httplib.OK,                     # expected_response_code
            self.create_model_from_doc,
            True)                           # expect_one_document
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, model, _id, _rev, cac):
        assert is_conflict is False
        self._call_callback(is_ok, model)

    def create_model_from_doc(self, doc):
        """Concrete classes derived from this class must implement
        this method which takes a dictionary (```doc```) and creates
        a model instance.
        """
        raise NotImplementedError()

    def _call_callback(self, is_ok, model=None):
        assert self._callback
        self._callback(is_ok, model, self)
        self._callback = None


class BaseAsyncModelRetriever(AsyncAction):

    def __init__(self, async_state):
        AsyncAction.__init__(self, async_state)

        self._callback = None

    def fetch(self, callback):
        assert self._callback is None
        self._callback = callback

        #
        # useful when trying to figure out URL encodings
        #
        #   http://meyerweb.com/eric/tools/dencoder/
        #
        # and when thinking about array keys
        #
        #   http://stackoverflow.com/questions/9687297/couchdb-search-or-filtering-on-key-array
        #
        path_fmt = '_design/%s/_view/%s?%s'
        query_string_key_value_pairs = self.get_query_string_key_value_pairs()
        query_string = urllib.urlencode(query_string_key_value_pairs)
        # :ASSUMPTION: that design docs and views are called the same thing
        # ie one view per design doc
        path = path_fmt % (self.design_doc, self.design_doc, query_string)

        request = CouchDBAsyncHTTPRequest(path, "GET", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, self.create_model_from_doc)
        cac.fetch(request, self.on_cac_fetch_done)

    def get_query_string_key_value_pairs(self):
        """This method is only called by ```fetch()``` to get the key value
        pairs that will be used to construct the query string in the request
        to CouchDB.

        The presence of this method was first introduced when support for
        "most recent document" type queries was required.

        Below is an example implementation for a rather complex scaneario
        where the keys are composite and we have a "most recent" style
        query type.

            def get_query_string_key_value_pairs(self):
                endkey = json.dumps([self._user.network_id, self._user.user_id])
                startkey = json.dumps([self._user.network_id, self._user.user_id, {}])
                return {
                     "include_docs": "true",
                     "limit": 1,
                     "descending": "true",
                     "endkey": endkey,
                     "startkey": startkey,
                }

        Below is the JavaScript design document that would support the
        above implementation.

            {
                "language": "javascript",
                "views": {
                    "member_details_by_network_id_user_id_and_created_on": {
                        "map": "function(doc) {
                            if (doc.type.match(/^member_details_v\\d+.\\d+/i)) {
                                emit([doc.network_id, doc.user_id, doc.created_on], null)
                            }
                        }"
                    }
                }
            }

        Note - all timestamps are expected to be represented as strings with
        the format YYYY-MM-DDTHH:MM:SS.MMMMMM+00:00 which is important because
        with this format sorting strings that are actually dates will work as
        you expect
        """
        raise NotImplementedError()

    def on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
        raise NotImplementedError()

    def create_model_from_doc(self, doc):
        """Concrete classes derived from this class must implement
        this method which takes a dictionary (```doc```) and creates
        a model instance.
        """
        raise NotImplementedError()


class AsyncModelRetriever(BaseAsyncModelRetriever):
    """Async'ly retrieve a model from the CouchDB database."""

    def __init__(self, design_doc, key, async_state):
        BaseAsyncModelRetriever.__init__(self, async_state)

        self.design_doc = design_doc
        self.key = key

        self._callback = None

    def get_query_string_key_value_pairs(self):
        return {
            "include_docs": "true",
            "key": json.dumps(self.key),
        }

    def on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
        assert is_conflict is False
        model = models[0] if models else None
        self._call_callback(is_ok, model)

    def _call_callback(self, is_ok, model=None):
        assert self._callback
        self._callback(is_ok, model, self)
        self._callback = None


class AsyncModelsRetriever(BaseAsyncModelRetriever):
    """Async'ly retrieve a collection of models from CouchDB."""

    def __init__(self, design_doc, start_key=None, end_key=None, async_state=None):
        BaseAsyncModelRetriever.__init__(self, async_state)

        self.design_doc = design_doc
        self.start_key = start_key
        self.end_key = end_key

        self._callback = None

    def get_query_string_key_value_pairs(self):
        query_params = {
            "include_docs": "true",
        }
        if self.start_key:
            query_params['startkey'] = json.dumps(self.start_key)
        if self.end_key:
            query_params['endkey'] = json.dumps(self.end_key)
        return query_params

    def transform_models(self, models):
        """By default the ```callback``` in ```fetch``` will recieve
        a list of models. Sometimes is useful to do a transformation
        on the list and have ```callback``` recieve the transformation
        rather than the list. For example, let's say you had a collection
        of models with the property x and you wanted to return a
        dictionary keyed by x. In this scenario you'd augment the
        derived class of ```AsyncModelsRetriever``` with something
        like:

            def transform_models(self, models):
                return {model.x: model for model in models}

        Don't expect this to be used too much but very useful when
        it is used:-)
        """
        return models

    def on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
        assert is_conflict is False
        self._call_callback(is_ok, models)

    def _call_callback(self, is_ok, models=None):
        assert self._callback is not None
        self._callback(is_ok, self.transform_models(models), self)
        self._callback = None


class InvalidTypeInDocForStoreException(Exception):
    """This exception is raised by ```AsyncPersister``` when
    a call to a model's as_doc_for_store() generates a doc
    with an invalid type property.
    """

    def __init__(self, model):
        msg_fmt = (
            "invalid 'type' in doc for store - "
            "see '%s.as_doc_for_store()"
        )
        msg = msg_fmt % type(model)
        Exception.__init__(self, msg)


class AsyncPersister(AsyncAction):
    """Async'ly persist a model object."""

    """```_doc_type_reg_ex``` is used to verify the format of the
    type property for each document before the document is written
    to the store.
    """
    _doc_type_reg_ex = re.compile(
        r"^[^\s]+_v\d+\.\d+$",
        re.IGNORECASE)

    def __init__(self, model, model_as_doc_for_store_args, async_state):
        AsyncAction.__init__(self, async_state)

        self.model = model
        self.model_as_doc_for_store_args = model_as_doc_for_store_args

        self._callback = None

    def persist(self, callback):
        assert not self._callback
        self._callback = callback

        model_as_doc_for_store = self.model.as_doc_for_store(*self.model_as_doc_for_store_args)

        #
        # this check is important because the conflict resolution
        # logic relies on being able to extract the type name from
        # a document read from the store
        #
        if not type(self)._doc_type_reg_ex.match(model_as_doc_for_store['type']):
            raise InvalidTypeInDocForStoreException(self.model)

        if '_id' in model_as_doc_for_store:
            path = model_as_doc_for_store['_id']
            method = 'PUT'
        else:
            path = ''
            method = 'POST'

        request = CouchDBAsyncHTTPRequest(path, method, model_as_doc_for_store)

        cac = CouchDBAsyncHTTPClient(httplib.CREATED, None)
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
        """```self.model``` has just been written to a CouchDB database which
        means ```self.model```'s _id and _rev properties might be out of
        sync with the _id and _rev properties in CouchDB since CouchDB
        generates these values. The "if _id" and "if _rev"
        sections of code below unite the in-memory view and the CouchDB
        view of this object/document.
        """
        if _id is not None:
            self.model._id = _id

        if _rev is not None:
            self.model._rev = _rev

        self._call_callback(is_ok, is_conflict)

    def _call_callback(self, is_ok, is_conflict):
        assert self._callback is not None
        assert (is_ok and not is_conflict) or (not is_ok)
        self._callback(is_ok, is_conflict, self)
        self._callback = None


class AsyncDeleter(AsyncAction):
    """Async'ly delete a model object."""

    def __init__(self, model, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.model = model

        self._callback = None

    def delete(self, callback):
        assert not self._callback
        self._callback = callback

        if not self.model._id or not self.model._rev:
            self._call_callback(False, False)
            return

        path = "%s?rev=%s" % (self.model._id, self.model._rev)
        request = CouchDBAsyncHTTPRequest(path, "DELETE", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, None)
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
        self._call_callback(is_ok, is_conflict)

    def _call_callback(self, is_ok, is_conflict):
        assert self._callback is not None
        assert (is_ok and not is_conflict) or (not is_ok)
        self._callback(is_ok, is_conflict, self)
        self._callback = None


class AsyncCouchDBHealthCheck(AsyncAction):
    """Async'ly confirm CouchDB can be reached."""

    def __init__(self, async_state=None):
        AsyncAction.__init__(self, async_state)

        self._callback = None

    def check(self, callback):
        assert not self._callback
        self._callback = callback

        request = CouchDBAsyncHTTPRequest("", "GET", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, None)
        cac.fetch(request, self._on_cac_db_fetch_done)

    def _on_cac_db_fetch_done(self, is_ok, is_conflict, response_body, _id, _rev, cac):
        self._call_callback(is_ok)

    def _call_callback(self, is_ok):
        assert self._callback is not None
        self._callback(is_ok, self)
        self._callback = None


class ViewMetrics(object):
    """An instance of this class contains metrics which describe
    both the shape and health of a view in a CouchDB databse.
    Instances of this class are created by ```AsyncViewMetricsRetriever```.
    """

    def __init__(self, design_doc, data_size, disk_size):
        object.__init__(self)

        self.design_doc = design_doc
        self.data_size = data_size
        self.disk_size = disk_size

    @property
    def fragmentation(self):
        """The view's fragmentation as an integer percentage."""
        return _fragmentation(self.data_size, self.disk_size)


class DatabaseMetrics(object):
    """An instance of this class contains metrics which describe
    both the shape and health of a CouchDB databse. Instances of
    this class are created by ```AsyncDatabaseMetricsRetriever```.
    """

    def __init__(self, database, doc_count, data_size, disk_size, view_metrics):
        object.__init__(self)

        self.database = database
        self.doc_count = doc_count
        self.data_size = data_size
        self.disk_size = disk_size
        self.view_metrics = view_metrics

    @property
    def fragmentation(self):
        """The database's fragmentation as an integer percentage."""
        return _fragmentation(self.data_size, self.disk_size)


class AsyncDatabaseMetricsRetriever(AsyncAction):
    """Async'ly retrieve metrics for the CouchDB database."""

    # FDD = Fetch Failure Details
    FFD_OK = 0x0000
    FFD_ERROR = 0x0080
    FFD_ERROR_TALKING_TO_COUCHDB = FFD_ERROR | 0x0001
    FFD_ERROR_GETTING_VIEW_METRICS = FFD_ERROR | 0x0002

    def __init__(self, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.fetch_failure_detail = None

        self._callback = None

    def fetch(self, callback):
        assert not self._callback
        self._callback = callback

        request = CouchDBAsyncHTTPRequest("", "GET", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, None)
        cac.fetch(request, self._on_cac_db_fetch_done)

    def _on_cac_db_fetch_done(self, is_ok, is_conflict, response_body, _id, _rev, acdba):
        assert is_conflict is False
        if not is_ok:
            self._call_callback(type(self).FFD_ERROR_TALKING_TO_COUCHDB)
            return

        async_state = (
            response_body.get("doc_count"),
            response_body.get("data_size"),
            response_body.get("disk_size"),
        )
        aaddmr = AsyncAllViewMetricsRetriever(async_state)
        aaddmr.fetch(self._on_aaddmr_fetch_done)

    def _on_aaddmr_fetch_done(self, is_ok, view_metrics, aaddmr):
        if not is_ok:
            self._call_callback(type(self).FFD_ERROR_GETTING_VIEW_METRICS)
            return

        (doc_count, data_size, disk_size) = aaddmr.async_state
        database_metrics = DatabaseMetrics(
            database,
            doc_count,
            data_size,
            disk_size,
            view_metrics)
        self._call_callback(type(self).FFD_OK, database_metrics)

    def _call_callback(self, fetch_failure_detail, database_metrics=None):
        assert self._callback is not None
        assert self.fetch_failure_detail is None
        self.fetch_failure_detail = fetch_failure_detail
        is_ok = not bool(self.fetch_failure_detail & type(self).FFD_ERROR)
        self._callback(
            is_ok,
            database_metrics if is_ok else None,
            self)
        self._callback = None


class AsyncAllViewMetricsRetriever(AsyncAction):
    """Async'ly retrieve metrics for all views in a database."""

    # FDD = Fetch Failure Details
    FFD_OK = 0x0000
    FFD_ERROR = 0x0080
    FFD_ERROR_TALKING_TO_COUCHDB = FFD_ERROR | 0x0001
    FFD_ERROR_FETCHING_VIEW_METRICS = FFD_ERROR | 0x0002
    FFD_NO_DESIGN_DOCS_IN_DATABASE = 0x0003

    def __init__(self, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.fetch_failure_detail = None

        self._todo = []
        self._done = []
        self._callback = None

    def fetch(self, callback):
        assert not self._callback
        self._callback = callback

        #
        # try something like this to get a sense of the response
        #
        #   curl 'http://127.0.0.1:5984/database/_all_docs?startkey="_design"&endkey="_design0"' | python -m json.tool
        #
        # and just remember to replace "database" in the above request. the
        # output will look something like:
        #
        # {
        #     "offset": 2,
        #     "rows": [
        #         {
        #             "id": "_design/fruit_by_fruit_id",
        #             "key": "_design/fruit_by_fruit_id",
        #             "value": {
        #                 "rev": "1-446934fdc8cd18bee9db4b9df095074a"
        #             }
        #         }
        #     ],
        #     "total_rows": 3
        # }
        #
        path = '_all_docs?startkey="_design"&endkey="_design0"'
        request = CouchDBAsyncHTTPRequest(path, "GET", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, None)
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, response_body, _id, _rev, acdba):
        assert is_conflict is False
        if not is_ok:
            self._call_callback(type(self).FFD_ERROR_TALKING_TO_COUCHDB)
            return

        rows = response_body.get("rows", [])
        if not rows:
            self._call_callback(type(self).FFD_NO_DESIGN_DOCS_IN_DATABASE)
            return

        for row in rows:
            design_doc = row["key"].split("/")[1]
            self._todo.append(design_doc)
            avmr = AsyncViewMetricsRetriever(design_doc)
            avmr.fetch(self._on_avmr_fetch_done)

    def _on_avmr_fetch_done(self, is_ok, view_metrics, avmr):
        if not is_ok:
            self._call_callback(type(self).FFD_ERROR_FETCHING_VIEW_METRICS)
            return

        self._todo.remove(view_metrics.design_doc)
        self._done.append(view_metrics)

        self._call_callback(type(self).FFD_OK)

    def _call_callback(self, fetch_failure_detail):
        if not self._callback:
            # results have already been sent to caller even though
            # we're still getting responses back from CouchDB
            return

        is_ok = not bool(fetch_failure_detail & type(self).FFD_ERROR)

        if not is_ok:
            assert self.fetch_failure_detail is None
            self.fetch_failure_detail = fetch_failure_detail
            self._callback(False, None, self)
            self._callback = None
            return

        if self._todo:
            return

        assert self.fetch_failure_detail is None
        self.fetch_failure_detail = fetch_failure_detail
        self._callback(True, self._done, self)
        self._callback = None


class AsyncViewMetricsRetriever(AsyncAction):
    """Async'ly retrieve metrics for a single view."""

    # FDD = Fetch Failure Details
    FFD_OK = 0x0000
    FFD_ERROR = 0x0080
    FFD_ERROR_TALKING_TO_COUCHDB = FFD_ERROR | 0x0001
    FFD_INVALID_RESPONSE_BODY = 0x0002

    def __init__(self, design_doc, async_state=None):
        AsyncAction.__init__(self, async_state)

        self.design_doc = design_doc
        self.fetch_failure_detail = None

        self._callback = None

    def fetch(self, callback):
        assert not self._callback
        self._callback = callback

        path = '_design/%s/_info' % self.design_doc
        request = CouchDBAsyncHTTPRequest(path, "GET", None)

        cac = CouchDBAsyncHTTPClient(httplib.OK, None)
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, response_body, _id, _rev, cac):
        assert is_conflict is False
        if not is_ok:
            self._call_callback(type(self).FFD_ERROR_TALKING_TO_COUCHDB)
            return

        view_index = response_body.get('view_index', {})
        data_size = view_index.get('data_size')
        disk_size = view_index.get('disk_size')
        cls = type(self)
        self._call_callback(
            cls.FFD_OK if data_size is not None and disk_size is not None else cls.FFD_INVALID_RESPONSE_BODY,
            data_size,
            disk_size)

    def _call_callback(self, fetch_failure_detail, data_size=None, disk_size=None):
        assert self._callback is not None
        assert self.fetch_failure_detail is None
        self.fetch_failure_detail = fetch_failure_detail
        is_ok = not bool(self.fetch_failure_detail & type(self).FFD_ERROR)
        self._callback(
            is_ok,
            ViewMetrics(self.design_doc, data_size, disk_size) if is_ok else None,
            self)
        self._callback = None
