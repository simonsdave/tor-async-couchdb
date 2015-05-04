#!/usr/bin/env python
"""This module contains all the logic required to create and delete
a CouchDB database for tor_async_councdb's basic sample.
"""

import os.path
import sys

from tor_async_couchdb import installer


class CommandLineParser(installer.CommandLineParser):

    def __init__(self):
        description = (
            "This utility used to create and/or delete the CouchDB "
            "database for tor_async_couchdb's basic sample."
        )
        installer.CommandLineParser.__init__(
            self,
            description,
            "tor_async_couchdb_sample")

if __name__ == "__main__":
    design_docs = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'design_docs')
    seed_docs = os.path.join(os.path.abspath(
        os.path.dirname(__file__)), 'seed_docs')
    sys.exit(installer.main(CommandLineParser(), design_docs, seed_docs))
