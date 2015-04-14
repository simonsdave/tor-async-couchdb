#
# to build the distrubution @ tor_async_couchdb-0.9.0.tar.gz
#
#   >git clone https://github.com/simonsdave/tor-async-couchdb.git
#   >cd tor-async-couchdb
#   >source cfg4dev
#   >python setup.py sdist --formats=gztar
#
from setuptools import setup

setup(
    name="tor_async_couchdb",
    packages=[
        "tor_async_couchdb",
    ],
    install_requires=[
        "python-keyczar==0.715",
    ],
    version="0.9.0",
    description="Tornado Async Client for CouchDB",
    author="Dave Simons",
    author_email="simonsdave@gmail.com",
    url="https://github.com/simonsdave/tor-async-couchdb"
)
