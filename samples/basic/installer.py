#!/usr/bin/env python
"""This module contains all the logic required to create and delete
a CouchDB database for tor_async_councdb's basic sample.
"""

import sys

from tor_async_couchdb import installer
import design_docs


class CommandLineParser(installer.CommandLineParser):

    def __init__(self):
        description = (
            "This utility used to create and/or delete the CouchDB "
            "database for tor_async_couchdb's basic sample."
        )
        installer.CommandLineParser.__init__(
            self,
            description,
            "tor_async_couchdb_sample_basic")

if __name__ == "__main__":
    sys.exit(installer.main(CommandLineParser(), design_docs))
