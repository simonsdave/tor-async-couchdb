"""This module contains the tamper module's unit tests."""

import os
import shutil
import sys
import tempfile
import unittest

from keyczar import keyczar
from keyczar import keyczart
import mock

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import tamper


class TempDirectory(object):

    def __init__(self):
        object.__init__(self)
        self._dir_name = None

    def __enter__(self):
        self._dir_name = tempfile.mkdtemp()
        return self._dir_name

    def __exit__(self, exc_type, exc_value, traceback):
        if self._dir_name:
            shutil.rmtree(self._dir_name, ignore_errors=True)


class TamperTestCase(unittest.TestCase):
    """A collection of unit tests for the tamper module."""

    def test_happy_path(self):

        with TempDirectory() as dir_name:
            keyczart.Create(
                dir_name,
                "some purpose",
                keyczart.keyinfo.SIGN_AND_VERIFY)

            keyczart.AddKey(
                dir_name,
                keyczart.keyinfo.PRIMARY)

            signer = keyczar.Signer.Read(dir_name)

            doc = {
                "dave": "was",
                "here": "today",
            }
            pre_sign_doc_len = len(doc)
            tamper.sign(signer, doc)
            self.assertEqual(len(doc), 1 + pre_sign_doc_len)
            self.assertTrue(tamper.verify(signer, doc))

    def test_verify_fails_when_doc_tampered_with(self):

        with TempDirectory() as dir_name:
            keyczart.Create(
                dir_name,
                "some purpose",
                keyczart.keyinfo.SIGN_AND_VERIFY)

            keyczart.AddKey(
                dir_name,
                keyczart.keyinfo.PRIMARY)

            signer = keyczar.Signer.Read(dir_name)

            doc = {
                "dave": "was",
                "here": "today",
            }
            pre_sign_doc_len = len(doc)
            tamper.sign(signer, doc)
            self.assertEqual(len(doc), 1 + pre_sign_doc_len)

            doc["bindle"] = "berry"

            self.assertFalse(tamper.verify(signer, doc))

    def test_verify_fails_when_sig_removed(self):

        with TempDirectory() as dir_name:
            keyczart.Create(
                dir_name,
                "some purpose",
                keyczart.keyinfo.SIGN_AND_VERIFY)

            keyczart.AddKey(
                dir_name,
                keyczart.keyinfo.PRIMARY)

            signer = keyczar.Signer.Read(dir_name)

            doc = {
                "dave": "was",
                "here": "today",
            }
            pre_sign_doc_len = len(doc)
            tamper.sign(signer, doc)
            self.assertEqual(len(doc), 1 + pre_sign_doc_len)

            del doc[tamper._tampering_sig_prop_name]
            self.assertEqual(len(doc), pre_sign_doc_len)

            self.assertFalse(tamper.verify(signer, doc))
