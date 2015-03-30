"""This module implements a collection of unit tests for
the async_model_actions.py module."""

import httplib
import os
import mock
import sys
import unittest
import uuid

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from async_model_actions import AsyncModelRetriever
from async_model_actions import AsyncModelsRetriever
from async_model_actions import AsyncUserStoreHealthCheck
from async_model_actions import AsyncPersister
from model import Model


class Patcher(object):

    def __init__(self, patcher):
        object.__init__(self)
        self._patcher = patcher

    def __enter__(self):
        self._patcher.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._patcher.stop()


class AsyncUserStoreActionPatcher(Patcher):

    def __init__(self, is_ok, is_conflict, models, _id, _rev):

        def fetch_patch(ausa, callback):
            callback(is_ok, is_conflict, models, _id, _rev, ausa)

        patcher = mock.patch(
            "async_model_actions._AsyncUserStoreAction.fetch",
            fetch_patch)

        Patcher.__init__(self, patcher)


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
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
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
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
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
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
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

    def test_implementation_for_create_model_from_doc_required(self):
        """AsyncModelRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of create_model_from_doc() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(AsyncModelRetriever):
            pass

        bad = Bad(None, None, None)
        with self.assertRaises(NotImplementedError):
            bad.create_model_from_doc({})

        class Good(Bad):
            def create_model_from_doc(self, doc):         
                pass

        good = Good(None, None, None)
        good.create_model_from_doc({})


class AsyncModelsRetrieverUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncModelsRetriever class."""

    def test_ctr(self):
        design_doc = uuid.uuid4().hex
        async_state = uuid.uuid4().hex

        amr = AsyncModelsRetriever(
            design_doc,
            async_state)

        self.assertTrue(amr.design_doc is design_doc)
        self.assertTrue(amr.async_state is async_state)

    def test_error(self):
        the_is_ok = False
        the_is_conflict = False
        the_models = None
        the_id = None
        the_rev = None
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            design_doc = uuid.uuid4().hex
            async_state = uuid.uuid4().hex

            the_amr = AsyncModelsRetriever(
                design_doc,
                async_state)

            def on_the_amr_fetch_done(is_ok, models, amr):
                self.assertEqual(is_ok, the_is_ok)
                self.assertTrue(models is the_models)
                self.assertTrue(amr is the_amr)

            the_amr.fetch(on_the_amr_fetch_done)

    def test_all_good(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = [Model()]
        the_id = None
        the_rev = None
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            design_doc = uuid.uuid4().hex
            async_state = uuid.uuid4().hex

            the_amr = AsyncModelsRetriever(
                design_doc,
                async_state)

            def on_the_amr_fetch_done(is_ok, models, amr):
                self.assertEqual(is_ok, the_is_ok)
                self.assertTrue(models is the_models)
                self.assertTrue(amr is the_amr)

            the_amr.fetch(on_the_amr_fetch_done)

    def test_implementation_for_create_model_from_doc_required(self):
        """AsyncModelsRetriever is an abstract base class.
        Concrete derived classes must provide an implementation
        of create_model_from_doc() otherwise an exception is
        raised. This test verifies the exception is raised
        when an implementation is not provided."""

        class Bad(AsyncModelsRetriever):
            pass

        bad = Bad(None, None)
        with self.assertRaises(NotImplementedError):
            bad.create_model_from_doc({})

        class Good(Bad):
            def create_model_from_doc(self, doc):         
                pass

        good = Good(None, None)
        good.create_model_from_doc({})


class AsyncPersisterUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncPersister class."""

    def test_ctr(self):
        model = mock.Mock()
        model_as_dict_for_store_args = mock.Mock()
        async_state = mock.Mock()

        ap = AsyncPersister(model, model_as_dict_for_store_args, async_state)

        self.assertTrue(ap.model is model)
        self.assertTrue(ap.model_as_dict_for_store_args is model_as_dict_for_store_args)
        self.assertTrue(ap.async_state is async_state)

    def test_create_new(self):
        """Verify AsyncPersister.persist() when creating a new document
        in the User Store.
        """

        the_model = Model()
        the_model_as_dict_args = []
        the_ap = AsyncPersister(the_model, the_model_as_dict_args, None)

        the_id = uuid.uuid4().hex
        the_rev = uuid.uuid4().hex

        self.assertIsNone(the_model._id)
        self.assertNotEqual(the_model._id, the_id)
        self.assertIsNone(the_model._rev)
        self.assertNotEqual(the_model._rev, the_rev)

        def callback(is_ok, is_conflict, ap):
            self.assertTrue(is_ok)
            self.assertIsNotNone(the_model._id)
            self.assertEqual(the_model._id, the_id)
            self.assertIsNotNone(the_model._rev)
            self.assertEqual(the_model._rev, the_rev)
            self.assertFalse(is_conflict)
            self.assertTrue(ap is the_ap)

        with AsyncUserStoreActionPatcher(True, False, [], the_id, the_rev):
            the_ap.persist(callback)

    def test_update_existing(self):
        """Verify AsyncPersister.persist() when updating a document
        that already exists in the User Store.
        """

        the_model = Model(doc={"_id": uuid.uuid4().hex, "_rev": uuid.uuid4().hex})
        the_model_as_dict_args = []
        the_ap = AsyncPersister(the_model, the_model_as_dict_args, None)

        the_next_rev = uuid.uuid4().hex
        self.assertIsNotNone(the_model._rev)
        self.assertNotEqual(the_model._rev, the_next_rev)

        def callback(is_ok, is_conflict, ap):
            self.assertTrue(is_ok)
            self.assertIsNotNone(the_model._rev)
            self.assertEqual(the_model._rev, the_next_rev)
            self.assertFalse(is_conflict)
            self.assertTrue(ap, the_ap)

        with AsyncUserStoreActionPatcher(True, False, [], the_model._id, the_next_rev):
            the_ap.persist(callback)


class AsyncUserStoreHealthCheckCheckUnitTaseCase(unittest.TestCase):
    """A collection of unit tests for the AsyncUserStoreHealthCheck class."""

    def test_ctr_with_async_state(self):
        async_state = uuid.uuid4().hex

        aushc = AsyncUserStoreHealthCheck(async_state)

        self.assertTrue(aushc.async_state is async_state)

    def test_ctr_without_async_state(self):
        aushc = AsyncUserStoreHealthCheck()

        self.assertIsNone(aushc.async_state)

    def test_all_good(self):
        the_is_ok = True
        the_is_conflict = False
        the_models = []
        the_id = None
        the_rev = None
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            the_aushc = AsyncUserStoreHealthCheck()

            def callback(is_ok, aushc):
                self.assertTrue(is_ok)
                self.assertTrue(aushc is the_aushc)

            the_aushc.check(callback)

    def test_unreachable_user_store(self):
        the_is_ok = False
        the_is_conflict = False
        the_models = []
        the_id = None
        the_rev = None
        with AsyncUserStoreActionPatcher(the_is_ok, the_is_conflict, the_models, the_id, the_rev):
            the_aushc = AsyncUserStoreHealthCheck()

            def callback(is_ok, aushc):
                self.assertFalse(is_ok)
                self.assertTrue(aushc is the_aushc)

            the_aushc.check(callback)
