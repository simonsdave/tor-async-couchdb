"""This file contains a series of integration tests that sanity check
a sample health service running on http://127.0.0.1:8445
"""

import httplib
import unittest

import requests

_base_url = 'http://127.0.0.1:8445/v1.0/_health'


class TheTestCase(unittest.TestCase):

    def _test_health_check_happy_path(self, quick):
        query_string = '' if quick is None else '?quick=%s' % quick
        url = '%s%s' % (_base_url, query_string)
        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        expected_response = {
          "status": "green",
          "links": {
            "self": {
              "href": url,
            }
          }
        }
        self.assertEqual(response.json(), expected_response)

    def test_default_ie_quick_health_check_happy_path(self):
        self._test_health_check_happy_path(None)

    def test_quick_health_check_happy_path(self):
        self._test_health_check_happy_path(True)

    def test_comprehensive_health_check_happy_path(self):
        self._test_health_check_happy_path(False)
