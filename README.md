# tor-async-couchdb
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT) ![Python 2.7](https://img.shields.io/badge/python-2.7-FFC100.svg?style=flat) [![Requirements Status](https://requires.io/github/simonsdave/tor-async-couchdb/requirements.svg?branch=master)](https://requires.io/github/simonsdave/tor-async-couchdb/requirements/?branch=master) [![Build Status](https://travis-ci.org/simonsdave/tor-async-couchdb.svg)](https://travis-ci.org/simonsdave/tor-async-couchdb) [![Coverage Status](https://coveralls.io/repos/simonsdave/tor-async-couchdb/badge.svg)](https://coveralls.io/r/simonsdave/tor-async-couchdb) [![Code Health](https://landscape.io/github/simonsdave/tor-async-couchdb/master/landscape.svg?style=flat)](https://landscape.io/github/simonsdave/tor-async-couchdb/master)

```tor-async-couchdb``` is a [Tornado](http://www.tornadoweb.org/en/stable/)
[async](http://tornado.readthedocs.org/en/latest/guide/async.html) client
for [CouchDB](http://couchdb.apache.org/).
```tor-async-couchdb``` is intended to operate as part of a service's application
tier and interact with the service's data tier implemented
using [CouchDB](http://couchdb.apache.org/).

```tor-async-couchdb``` documentation isn't as strong as it could be. This
README.md, samples and test are best way to gain an understanding of how to
use ```tor-async-couchdb```.

```tor-async-couchdb``` has been used with
the open source version of [CouchDB](http://couchdb.apache.org/),
[Cloudant DBaaS](https://cloudant.com/product/),
and [Cloudant Local](https://cloudant.com/cloudant-local/).

```tor-async-couchdb``` grew  ... experience operating and scaling CouchDB ... experience got expressed/enforced by ```tor-async-couchdb``` and a number of conventions including:

* data models:
  * every document should have a versioned type property
  * (standard NoSQL data model thinking) should assume documents are chunky and retrieval of a single document is often all that's necessary to implement a chunk of service functionality
  * are designed assuming conflicts will happen as part of regular operation
  * are designed with full knowledge that sensitive data at rest is an information security concern that needs to be taken seriously and therefore each property should be evaluated against a
data and information classification policy ([this](http://www.cmu.edu/iso/governance/guidelines/data-classification.html) and, if deemed senstive, the property should ideally
be hashed ([bcrypt]([py-bcrypt](https://pypi.python.org/pypi/py-bcrypt/) and if not
[SHA3-512](http://en.wikipedia.org/wiki/SHA-3)) and if it can't be hashed then
encrypt using [Keyczar](http://www.keyczar.org/)
* CouchDB, not the service tier, should generate document IDs
* document retrieval should be done through views against document properties not document IDs
* one design document per view
* services should embrace eventual consistency
* horizontally scaling CouchDB should be done using infrastructure (CouchDB 2.0 and Cloudant)
not application level sharding
* direct tampering of data in the database by DBAs is undesirable and therefore
tamper resistance is valued

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
