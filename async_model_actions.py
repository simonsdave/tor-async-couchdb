"""This module contains a collection of classes that implement
async actions against the User Store (implemented using CouchDB).
"""

import hashlib
import httplib
import json
import logging
import urllib

import tornado.httputil
import tornado.httpclient

import tamper

_logger = logging.getLogger("async_actions.%s" % __name__)

"""```user_store``` points to the User Store. By default it
points to a local CouchDB database. It is expected that the
service's mainline will update this configuration.
"""
user_store = "http://127.0.0.1:5984/identity_service_user_store"

"""If not None, ```tampering_signer``` is the keyczar signer
used to enforce tampering proofing of the User Store.
"""
tampering_signer = None

"""If the User Store requires basic authentication in order
to access it then set ```username``` and ```password``` to
appropriate non-None values.
"""
username = None
password = None

"""Return the boolean value of the user_service / user_store_validate_cert
configuration option. By default (ie of the setting doesn't appear
in the configuration file) True will be returned. This config
option proved very useful when the user service made requests to
the user store's SSL end-point that was using self-signed certs.
"""
validate_cert = True


class AsyncAction(object):
    """Abstract base class for all async actions."""

    def __init__(self, async_state):
        object.__init__(self)

        self.async_state = async_state


class _AsyncUserStoreAction(AsyncAction):
    """```_AsyncUserStoreAction``` used to be an abstract base
    class for all async interactions with the user store. However
    when it came time to unit tests derived classes it was really
    obvious that it was better to use composition rather than
    implemntation inheritance.
    """

    def __init__(self,
                 path,
                 method,
                 body_as_dict,
                 expected_response_code,
                 create_model_from_doc,
                 async_state=None):
        AsyncAction.__init__(self, async_state)

        self.path = path
        self.method = method
        self.body_as_dict = body_as_dict
        self.expected_response_code = expected_response_code
        self.create_model_from_doc = create_model_from_doc

        self._callback = None

    def fetch(self, callback):
        """fetch() is perhaps not the best name but it matches
        the key method in the async HTTP client classs:-).
        """
        assert self._callback is None
        self._callback = callback

        url = "%s/%s" % (user_store, self.path)

        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "charset=utf8",
        }

        if self.body_as_dict is not None:
            if tampering_signer is not None:
                tamper.sign(tampering_signer, self.body_as_dict)
            body = json.dumps(self.body_as_dict)
            headers["Content-Type"] = "application/json; charset=utf8"
        else:
            body = None

        auth_mode = "basic" if username or password else None

        request = tornado.httpclient.HTTPRequest(
            url,
            method=self.method,
            body=body,
            headers=tornado.httputil.HTTPHeaders(headers),
            validate_cert=validate_cert,
            auth_mode=auth_mode,
            auth_username=username,
            auth_password=password)

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
            "User Store took %d ms to respond with %d to '%s' "
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
                "User Store responded to %s on %s "
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
                "User Store responded to %s on %s with error '%s'",
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
            if tampering_signer is not None:
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
            True,
            False,
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


class AsyncModelRetriever(AsyncAction):
    """Async'ly retrieve a model from the User Store."""

    def __init__(self, design_doc, key, async_state):
        AsyncAction.__init__(self, async_state)

        self.design_doc = design_doc
        self.key = key

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

        ausa = _AsyncUserStoreAction(
            path,
            "GET",
            None,           # body
            httplib.OK,
            self.create_model_from_doc)

        ausa.fetch(self._on_ausa_fetch_done)

    def _on_ausa_fetch_done(self, is_ok, is_conflict, models, _id, _rev, ausa):
        assert is_conflict is False
        model = models[0] if models else None
        self._call_callback(is_ok, model)

    def _call_callback(self, is_ok, model=None):
        assert self._callback
        self._callback(is_ok, model, self)
        self._callback = None

    def get_query_string_key_value_pairs(self):
        """This method is only called by ```fetch()``` to get the key value
        pairs that will be used to construct the query string in the request
        to the User Store.

        The presence of this method is a bit of a hack that was introduced
        when support for "most recent document" type queries was required.
        With this method here it allows derived classes to override the
        implementation and specialize the response for the new query types.
        """
        return {
            "include_docs": "true",
            "key": json.dumps(self.key),
        }

    def create_model_from_doc(self, doc):
        """Concrete classes derived from this class must implement
        this method which takes a dictionary (```doc```) and creates
        a model instance.
        """
        raise NotImplementedError()


