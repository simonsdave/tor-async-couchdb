# tor-async-couchdb
[![MIT license](http://img.shields.io/badge/license-MIT-brightgreen.svg)](http://opensource.org/licenses/MIT) ![Python 2.7](https://img.shields.io/badge/python-2.7-FFC100.svg?style=flat) [![Requirements Status](https://requires.io/github/simonsdave/tor-async-couchdb/requirements.svg?branch=master)](https://requires.io/github/simonsdave/tor-async-couchdb/requirements/?branch=master) [![Build Status](https://travis-ci.org/simonsdave/tor-async-couchdb.svg)](https://travis-ci.org/simonsdave/tor-async-couchdb) [![Coverage Status](https://coveralls.io/repos/simonsdave/tor-async-couchdb/badge.svg)](https://coveralls.io/r/simonsdave/tor-async-couchdb) [![Code Health](https://landscape.io/github/simonsdave/tor-async-couchdb/master/landscape.svg?style=flat)](https://landscape.io/github/simonsdave/tor-async-couchdb/master)

```tor-async-couchdb``` is a [Tornado](http://www.tornadoweb.org/en/stable/)
[async](http://tornado.readthedocs.org/en/latest/guide/async.html) client
for [CouchDB](http://couchdb.apache.org/).
```tor-async-couchdb``` is intended to operate as part of a service's application
tier and interact with the service's data tier implemented
using [CouchDB](http://couchdb.apache.org/).

```tor-async-couchdb``` documentation isn't as strong as it could be. This
README.md, samples and tests are best way to gain an understanding of how to
use ```tor-async-couchdb```.

```tor-async-couchdb``` was originally created for use with
[CouchDB](http://couchdb.apache.org/). ```tor-async-couchdb```
has also been used with [Cloudant DBaaS](https://cloudant.com/product/)
and [Cloudant Local](https://cloudant.com/cloudant-local/).

```tor-async-couchdb``` was created as a way to capture the best practices
learned after operating and scaling a number of services that used CouchDB
and Tornado. The bullets below summarize these best practices.

* services should embrace eventual consistency
* thoughts on data models:
  * every document should have a versioned type property (ex *type=v9.99*)
  * documents are chunky; retrieval of a single document is often all
  that's necessary to implement a RESTful service's endpoint
  ala standard NoSQL data model thinking
  * assume conflicts happen as part of regular operation
  * sensitive data at rest is
  an information security concern;
  each property should be evaluated against a data and information
  classification policy; if a property is deemed sensitive it should, ideally,
  be hashed ([bcrypt]([py-bcrypt](https://pypi.python.org/pypi/py-bcrypt/) preferred
  and if not [SHA3-512](http://en.wikipedia.org/wiki/SHA-3));
  if a sensitive property can't be hashed it should be encrypted using
  [Keyczar](http://www.keyczar.org/) - [this](http://www.cmu.edu/iso/governance/guidelines/data-classification.html)
  is a good example of data classification
* CouchDB, not the service tier, should generate document IDs
* document retrieval should be done through views against document properties not document IDs
* one design document per view
* horizontally scaling CouchDB should be done using infrastructure (CouchDB 2.0 and Cloudant)
not application level sharding
* direct tampering of data in the database by DBAs is undesirable and therefore
tamper resistance is valued

# Using

Add the following to your project's ```setup.py```:

```python
from setuptools import setup
setup(
    install_requires=[
        "tor-async-couchdb==0.30.0",
    ],
    dependency_links=[
        "https://github.com/simonsdave/tor-async-couchdb/tarball/v0.30.0#egg=tor-async-couchdb-0.30.0",
    ],
```

Configure ```tor-async-couchdb``` in your service's mainline.
Typically the configuration options are expected to come
from a configuration file and/or the service's command line.

```python
from tor_async_couchdb import async_model_actions

async_model_actions.database = "http://127.0.0.1:5984/database"
async_model_actions.tampering_signer = None
async_model_actions.username = None
async_model_actions.password = None
async_model_actions.validate_cert = True
```
