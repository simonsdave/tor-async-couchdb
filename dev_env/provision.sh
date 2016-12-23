#!/usr/bin/env bash

#
# this script provisions a tor-async-couchdb development environment
#

set -e

apt-get update -y

apt-get install -y git

apt-get install -y python-virtualenv
apt-get install -y python-dev
apt-get build-dep -y python-crypto
apt-get install -y libcurl4-openssl-dev
apt-get install -y libffi-dev
apt-get build-dep -y python-pycurl
apt-get install -y unzip

timedatectl set-timezone EST

# install couchdb as per https://launchpad.net/~couchdb/+archive/ubuntu/stable
# there are some other instructions @ https://cwiki.apache.org/confluence/display/COUCHDB/Ubuntu
apt-get --no-install-recommends -y install build-essential pkg-config erlang libicu-dev libmozjs185-dev
apt-get install software-properties-common -y
add-apt-repository ppa:couchdb/stable -y
apt-get update -y
apt-get install -V -y couchdb
cp /vagrant/local.ini /etc/couchdb/local.ini
chown couchdb:couchdb /etc/couchdb/local.ini
service couchdb restart

curl -s -L --output /usr/local/bin/jq 'https://github.com/stedolan/jq/releases/download/jq-1.5/jq-linux64'
chown root.root /usr/local/bin/jq
chmod a+x /usr/local/bin/jq

cp /vagrant/.vimrc ~vagrant/.vimrc
chown vagrant:vagrant ~vagrant/.vimrc

echo 'export VISUAL=vim' >> ~vagrant/.profile
echo 'export EDITOR="$VISUAL"' >> ~vagrant/.profile

if [ $# == 2 ]; then
    su - vagrant -c "git config --global user.name \"${1:-}\""
    su - vagrant -c "git config --global user.email \"${2:-}\""
fi

exit 0
