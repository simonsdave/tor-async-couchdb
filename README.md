# tor-async-couchdb
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT) ![Python 2.7](https://img.shields.io/badge/python-2.7-FFC100.svg?style=flat) [![Requirements Status](https://requires.io/github/simonsdave/tor-async-couchdb/requirements.svg?branch=master)](https://requires.io/github/simonsdave/tor-async-couchdb/requirements/?branch=master) [![Build Status](https://travis-ci.org/simonsdave/tor-async-couchdb.svg)](https://travis-ci.org/simonsdave/tor-async-couchdb) [![Coverage Status](https://coveralls.io/repos/simonsdave/tor-async-couchdb/badge.svg)](https://coveralls.io/r/simonsdave/tor-async-couchdb) [![Code Health](https://landscape.io/github/simonsdave/tor-async-couchdb/master/landscape.svg?style=flat)](https://landscape.io/github/simonsdave/tor-async-couchdb/master)

tor-async-couchdb is a [Tornado](http://www.tornadoweb.org/en/stable/)
async client for [CouchDB](http://couchdb.apache.org/).
tor-async-couchdb is intended to operate as part of a service's application
tier (implemented using Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html))
and interact with the service's data tier (implemented using CouchDB).

>**Note** - ```tor-async-couchdb``` is poorly documented (@ the moment) - tests &
samples are best way to gain an understanding of the code and capabilities

```tor-async-couchdb``` is known to work with:

* Python 2.7.x
* Tornado 3.2.2 to 4.1
* CouchDB 1.6.1
* Mac OS X 10.9
* Ubuntu 12.04 and 14.04

```tor-async-couchdb``` has been used with although not extensively tested with:

* Cloudant's DBaaS offering as well as Cloudant Local

#Capabilities

When thinking about ```tor-async-couchdb``` capabilities it's
probably helpful to think about them in
[this architectural context](https://github.com/simonsdave/microservice-architecture).

##Functional Capabilities
* **Python object to CouchDB doc mapping** - easy mapping instances of
Python model classes (instances) to CouchDB documents
* **async [CRUD](http://en.wikipedia.org/wiki/Create,_read,_update_and_delete)** operations on model instances
* **async collections retrieval** - async retrieval of collections of model instances
* **async retrieval by any document property** - async'ly retrieve model instances
and collections of model instances by querying any CouchDB document property
* **CouchDB b-tree friendly document IDs**
* ```tor-async-couchdb```'s interface encourages users
of the package to deal with CouchDB's document conflict
errors using a simple retry pattern
* encourages an approach to **NoSQL data modeling** that enables
  * **automated reconciliation of document conflicts**
  * **satisfying data and information classification policies**
* :TODO: never delete/most recent style queries
* a collection of utility classes that make creating a
Python based **CouchDB database installer** possible in only a few lines of code
* async retrieval of database and view metrics

##Security Capabilities
* app tier optionally **authenticate to CouchDB using BASIC authentication**
* with well defined points of extensibility in Python object to
CouchDB document mapping enabling **per property encryption/hashing**
* **anti-tampering** which ensures CouchDB documents
can only be created and updated by a service's application tier

#Using

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
All model classes are derived from ```tor_async_couchdb.model.Model``` base class.
