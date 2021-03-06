# tor-async-couchdb
![Maintained](https://img.shields.io/maintenance/no/2018.svg?style=flat)
![license](https://img.shields.io/pypi/l/tor-async-couchdb.svg?style=flat)
![PythonVersions](https://img.shields.io/pypi/pyversions/tor-async-couchdb.svg?style=flat)
![status](https://img.shields.io/pypi/status/tor-async-couchdb.svg?style=flat)
[![PyPI](https://img.shields.io/pypi/v/tor-async-couchdb.svg?style=flat)](https://pypi.python.org/pypi/tor-async-couchdb)

```
Repo Status = as of EO '18 this repo is no longer being maintained.
```

```tor-async-couchdb``` is an opinionated [Tornado](http://www.tornadoweb.org/en/stable/)
[async](http://tornado.readthedocs.org/en/latest/guide/async.html) client
for [CouchDB](http://couchdb.apache.org/).
```tor-async-couchdb``` is intended to operate as part of a service's application
tier and interact with the service's data tier implemented
using [CouchDB](http://couchdb.apache.org/).

```tor-async-couchdb``` documentation isn't as strong as it could be.
sample services are best way to gain an understanding of how to
use ```tor-async-couchdb```.

```tor-async-couchdb``` was originally created for use with
[CouchDB](http://couchdb.apache.org/). ```tor-async-couchdb```
has also been used with [Cloudant DBaaS](https://cloudant.com/product/)
and [Cloudant Local](https://cloudant.com/cloudant-local/).

```tor-async-couchdb``` was created as a way to capture a very opinionated set of best practices
and learnings after operating and scaling a number of services that used CouchDB
and Tornado. The opinions are summarized [here](docs/opinions.md).

# Using

Install ```tor-async-couchdb```.

```bash
>pip install tor_async_couchdb
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
