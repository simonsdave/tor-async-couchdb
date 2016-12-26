import httplib
import json
import random

import locust
import requests


_host = "http://127.0.0.1:8445"
_verify_cert = False
_timeout = 30.0
_number_fruits = 5
_weight_get = 50
_weight_put = 50

if not _verify_cert:
    requests.packages.urllib3.disable_warnings()


def _create_fruit():
    payload = {
    }
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    response = requests.post(
        "%s/v1.0/fruits" % _host,
        verify=_verify_cert,
        headers=headers,
        data=json.dumps(payload))
    assert response.status_code == httplib.CREATED

    return response.json()["fruit_id"]


_fruit_ids = [_create_fruit() for i in range(0, _number_fruits)]


class UserBehavior(locust.TaskSet):
    min_wait = 0
    max_wait = 0

    @locust.task(_weight_get)
    def get(self):
        fruit_id = random.choice(_fruit_ids)

        response = self.client.get(
            "/v1.0/fruits/%s" % fruit_id,
            verify=_verify_cert,
            timeout=_timeout)

        print "GET fruit\t%s\t%d" % (
            response.status_code,
            int(1000 * response.elapsed.total_seconds()))

    @locust.task(_weight_put)
    def put(self):
        fruit_id = random.choice(_fruit_ids)

        payload = {
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
        }
        response = self.client.put(
            "/v1.0/fruits/%s" % fruit_id,
            verify=_verify_cert,
            headers=headers,
            data=json.dumps(payload),
            timeout=_timeout)

        print "PUT fruit\t%s\t%d" % (
            response.status_code,
            int(1000 * response.elapsed.total_seconds()))


class User(locust.HttpLocust):
    min_wait = 0
    max_wait = 0
    weight = 100
    host = _host
    task_set = UserBehavior