class AsyncModelsRetriever(AsyncAction):
    """Async'ly retrieve a collection of models from the User Store."""

    def __init__(self,
                 design_doc,
                 async_state):
        AsyncAction.__init__(self, async_state)

        self.design_doc = design_doc

        self._callback = None

    def fetch(self, callback):
        assert self._callback is None
        self._callback = callback

        # :TRICKY: assumption here that design docs and views
        # are called the same thing ie one view per design doc
        path_fmt = '_design/%s/_view/%s?include_docs=true'
        ausa = _AsyncUserStoreAction(
            path_fmt % (self.design_doc, self.design_doc),
            "GET",
            None,           # body
            httplib.OK,
            self.create_model_from_doc)

        ausa.fetch(self._on_ausa_fetch_done)

    def create_model_from_doc(self, doc):
        raise NotImplementedError()

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

    def _on_ausa_fetch_done(self, is_ok, is_conflict, models, _id, _rev, ausa):
        assert is_conflict is False
        self._call_callback(is_ok, models)

    def _call_callback(self, is_ok, models=None):
        assert self._callback is not None
        self._callback(is_ok, self.transform_models(models), self)
        self._callback = None


class AsyncPersister(AsyncAction):
    """Async'ly persist a model object."""

    def __init__(self, model, model_as_dict_for_store_args, async_state):
        AsyncAction.__init__(self, async_state)

        self.model = model
        self.model_as_dict_for_store_args = model_as_dict_for_store_args

        # self._ausa is here only because it makes unit testing easier
        self._callback = None

    def persist(self, callback):
        assert not self._callback
        self._callback = callback

        model_as_dict_for_store = self.model.as_dict_for_store(*self.model_as_dict_for_store_args)
        if "_id" in model_as_dict_for_store:
            path = model_as_dict_for_store["_id"]
            method = "PUT"
        else:
            path = ""
            method = "POST"

        ausa = _AsyncUserStoreAction(
            path,
            method,
            model_as_dict_for_store,
            httplib.CREATED,
            None)           # create_model_from_doc
        ausa.fetch(self._on_ausa_fetch_done)

    def _on_ausa_fetch_done(self, is_ok, is_conflict, models, _id, _rev, ausa):
        """```self.model``` has just been written to the User Store which
        means ```self.model```'s _id and _rev properties might be out of
        sync with the _id and _rev properties in the User Store since the
        User Store will generate these values. The "if _id" and "if _rev"
        sections of code below unite the in-memory view and the in User
        Store view of this object/document.
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


class AsyncUserStoreHealthCheck(AsyncAction):
    """Async'ly confirm the User Service can reach the User Store."""

    def __init__(self, async_state=None):
        AsyncAction.__init__(self, async_state)

        self._callback = None

    def check(self, callback):
        assert not self._callback
        self._callback = callback

        ausa = _AsyncUserStoreAction(
            "",             # path
            "GET",
            None,           # body
            httplib.OK,
            None)           # create_model_from_doc
        ausa.fetch(self._on_ausa_fetch_done)

    def _on_ausa_fetch_done(self, is_ok, is_conflict, models, _id, _rev, ausa):
        assert is_conflict is False
        self._call_callback(is_ok)

    def _call_callback(self, is_ok):
        assert self._callback is not None
        self._callback(is_ok, self)
        self._callback = None
