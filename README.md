# tor-async-couchdb [![Build Status](https://travis-ci.org/simonsdave/tor-async-couchdb.svg)](https://travis-ci.org/simonsdave/tor-async-couchdb) [![Coverage Status](https://coveralls.io/repos/simonsdave/tor-async-couchdb/badge.svg)](https://coveralls.io/r/simonsdave/tor-async-couchdb) [![Requirements Status](https://requires.io/github/simonsdave/tor-async-couchdb/requirements.svg?branch=master)](https://requires.io/github/simonsdave/tor-async-couchdb/requirements/?branch=master)

tor-async-couchdb is a [Tornado](http://www.tornadoweb.org/en/stable/)
async client for [CouchDB](http://couchdb.apache.org/).
tor-async-couchdb is intended to operate as part of a service's application
tier (implemented using Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html))
and interact with the service's data tier (implemented using CouchDB).

Note - ```tor-async-couchdb``` is poorly documented (@ the moment) - tests &
samples are best way to gain an understanding of the code and capabilities

Key features:

* defines a pattern for mapping instances of Python
model classes to CouchDB documents with well defined
points of extensibility at which model properties can
be encrypted/hashed before being written to CouchDB and
decrypted after being read from CouchDB
* async persisting of model instances
* async retrieval of individual and collections of
model instances with well defined responsibilities
between the async client and CouchDB views
* enables querying of document by a CouchDB view using
any document property and documents are always retrieved
via a view
* anti-tampering capability that ensures CouchDB documents
can only be created and update by a service's application
tier
* a collection of utility classes that make creating a
Python based CouchDB installer possible in only a few lines
of code; the utility classes require that design documents
and seed documents are declared in a manner that makes
authoring ```setup.py```'s a snap
* an approach to document IDs which encourages users
of ```tor-async-couchdb``` to allow CouchDB to generate
document identifiers to avoid btree fragmentation
* ```tor-async-couchdb```'s interface encourages users
of the package to deal with CouchDB's document conflict
errors using a retry pattern
* encourages a particular approach to NoSQL data model that permits
automated reconciliation of document conflicts and enables true
multi-master replication scenarios and a path to satisfying
data and information classification policies
* ```tor-async-couchdb``` has been used for a while in
a distributed with reasonably high concurrency levels and
a generally high level of paranoia
* :TODO: add use of ```include_docs``` to reduce view disk
space consumption
* :TODO: never delete/most recent sytle queries

```tor-async-couchdb``` is known to work with:

* Python 2.7.x
* Tornado 3.2.2 to 4.1
* CouchDB 1.6.1
* Mac OS X 10.9
* Ubuntu 12.04 and 14.04

```tor-async-couchdb``` has been used with but less extensively tested with:

* Cloudant's DBaaS offering as well as Cloudant Local

##Using

Add the following line to your requirements.txt
```
git+git://github.com/simonsdave/tor-async-couchdb.git@master
```

If you have a setup.py make these changes:
```python
from setuptools import setup
setup(
    install_requires=[
        "tor-async-couchdb==1.0.0",
    ],
    dependency_links=[
        "http://github.com/simonsdave/tor-async-couchdb/tarball/master#egg=tor-async-couchdb-1.0.0",
    ],
```

Configure tor-async-couchdb in your service's mainline.
Typically we'd expect the configuration options come come
from a configuration file and/or the service's command line.
```python
from tor_async_couchdb import async_model_actions

async_model_actions.user_store = "http://127.0.0.1:5984/database"
async_model_actions.tampering_signer = None # keyczar signer
async_model_actions.username = None
async_model_actions.password = None
async_model_actions.validate_cert = False
```

Instances of a model class are saved in CouchDB as a document with
a ```type``` property set to a value like ```boo_v1.0```.
All model classes are derived from a common abstract base class
```tor_async_couchdb.model.Model```.
