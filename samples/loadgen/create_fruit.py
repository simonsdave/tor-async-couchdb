#!/usr/bin/env python

import httplib
import json
import optparse
import random
import sys

import requests


def _create_fruit(service_base_url, color):
    payload = {
        'color': color,
    }
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
    }
    response = requests.post(
        '%s/v1.0/fruits' % service_base_url,
        headers=headers,
        data=json.dumps(payload))
    if response.status_code != httplib.CREATED:
        sys.exit(1)

    return response.json()['fruit_id']


class _CommandLineParser(optparse.OptionParser):

    def __init__(self):
        optparse.OptionParser.__init__(
            self,
            'usage: %prog [options]',
            description='Utility to create lots of fruit')

        default = 50
        help = 'number-fruit - default = %s' % default
        self.add_option(
            '--number-fruit',
            action='store',
            dest='number_fruit',
            default=default,
            type=int,
            help=help)

        default = 'http://127.0.0.1:8445'
        help = 'service - default = %s' % default
        self.add_option(
            '--service',
            action='store',
            dest='service_base_url',
            default=default,
            type='string',
            help=help)

    def parse_args(self, *args, **kwargs):
        (clo, cla) = optparse.OptionParser.parse_args(self, *args, **kwargs)
        if 0 != len(cla):
            self.error('try again ...')
        return (clo, cla)


if __name__ == '__main__':

    clp = _CommandLineParser()
    (clo, cla) = clp.parse_args()

    colors = ['red', 'orange', 'blue', 'brown', 'yellow', 'pink', 'white', 'black']

    print 'export let fruit_ids = ['
    for i in range(0, clo.number_fruit):
        fruit_id = _create_fruit(clo.service_base_url, random.choice(colors))
        print '  "%s"%s' % (fruit_id, ',' if i != (clo.number_fruit - 1) else '')
    print '];'

    sys.exit(0)
