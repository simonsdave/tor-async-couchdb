# tor-async-couchdb [![Build Status](https://travis-ci.org/simonsdave/tor-async-couchdb.svg)](https://travis-ci.org/simonsdave/tor-async-couchdb) [![Coverage Status](https://coveralls.io/repos/simonsdave/tor-async-couchdb/badge.svg)](https://coveralls.io/r/simonsdave/tor-async-couchdb) [![Requirements Status](https://requires.io/github/simonsdave/tor-async-couchdb/requirements.svg?branch=master)](https://requires.io/github/simonsdave/tor-async-couchdb/requirements/?branch=master)

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

##Functional Capabilities
* **Python object to CouchDB doc mapping** - easily mapping instances of
Python model classes (objects) to CouchDB documents
* **async persist** of model instances
* **async doc retrieval** of individual docs and of collections of docs
* **doc query by any document property** using disk space optimized
CouchDB views
* **CouchDB b-tree friendly document IDs**
* ```tor-async-couchdb```'s interface encourages users
of the package to deal with CouchDB's document conflict
errors using a retry pattern
* encourages an approach to **NoSQL data modeling** that enables
  * **automated reconciliation of document conflicts** thus enabling true
    multi-master replication which in turn permit deployments with
    multiple, simultaneously active data centers
  * **satisfying data and information classification policies**
* :TODO: never delete/most recent style queries

* a collection of utility classes that make creating a
Python based **CouchDB database installer** possible in only a few lines
of code; the utility classes require that design documents
and seed documents are declared in a manner that makes
authoring ```setup.py```'s a snap

##Security Capabilities
* app tier optionally **authenticate to CouchDB using BASIC authentication**
* with well defined points of extensibility in Python object to
CouchDB doc mapping which enables **per property encryption/hashing**
* **anti-tampering** which ensures CouchDB documents
can only be created and updated by a service's application tier

#Architectural Context
In order to understand the value that ```tor-async-couchdb``` enables
it's helpful to consider the architectural context within which
```tor-async-couchdb``` was intended to be deployed.
Below is the outline of that context:

* service infrastructure is deployed into IaaS providers (AWS, GCE, etc) - the important point here is that we have access to elastic computing (we can spin up new servers in minutes) - multiple providers is nice from an availability point of view but also ensures that if for some super odd reason an individual provider runs out of server capacity we can use other providers - worth noting that the service infrastructure simultaneously operates in multiple deployments (data centers) at multiple IaaS providers with DNS being used to route requests to the network wise closet deployment
* each tier (app tiers and data tier) of the service infrastructure scales horizontally - the important point with this is that we can spin up new servers (see above), deploy app or data services to the new servers and those new services immediately increase the capacity of a tier)
* app tier horizontal scale is well understood these days and is typically
accomplished using an entirely stateless app tier
* optimization of app tier server resources is accomplished by using
Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html)
as an elegant solution to the [C10K problem](http://en.wikipedia.org/wiki/C10k_problem)
* how does the data tier scale horizontally (& across data centers)? answer = leverage NoSQL databases
which are designed to scale horizontally and support multi-master replication;
CouchDB is the database or choice in the data tier because of its exceptionally strong
replication capabilities and that enables the simultaneous multiple data center
deployment previously described; CouchDB 2.0 and IBM's commercial offering of
CouchDB called Cloudant enables both horizontal scaling of the data tier
* when load balancing and proxying are required, tried and tested haproxy
and nginx are the preferred tools

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
All model classes are derived from a common abstract base class
```tor_async_couchdb.model.Model```.
