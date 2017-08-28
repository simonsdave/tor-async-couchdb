#!/usr/bin/env bash

#
# this script provisions a tor-async-couchdb development environment
#

set -e

#
# for python development
#
apt-get install -y python-virtualenv
apt-get install -y python-dev
apt-get build-dep -y python-crypto
apt-get install -y libcurl4-openssl-dev
apt-get install -y libffi-dev
apt-get build-dep -y python-pycurl

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

# docker 2.0
docker pull klaemo/couchdb:latest

# docker 1.6.1
docker pull couchdb:latest

exit 0
