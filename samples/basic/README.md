#```tor_async_couchdb``` Basic Sample
This service implements a simple RESTful service that
demonstrates how ```tor-async-couchdb``` was intended to be used.
This is the first in a series of samples services.
We'll build on this basic sample service as we explore the more
advanced features of ```tor-async-couchdb```.

The sample is a 2-tier application - an app tier talking to
a data tier using using HTTP.
The application tier is a service that exposes a RESTful API
which allows the creation, retrieval and update of fruit resources.
The application tier is implemented using using
Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html)
and ```tor-async-couchdb```.

#Creating the CouchDB Database

Create the database on CouchDB running on ```http://127.0.0.1:5984```
using the installer.
```bash
>./installer.py --delete=true --create=false --log=info --createdesign=false --createseed=false
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Deleting database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
ERROR:tor_async_couchdb.installer:No need to delete database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984' since database doesn't exist
(env)>./installer.py --create=true --log=info
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Creating database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Successfully created database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design documents in database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit_id' in database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/basic/design_docs/fruit_by_fruit_id.py'
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample_basic/_design/fruit_by_fruit_id'
```

#Running the Service
Service's command line options
```bash
>./service.py --help
Usage: service.py [options]

This service implements a simple RESTful service that demonstrates how tor-
async-couchdb was intended to be used.

Options:
  -h, --help   show this help message and exit
  --port=PORT  port - default = 8445
  --ip=IP      ip - default = 127.0.0.1
```

Service startup
```bash
>./service.py
2015-04-20T23:01:15.638+00:00 INFO service service started and listening on http://127.0.0.1:8445
```

#Exercising the Service's API
Create
```bash
>curl -s -X POST http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
```

Get individual
```bash
>curl -s http://127.0.0.1:8445/v1.0/fruits/996e11bfd4224feabe32e157e74c7343 | python -m json.tool
```

Get all
```bash
>curl -s http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
```

Update
```bash
curl -s -X PUT http://127.0.0.1:8445/v1.0/fruits/996e11bfd4224feabe32e157e74c7343 | python -m json.tool
```

# Service's Data Model
```bash
curl http://127.0.0.1:5984/tor_async_couchdb_basic_sample/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
```
