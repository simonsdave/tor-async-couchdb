#!/usr/bin/env bash

#
# this script provisions a tor-async-couchdb development environment
#

set -e

#
# couchdb is run out of docker containers to
#
#   1/ simplify dev env provisioning
#   2/ permit easy switching between 1.6 and 2.0
#
# reference
#
#   https://github.com/apache/couchdb-docker
#

# couchdb 2.0
docker pull klaemo/couchdb:latest

# couchdb 1.6.1
docker pull couchdb:latest

exit 0
