"""This file contains a series of integration tests that sanity check
a sample metrics service running on http://127.0.0.1:8445
"""

import httplib
import unittest

import requests

_base_url = 'http://127.0.0.1:8445/v1.0/_metrics'


class TheTestCase(unittest.TestCase):

    def _keys_from_dict(self, d):
        rv = {}
        for k, v in d.iteritems():
            rv[k] = self._keys_from_dict(v) if isinstance(v, dict) else ''
        return rv

    def test_metrics_happy_path(self):
        response = requests.get(_base_url)
        self.assertEqual(response.status_code, httplib.OK)
        expected_response = {
          "links": {
            "self": {
              "href": ''
            }
          },
          "database": {
            "docCount": '',
            "fragmentation": '',
            "dataSize": '',
            "diskSize": '',
            "views": {
              "fruit_by_fruit_id": {
                "fragmentation": '',
                "dataSize": '',
                "diskSize": ''
              },
              "fruit_by_color": {
                "fragmentation": '',
                "dataSize": '',
                "diskSize": ''
              }
            }
          }
        }
        self.assertEqual(self._keys_from_dict(response.json()), expected_response)
