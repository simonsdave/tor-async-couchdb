#!/usr/bin/env python

import httplib
import json

import requests


_host = "http://127.0.0.1:8445"
_verify_cert = False
_number_fruit = 10

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


print 'export let fruit_ids = ['
for i in range(0, _number_fruit):
    print '  "%s"%s' % (_create_fruit(), ',' if i != (_number_fruit - 1) else '')
print '];'
