"""This module implements a collection of unit tests for
the async_model_actions.py module.
"""

import httplib
import unittest
import uuid

import mock

from ..async_model_actions import AsyncAllViewMetricsRetriever
from ..async_model_actions import AsyncDeleter
from ..async_model_actions import AsyncModelRetriever
from ..async_model_actions import AsyncModelsRetriever
from ..async_model_actions import AsyncPersister
from ..async_model_actions import AsyncCouchDBHealthCheck
from ..async_model_actions import AsyncViewMetricsRetriever
from ..async_model_actions import BaseAsyncModelRetriever
from ..async_model_actions import CouchDBAsyncHTTPClient
from ..async_model_actions import DatabaseMetrics
from ..async_model_actions import InvalidTypeInDocForStoreException
from ..async_model_actions import ViewMetrics
from ..model import Model
from .. import async_model_actions  # noqa, needed for patching using relative path


class MyModel(Model):

    def as_doc_for_store(self, *args, **kwargs):
        rv = Model.as_doc_for_store(self, *args, **kwargs)
        rv["type"] = "mymodel_v1.0"
        return rv


class MyModelWithBadType(Model):

    def as_doc_for_store(self, *args, **kwargs):
        rv = Model.as_doc_for_store(self, *args, **kwargs)
        rv["type"] = "boo"
        return rv


class CouchDBAsyncHTTPClientPatcher(object):

    def __init__(self, is_ok, is_conflict, models, _id, _rev):

        def fetch_patch(cac, request, callback):
            callback(is_ok, is_conflict, models, _id, _rev, cac)

        self._patcher = mock.patch(
            __name__ + ".async_model_actions.CouchDBAsyncHTTPClient.fetch",
            fetch_patch)

    def __enter__(self):
        self._patcher.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._patcher.stop()


class CouchDBAsyncHTTPClientTestCase(unittest.TestCase):
    """A collection of unit tests for the CouchDBAsyncHTTPClient class."""

    def test_ctr(self):
        the_expected_response_code = uuid.uuid4().hex
        the_create_model_from_doc = uuid.uuid4().hex

        ac = CouchDBAsyncHTTPClient(
            the_expected_response_code,
            the_create_model_from_doc)

        self.assertEqual(
            ac.expected_response_code,
            the_expected_response_code)

        self.assertEqual(
            ac.create_model_from_doc,
            the_create_model_from_doc)

    @unittest.skip('assert_called_once_with() failing')
    def test_happy_path_with_no_time_info(self):
        response = mock.Mock()
        response.code = httplib.OK
        response.error = None
        response.body = None
        response.time_info = {}
        response.effective_url = "http://www.example.com/%s" % uuid.uuid4().hex
        response.request_time = 0.99
        response.request = mock.Mock()
        response.request.method = "GET"

        def fetch_patch(request, callback):
            callback(response)

        with mock.patch("tornado.httpclient.AsyncHTTPClient.fetch", side_effect=fetch_patch):
            the_ac = CouchDBAsyncHTTPClient(response.code, None)

            with mock.patch(__name__ + '.async_model_actions._logger') as logger_patch:
                callback = mock.Mock()
                the_ac.fetch(response.request, callback)
                callback.assert_called_once_with(True, False, [], None, None, the_ac)

                self.assertEqual(
                    logger_patch.error.call_args_list,
                    [])

                expected_info_message_fmt = (
                    "CouchDB took %.2f ms to respond with "
                    "%d to '%s' against >>>%s<<< - "
                    "timing detail: q=0.00 ms n=0.00 ms c=0.00 ms p=0.00 ms s=0.00 ms t=0.00 ms r=0.00 ms"
                )
                expected_info_message = expected_info_message_fmt % (
                    response.request_time * 1000,
                    response.code,
                    response.request.method,
                    response.effective_url)
                self.assertEqual(
                    logger_patch.info.call_args_list,
                    [mock.call(expected_info_message)])

    @unittest.skip('assert_called_once_with() failing')
    def test_happy_path_with_time_info(self):
        response = mock.Mock()
        response.code = httplib.OK
        response.error = None
        response.body = None
        response.time_info = {
            "queue": 1,
            "namelookup": 2,
            "connect": 3,
            "pretransfer": 4,
            "starttransfer": 5,
            "total": 6,
            "redirect": 7,
        }
        response.effective_url = "http://www.example.com/%s" % uuid.uuid4().hex
        response.request_time = 0.99
        response.request = mock.Mock()
        response.request.method = "GET"

        def fetch_patch(request, callback):
            callback(response)

        with mock.patch("tornado.httpclient.AsyncHTTPClient.fetch", side_effect=fetch_patch):
            the_ac = CouchDBAsyncHTTPClient(response.code, None)

            with mock.patch(__name__ + '.async_model_actions._logger') as logger_patch:
                callback = mock.Mock()
                the_ac.fetch(response.request, callback)
                callback.assert_called_once_with(True, False, [], None, None, the_ac)

                self.assertEqual(
                    logger_patch.error.call_args_list,
                    [])

                expected_info_message_fmt = (
                    "CouchDB took %.2f ms to respond with "
                    "%d to '%s' against >>>%s<<< - "
                    "timing detail: q=%.2f ms n=%.2f ms c=%.2f ms p=%.2f ms s=%.2f ms t=%.2f ms r=%.2f ms"
                )
                expected_info_message = expected_info_message_fmt % (
                    response.request_time * 1000,
                    response.code,
                    response.request.method,
                    response.effective_url,
                    response.time_info["queue"] * 1000,
                    response.time_info["namelookup"] * 1000,
                    response.time_info["connect"] * 1000,
                    response.time_info["pretransfer"] * 1000,
                    response.time_info["starttransfer"] * 1000,
                    response.time_info["total"] * 1000,
                    response.time_info["redirect"] * 1000)
                self.assertEqual(
                    logger_patch.info.call_args_list,
                    [mock.call(expected_info_message)])


class BaseAsyncModelRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the BaseAsyncModelRetriever class."""

    def test_implementation_for_get_query_string_key_value_pairs_required(self):
        """BaseAsyncModelRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of get_query_string_key_value_pairs() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(BaseAsyncModelRetriever):
            pass

        bad = Bad(None)
        with self.assertRaises(NotImplementedError):
            bad.get_query_string_key_value_pairs()

        class Good(Bad):
            def get_query_string_key_value_pairs(self):
                pass

        good = Good(None)
        good.get_query_string_key_value_pairs()

    def test_implementation_for_create_model_from_doc_required(self):
        """BaseAsyncModelRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of create_model_from_doc() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(BaseAsyncModelRetriever):
            pass

        bad = Bad(None)
        with self.assertRaises(NotImplementedError):
            bad.create_model_from_doc({})

        class Good(Bad):
            def create_model_from_doc(self, doc):
                pass

        good = Good(None)
        good.create_model_from_doc({})

    def test_implementation_for_on_cac_fetch_done_required(self):
        """BaseAsyncModelRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of on_cac_fetch_done() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(BaseAsyncModelRetriever):
            pass

        bad = Bad(None)
        with self.assertRaises(NotImplementedError):
            bad.on_cac_fetch_done(None, None, None, None, None, None)

        class Good(Bad):
            def on_cac_fetch_done(self, is_ok, is_conflict, models, _id, _rev, cac):
                pass

        good = Good(None)
        good.on_cac_fetch_done(None, None, None, None, None, None)


class AsyncModelRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncModelRetriever class."""

    def test_ctr_with_async_state(self):
        design_doc = uuid.uuid4().hex
        key = uuid.uuid4().hex
        async_state = uuid.uuid4().hex

        amr = AsyncModelRetriever(
            design_doc,
            key,
            async_state)

        self.assertTrue(amr.design_doc is design_doc)
        self.assertTrue(amr.key is key)
        self.assertTrue(amr.async_state is async_state)

    def test_error(self):
        the_is_ok = False
        the_is_conflict = False
        the_models = None
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            design_doc = uuid.uuid4().hex
            key = uuid.uuid4().hex
            async_state = uuid.uuid4().hex

            the_amr = AsyncModelRetriever(
                design_doc,
                key,
                async_state)

            def on_the_amr_fetch_done(is_ok, model, amr):
                self.assertEqual(is_ok, the_is_ok)
                self.assertTrue(model is None)
                self.assertTrue(amr is the_amr)

            the_amr.fetch(on_the_amr_fetch_done)

    def test_not_found(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = []
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            design_doc = uuid.uuid4().hex
            key = uuid.uuid4().hex
            async_state = uuid.uuid4().hex

            the_amr = AsyncModelRetriever(
                design_doc,
                key,
                async_state)

            def on_the_amr_fetch_done(is_ok, model, amr):
                self.assertEqual(is_ok, the_is_ok)
                self.assertTrue(model is None)
                self.assertTrue(amr is the_amr)

            the_amr.fetch(on_the_amr_fetch_done)

    def test_all_good(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = [Model()]
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            design_doc = uuid.uuid4().hex
            key = uuid.uuid4().hex
            async_state = uuid.uuid4().hex

            the_amr = AsyncModelRetriever(
                design_doc,
                key,
                async_state)

            def on_the_amr_fetch_done(is_ok, model, amr):
                self.assertEqual(is_ok, the_is_ok)
                self.assertTrue(model is the_models[0])
                self.assertTrue(amr is the_amr)

            the_amr.fetch(on_the_amr_fetch_done)


class AsyncModelsRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncModelsRetriever class."""

    def setUp(self):
        self.design_doc = uuid.uuid4().hex
        self.async_state = uuid.uuid4().hex
        self.start_key = uuid.uuid4().hex
        self.end_key = uuid.uuid4().hex
        self.amr = AsyncModelsRetriever(
            self.design_doc,
            self.start_key,
            self.end_key,
            self.async_state)

    def test_ctr(self):
        self.assertTrue(self.amr.design_doc is self.design_doc)
        self.assertTrue(self.amr.start_key is self.start_key)
        self.assertTrue(self.amr.end_key is self.end_key)
        self.assertTrue(self.amr.async_state is self.async_state)

    def test_error(self):
        the_is_ok = False
        the_is_conflict = False
        the_models = None
        the_id = None
        the_rev = None

        def on_the_amr_fetch_done(is_ok, models, amr):
            self.assertEqual(is_ok, the_is_ok)
            self.assertTrue(models is the_models)
            self.assertTrue(amr is self.amr)

        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            self.amr.fetch(on_the_amr_fetch_done)

    def test_all_good(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = [Model()]
        the_id = None
        the_rev = None

        def on_the_amr_fetch_done(is_ok, models, amr):
            self.assertEqual(is_ok, the_is_ok)
            self.assertTrue(models is the_models)
            self.assertTrue(amr is self.amr)

        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            self.amr.fetch(on_the_amr_fetch_done)

    def test_implementation_for_create_model_from_doc_required(self):
        """AsyncModelsRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of create_model_from_doc() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(AsyncModelsRetriever):
            pass

        bad = Bad(None, None, None, None)
        with self.assertRaises(NotImplementedError):
            bad.create_model_from_doc({})

        class Good(Bad):
            def create_model_from_doc(self, doc):
                pass

        good = Good(None, None, None, None)
        good.create_model_from_doc({})


class AsyncPersisterUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncPersister class."""

    def test_ctr(self):
        model = mock.Mock()
        model_as_doc_for_store_args = mock.Mock()
        async_state = mock.Mock()

        ap = AsyncPersister(model, model_as_doc_for_store_args, async_state)

        self.assertTrue(ap.model is model)
        self.assertTrue(ap.model_as_doc_for_store_args is model_as_doc_for_store_args)
        self.assertTrue(ap.async_state is async_state)

    def test_create_new(self):
        """Verify AsyncPersister.persist() when creating a new document."""

        the_model = MyModel(doc={})
        the_model_as_dict_args = []
        the_ap = AsyncPersister(the_model, the_model_as_dict_args, None)

        the_id = uuid.uuid4().hex
        the_rev = uuid.uuid4().hex

        self.assertIsNone(the_model._id)
        self.assertNotEqual(the_model._id, the_id)
        self.assertIsNone(the_model._rev)
        self.assertNotEqual(the_model._rev, the_rev)

        with CouchDBAsyncHTTPClientPatcher(True, False, [], the_id, the_rev):
            callback = mock.Mock()
            the_ap.persist(callback)
            callback.assert_called_once_with(True, False, the_ap)

            self.assertIsNotNone(the_model._id)
            self.assertEqual(the_model._id, the_id)

            self.assertIsNotNone(the_model._rev)
            self.assertEqual(the_model._rev, the_rev)

    def test_update_existing(self):
        """Verify AsyncPersister.persist() when updating a document
        that already exists.
        """

        the_model = MyModel(doc={
            "_id": uuid.uuid4().hex,
            "_rev": uuid.uuid4().hex,
        })

        the_model_as_dict_args = []
        the_ap = AsyncPersister(the_model, the_model_as_dict_args, None)

        the_next_rev = uuid.uuid4().hex
        self.assertIsNotNone(the_model._rev)
        self.assertNotEqual(the_model._rev, the_next_rev)

        with CouchDBAsyncHTTPClientPatcher(True, False, [], the_model._id, the_next_rev):
            callback = mock.Mock()
            the_ap.persist(callback)
            callback.assert_called_once_with(True, False, the_ap)
            self.assertEqual(the_model._rev, the_next_rev)

    def test_create_new_with_invalid_type_property(self):

        the_model = MyModelWithBadType(doc={})
        the_model_as_dict_args = []
        the_ap = AsyncPersister(the_model, the_model_as_dict_args, None)

        the_id = uuid.uuid4().hex
        the_rev = uuid.uuid4().hex

        with CouchDBAsyncHTTPClientPatcher(True, False, [], the_id, the_rev):
            callback = mock.Mock()
            with self.assertRaises(InvalidTypeInDocForStoreException):
                the_ap.persist(callback)


class AsyncDeleterUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncDeleter class."""

    def test_ctr(self):
        model = mock.Mock()
        async_state = mock.Mock()

        ad = AsyncDeleter(model, async_state)
        self.assertTrue(ad.model is model)
        self.assertTrue(ad.async_state is async_state)

        ad = AsyncDeleter(model)
        self.assertTrue(ad.model is model)
        self.assertIsNone(ad.async_state)

    def test_none_id_and_rev(self):
        model = mock.Mock()
        model._id = None
        model._rev = None

        ad = AsyncDeleter(model)

        callback = mock.Mock()
        ad.delete(callback)
        callback.assert_called_once_with(False, False, ad)

    def test_none_id(self):
        model = mock.Mock()
        model._id = None
        model._rev = uuid.uuid4().hex

        ad = AsyncDeleter(model)

        callback = mock.Mock()
        ad.delete(callback)
        callback.assert_called_once_with(False, False, ad)

    def test_none_rev(self):
        model = mock.Mock()
        model._id = uuid.uuid4().hex
        model._rev = None

        ad = AsyncDeleter(model)

        callback = mock.Mock()
        ad.delete(callback)
        callback.assert_called_once_with(False, False, ad)

    def test_conflict_detected(self):
        model = mock.Mock()
        model._id = uuid.uuid4().hex
        model._rev = uuid.uuid4().hex

        ad = AsyncDeleter(model)
        with CouchDBAsyncHTTPClientPatcher(False,   # is_ok
                                           True,    # is_conflict
                                           None,    # models
                                           None,    # _id
                                           None):   # _rev
            callback = mock.Mock()
            ad.delete(callback)
            callback.assert_called_once_with(False, True, ad)

    def test_error_on_delete(self):
        model = mock.Mock()
        model._id = uuid.uuid4().hex
        model._rev = uuid.uuid4().hex

        ad = AsyncDeleter(model)
        with CouchDBAsyncHTTPClientPatcher(False,   # is_ok
                                           False,   # is_conflict
                                           None,    # models
                                           None,    # _id
                                           None):   # _rev
            callback = mock.Mock()
            ad.delete(callback)
            callback.assert_called_once_with(False, False, ad)

    def test_happy_path(self):
        model = mock.Mock()
        model._id = uuid.uuid4().hex
        model._rev = uuid.uuid4().hex

        ad = AsyncDeleter(model)
        with CouchDBAsyncHTTPClientPatcher(True,    # is_ok
                                           False,   # is_conflict
                                           None,    # models
                                           None,    # _id
                                           None):   # _rev
            callback = mock.Mock()
            ad.delete(callback)
            callback.assert_called_once_with(True, False, ad)


class AsyncCouchDBHealthCheckCheckUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncCouchDBHealthCheck class."""

    def test_ctr_with_async_state(self):
        async_state = uuid.uuid4().hex

        aushc = AsyncCouchDBHealthCheck(async_state)

        self.assertTrue(aushc.async_state is async_state)

    def test_ctr_without_async_state(self):
        aushc = AsyncCouchDBHealthCheck()

        self.assertIsNone(aushc.async_state)

    def test_all_good(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = {}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            the_aushc = AsyncCouchDBHealthCheck()

            def callback(is_ok, aushc):
                self.assertTrue(is_ok)
                self.assertTrue(aushc is the_aushc)

            the_aushc.check(callback)

    def test_unreachable_couchdb(self):
        the_is_ok = False
        the_is_conflict = False
        the_models = {}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            the_aushc = AsyncCouchDBHealthCheck()

            def callback(is_ok, aushc):
                self.assertFalse(is_ok)
                self.assertTrue(aushc is the_aushc)

            the_aushc.check(callback)


class ViewMetricsUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the ViewMetrics class."""

    def test_ctr(self):
        the_design_doc = mock.Mock()
        the_data_size = mock.Mock()
        the_disk_size = mock.Mock()

        view_metrics = ViewMetrics(the_design_doc, the_data_size, the_disk_size)

        self.assertTrue(view_metrics.design_doc is the_design_doc)
        self.assertTrue(view_metrics.data_size is the_data_size)
        self.assertTrue(view_metrics.disk_size is the_disk_size)

    def test_fragmentation(self):
        self.assertIsNone(ViewMetrics(mock.Mock(), None, None).fragmentation)
        self.assertIsNone(ViewMetrics(mock.Mock(), 1, None).fragmentation)
        self.assertIsNone(ViewMetrics(mock.Mock(), None, 2).fragmentation)
        self.assertIsNotNone(ViewMetrics(mock.Mock(), 100, 100).fragmentation)
        self.assertEqual(0, ViewMetrics(mock.Mock(), 100, 100).fragmentation)
        self.assertEqual(50, ViewMetrics(mock.Mock(), 1000, 2000).fragmentation)


class DatabaseMetricsUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the DatabaseMetrics class."""

    def test_ctr(self):
        the_database = mock.Mock()
        the_doc_count = mock.Mock()
        the_data_size = mock.Mock()
        the_disk_size = mock.Mock()
        the_view_metrics = mock.Mock()

        database_metrics = DatabaseMetrics(
            the_database,
            the_doc_count,
            the_data_size,
            the_disk_size,
            the_view_metrics)

        self.assertTrue(database_metrics.database is the_database)
        self.assertTrue(database_metrics.doc_count is the_doc_count)
        self.assertTrue(database_metrics.data_size is the_data_size)
        self.assertTrue(database_metrics.disk_size is the_disk_size)
        self.assertTrue(database_metrics.view_metrics is the_view_metrics)

    def test_fragmentation(self):
        self.assertIsNone(DatabaseMetrics(mock.Mock(), 1, None, None, []).fragmentation)
        self.assertIsNone(DatabaseMetrics(mock.Mock(), 1, 1, None, []).fragmentation)
        self.assertIsNone(DatabaseMetrics(mock.Mock(), 1, None, 2, []).fragmentation)
        self.assertIsNotNone(DatabaseMetrics(mock.Mock(), 1, 100, 100, []).fragmentation)
        self.assertEqual(0, DatabaseMetrics(mock.Mock(), 1, 100, 100, []).fragmentation)
        self.assertEqual(50, DatabaseMetrics(mock.Mock(), 1, 1000, 2000, []).fragmentation)


class AsyncViewMetricsRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncViewMetricsRetriever class."""

    def test_ctr_with_async_state(self):
        the_design_doc = mock.Mock()
        the_async_state = mock.Mock()

        avmr = AsyncViewMetricsRetriever(the_design_doc, the_async_state)

        self.assertTrue(avmr.design_doc is the_design_doc)
        self.assertTrue(avmr.async_state is the_async_state)

    def test_ctr_without_async_state(self):
        the_design_doc = mock.Mock()

        avmr = AsyncViewMetricsRetriever(the_design_doc)

        self.assertTrue(avmr.design_doc is the_design_doc)
        self.assertIsNone(avmr.async_state)

    def test_fetch_error_talking_to_couchdb(self):
        the_is_ok = False
        the_is_conflict = False
        the_response_body = None
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            the_avmr = AsyncViewMetricsRetriever(mock.Mock())

            def callback(is_ok, view_metrics, avmr):
                self.assertFalse(is_ok)
                self.assertIsNone(view_metrics)
                self.assertEqual(type(avmr).FFD_ERROR_TALKING_TO_COUCHDB, avmr.fetch_failure_detail)
                self.assertTrue(avmr is the_avmr)

            the_avmr.fetch(callback)

    def test_fetch_invalid_response_body_no_view_index(self):
        the_is_ok = True
        the_is_conflict = False
        the_response_body = {}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            the_avmr = AsyncViewMetricsRetriever(mock.Mock())

            def callback(is_ok, view_metrics, avmr):
                self.assertTrue(is_ok)
                self.assertIsNotNone(view_metrics)
                self.assertIsNone(view_metrics.data_size)
                self.assertIsNone(view_metrics.disk_size)
                self.assertEqual(type(avmr).FFD_INVALID_RESPONSE_BODY, avmr.fetch_failure_detail)
                self.assertTrue(avmr is the_avmr)

            the_avmr.fetch(callback)

    def test_fetch_invalid_response_body_no_data_size(self):
        the_is_ok = True
        the_is_conflict = False
        the_disk_size = 42
        the_response_body = {'view_index': {'disk_size': the_disk_size}}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            the_avmr = AsyncViewMetricsRetriever(mock.Mock())

            def callback(is_ok, view_metrics, avmr):
                self.assertTrue(is_ok)
                self.assertIsNotNone(view_metrics)
                self.assertIsNone(view_metrics.data_size)
                self.assertEqual(view_metrics.disk_size, the_disk_size)
                self.assertEqual(type(avmr).FFD_INVALID_RESPONSE_BODY, avmr.fetch_failure_detail)
                self.assertTrue(avmr is the_avmr)

            the_avmr.fetch(callback)

    def test_fetch_invalid_response_body_no_disk_size(self):
        the_is_ok = True
        the_is_conflict = False
        the_data_size = 42
        the_response_body = {'view_index': {'data_size': the_data_size}}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            the_avmr = AsyncViewMetricsRetriever(mock.Mock())

            def callback(is_ok, view_metrics, avmr):
                self.assertTrue(is_ok)
                self.assertIsNotNone(view_metrics)
                self.assertEqual(view_metrics.data_size, the_data_size)
                self.assertIsNone(view_metrics.disk_size)
                self.assertEqual(type(avmr).FFD_INVALID_RESPONSE_BODY, avmr.fetch_failure_detail)
                self.assertTrue(avmr is the_avmr)

            the_avmr.fetch(callback)

    def test_happy_path(self):
        the_is_ok = True
        the_is_conflict = False
        the_data_size = 42
        the_disk_size = the_data_size + 1000
        the_response_body = {'view_index': {'data_size': the_data_size, 'disk_size': the_disk_size}}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            the_avmr = AsyncViewMetricsRetriever(mock.Mock())

            def callback(is_ok, view_metrics, avmr):
                self.assertTrue(is_ok)
                self.assertIsNotNone(view_metrics)
                self.assertEqual(view_metrics.data_size, the_data_size)
                self.assertEqual(view_metrics.disk_size, the_disk_size)
                self.assertEqual(type(avmr).FFD_OK, avmr.fetch_failure_detail)
                self.assertTrue(avmr is the_avmr)

            the_avmr.fetch(callback)


class AsyncAllViewMetricsRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncAllViewMetricsRetriever class."""

    def test_ctr_with_async_state(self):
        the_async_state = mock.Mock()

        aavmr = AsyncAllViewMetricsRetriever(the_async_state)

        self.assertTrue(aavmr.async_state is the_async_state)
        self.assertIsNone(aavmr.fetch_failure_detail)

    def test_ctr_with_no_async_state(self):
        aavmr = AsyncAllViewMetricsRetriever()

        self.assertIsNone(aavmr.async_state)
        self.assertIsNone(aavmr.fetch_failure_detail)

    def test_fetch_error_talking_to_couchdb(self):
        the_is_ok = False
        the_is_conflict = False
        the_response_body = None
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            callback = mock.Mock()

            aavmr = AsyncAllViewMetricsRetriever()
            aavmr.fetch(callback)

            callback.assert_called_once_with(False, None, aavmr)
            self.assertEqual(type(aavmr).FFD_ERROR_TALKING_TO_COUCHDB, aavmr.fetch_failure_detail)

    def test_fetch_database_has_no_design_docs_in_database(self):
        the_is_ok = True
        the_is_conflict = False
        the_response_body = {'rows': []}
        the_id = None
        the_rev = None
        with CouchDBAsyncHTTPClientPatcher(the_is_ok, the_is_conflict, the_response_body, the_id, the_rev):

            callback = mock.Mock()

            aavmr = AsyncAllViewMetricsRetriever()
            aavmr.fetch(callback)

            callback.assert_called_once_with(True, [], aavmr)
            self.assertEqual(type(aavmr).FFD_NO_DESIGN_DOCS_IN_DATABASE, aavmr.fetch_failure_detail)
