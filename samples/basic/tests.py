"""This file contains a series of integration tests that sanity check
a sample service running on http://127.0.0.1:8445
"""

import httplib
import json
from sets import Set
import unittest

import requests

_base_url = "http://127.0.0.1:8445"

class TheTestCase(unittest.TestCase):

    def _get_all(self):
        url = "%s/v1.0/fruits" % _base_url
        response = requests.get(url)
        self.assertEqual(response.status_code, httplib.OK)
        return response.json()

    def setUp(self):
        fruits = self._get_all()
        for fruit in fruits:
            fruit_id = fruit.get("fruit_id", None)
            self.assertIsNotNone(fruit_id)
            url = "%s/v1.0/fruits/%s" % (_base_url, fruit_id)
            response = requests.delete(url)
            self.assertEqual(response.status_code, httplib.OK)

        fruits = self._get_all()
        self.assertEqual(0, len(fruits))

    def test_not_found_on_get_to_base_url(self):
        response = requests.get(_base_url)
        self.assertEqual(response.status_code, httplib.NOT_FOUND)

    def test_get_all(self):
        self.assertEqual(0, len(self._get_all()))

        number_fruits = 5
        the_fruit_ids = Set()
        for i in range(0, number_fruits):
            payload = {
            }
            headers = {
                "Content-Type": "application/json; charset=utf-8",
            }
            create_response = requests.post(
                "%s/v1.0/fruits" % _base_url,
                headers=headers,
                data=json.dumps(payload))
            self.assertEqual(create_response.status_code, httplib.CREATED)
            fruit_id = create_response.json().get("fruit_id", None)
            self.assertIsNotNone(fruit_id)
            the_fruit_ids.add(fruit_id)

        self.assertEqual(
            number_fruits,
            len(the_fruit_ids))

        self.assertEqual(
            Set([fruit["fruit_id"] for fruit in self._get_all()]),
            the_fruit_ids)

    def test_crud(self):
        #
        # Create
        #
        payload = {
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        create_response = requests.post(
            "%s/v1.0/fruits" % _base_url,
            headers=headers,
            data=json.dumps(payload))
        self.assertEqual(create_response.status_code, httplib.CREATED)
        fruit_id = create_response.json().get("fruit_id", None)
        self.assertIsNotNone(fruit_id)

        #
        # Read
        #
        url = "%s/v1.0/fruits/%s" % (_base_url, fruit_id)
        read_response = requests.get(url)
        self.assertEqual(read_response.status_code, httplib.OK)
        self.assertEqual(
            read_response.json(),
            create_response.json())

        #
        # Update
        #
        payload = {
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        update_response = requests.put(
            "%s/v1.0/fruits/%s" % (_base_url, fruit_id),
            headers=headers,
            data=json.dumps(payload))
        self.assertEqual(read_response.status_code, httplib.OK)

        #
        # Delete
        #
        url = "%s/v1.0/fruits/%s" % (_base_url, fruit_id)
        delete_response = requests.delete(url)
        self.assertEqual(read_response.status_code, httplib.OK)
