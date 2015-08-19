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

"""```_doc_type_reg_ex``` is used to verify the format of the
type property for each document before the document is written
to the store.
"""
_doc_type_reg_ex = re.compile(
    r"^[^\s]+_v\d+\.\d+$",
    re.IGNORECASE)


class CouchDBAsyncHTTPRequest(tornado.httpclient.HTTPRequest):
    """```CouchDBAsyncHTTPRequest``` extends ```tornado.httpclient.HTTPRequest```
    adding ...
    """

    def __init__(self, path, method, body_as_dict):
        object.__init__(self)

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

    def __init__(self, expected_response_code, create_model_from_doc):
        object.__init__(self)

        self.expected_response_code = expected_response_code
        self.create_model_from_doc = create_model_from_doc

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
        # by performance analysis tools
        #
        fmt = (
            "CouchDB took %d ms to respond with %d to '%s' "
            "against >>>%s<<<"
        )
        _logger.info(
            fmt,
            response.request_time * 1000,
            response.code,
            response.request.method,
            response.effective_url)

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
        # extract models from response ...
        #
        response_body = json.loads(response.body) if response.body else {}

        models = []
        for row in response_body.get("rows", []):
            doc = row.get("doc", {})
            if tampering_signer:
                if not tamper.verify(tampering_signer, doc):
                    _logger.error(
                        "tampering detected in doc '%s'",
                        doc.get("_id", "?????"))
                    continue
            model = self.create_model_from_doc(doc)
            models.append(model)

        #
        # all done! :-)
        #
        self._call_callback(
            True,       # is_ok
            False,      # is_conflict
            models,
            response_body.get("id", None),
            response_body.get("rev", None))

    def _call_callback(self,
                       is_ok,
                       is_conflict,
                       models=None,
                       _id=None,
                       _rev=None):
        assert self._callback is not None
        self._callback(is_ok, is_conflict, models, _id, _rev, self)
        self._callback = None


class AsyncAction(object):
    """Abstract base class for all async actions."""

    def __init__(self, async_state):
        object.__init__(self)

        self.async_state = async_state


class BaseAsyncModelRetriever(AsyncAction):

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

        The presence of this method is a bit of a hack that was introduced
        when support for "most recent document" type queries was required.
        With this method here it allows derived classes to override the
        implementation and specialize the response for the new query types.

        # it does get the "most recent" style queries implemented:-)
         endkey = json.dumps([self._user.network_id, self._user.user_id])
         startkey = json.dumps([self._user.network_id, self._user.user_id, {}])
         return {
             "include_docs": "true",
             "limit": 1,
             "descending": "true",
             "endkey": endkey,
             "startkey": startkey,
         }

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

        all timestamps a represented as strings with the format "YYYY-MM-DDTHH:MM:SS.MMMMMM+00:00"
        which is important because in this format sorting strings that are actually dates will
        work as you expect
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
        AsyncAction.__init__(self, async_state)

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
        AsyncAction.__init__(self, async_state)

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
        if not _doc_type_reg_ex.match(model_as_doc_for_store["type"]):
            raise InvalidTypeInDocForStoreException(self.model)

        if "_id" in model_as_doc_for_store:
            path = model_as_doc_for_store["_id"]
            method = "PUT"
        else:
            path = ""
            method = "POST"

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
        cac.fetch(request, self._on_cac_fetch_done)

    def _on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, acdba):
        assert is_conflict is False
        self._call_callback(is_ok)

    def _call_callback(self, is_ok):
        assert self._callback is not None
        self._callback(is_ok, self)
        self._callback = None


class Conflict(object):

    """...
    """
    _conflict_resolution_periodic_callback = None

    @classmethod
    def _the_conflict_resolution_periodic_callback(cls):
        """...
        """

        def create_model_from_doc(doc):
            return doc

        # :TODO: place some limit on # of conflicts we'll attempt
        # to resolve in any one shot
        acdba = _AsyncCouchDBAction(
            "_design/conflicts/_view/conflicts?include_docs=true",
            "GET",
            None,                       # body
            httplib.OK,                 # expected_response_code
            create_model_from_doc)
        acdba.fetch(cls._on_cac_fetch_done)

    @classmethod
    def _on_cac_fetch_done(self, is_ok, is_conflict, conflict_docs, _id, _rev, acdba):
        """
            conflicts = []

            for conflict in response.json()["rows"]:
                id = conflict["id"]
                original = get_document_by_id(host, db, id)
                revs_in_conflict = []
                for rev in conflict["key"]:
                    revs_in_conflict.append(get_document_by_id(host, db, id, rev))
                conflicts.append(Conflict(original, revs_in_conflict))

            return conflicts

            {
                "offset": 0,
                "rows": [
                    {
                        "doc": {
                            "_id": "345d17dae686f2b43588108519ffe01b",
                            "_rev": "5-c29587f1652f7eeb88594dcf7faa936a",
                            "doc_id": "7f93a69c0af549488f8aeb31e2fdf240",
                            "ts": "2015-05-06T13:48:42.302830"
                        },
                        "id": "345d17dae686f2b43588108519ffe01b",
                        "key": [
                            "3-b19436151bcdfe0be933ef596a3dad08"
                        ],
                        "value": null
                    }
                ],
                "total_rows": 1
            }
        """

        """
        if not is_ok:
            return

        conflicts = []
        for conflict_doc in conflict_docs:
            current_id = conflict_doc["id"]
            # for conflicting_rev in ...
        """
        pass

    @classmethod
    def start_conflict_resolution(cls):
        if cls._conflict_resolution_periodic_callback:
            return False

        five_minutes_in_milliseconds = 5 * 60 * 1000
        # :TODO: <<<<<< REMOVE ME & TWO LINES BELOW >>>>>
        five_minutes_in_milliseconds = 20 * 1000
        # :TODO: <<<<<< REMOVE ME & TWO LINES ABOVE >>>>>

        cls._conflict_resolution_periodic_callback = tornado.ioloop.PeriodicCallback(
            cls._the_conflict_resolution_periodic_callback,
            five_minutes_in_milliseconds)
        cls._conflict_resolution_periodic_callback.start()

        return True

    @classmethod
    def stop_conflict_resolution(cls):
        """...
        """
        if not cls._conflict_resolution_periodic_callback:
            return False

        cls._conflict_resolution_periodic_callback.stop()
        cls._conflict_resolution_periodic_callback = None

        return True
