"""This module implements a unit tests for the model module."""

import os
import re
import sys
import unittest
import uuid

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from model import Model


class ModelTaseCase(unittest.TestCase):
    """A collection of unit tests for the Model class."""

    def test_ctr_no_args(self):
        model = Model()
        self.assertIsNone(model._id)
        self.assertIsNone(model._rev)

    def test_ctr_empty_doc(self):
        model = Model(doc={})
        self.assertIsNone(model._id)
        self.assertIsNone(model._rev)

    def test_ctr_with_doc(self):
        doc = {
            "_id": uuid.uuid4().hex,
            "_rev": uuid.uuid4().hex,
        }
        model = Model(doc=doc)
        self.assertEqual(model._id, doc["_id"])
        self.assertEqual(model._rev, doc["_rev"])

    def test_as_dict_for_store_not_initalized(self):
        doc = {}
        model = Model(doc=doc)
        doc_from_as_dict_for_store = model.as_dict_for_store()
        self.assertEqual(0, len(doc_from_as_dict_for_store))

    def test_as_dict_for_store_initalized(self):
        doc = {
            "_id": uuid.uuid4().hex,
            "_rev": uuid.uuid4().hex,
        }
        model = Model(doc=doc)
        doc_from_as_dict_for_store = model.as_dict_for_store()
        self.assertEqual(doc["_id"], doc_from_as_dict_for_store["_id"])
        self.assertEqual(doc["_rev"], doc_from_as_dict_for_store["_rev"])
