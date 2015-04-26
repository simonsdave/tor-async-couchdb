#```tor_async_couchdb``` Basic Sample
This service implements a simple RESTful service that
demonstrates how the basic features of ```tor-async-couchdb``` were intended to be used.
This is the first in a series of samples services.
We'll build on this basic sample service as we explore the more
advanced features of ```tor-async-couchdb```.

This sample is a 2-tier application - an app tier talking to a data tier.
The app tier is a service that exposes a RESTful API
which allows the creation, retrieval and update of fruit resources.
The application tier is implemented using using
Tornado's [Asynchronous and non-Blocking I/O](http://tornado.readthedocs.org/en/latest/guide/async.html)
and ```tor-async-couchdb```.
The data tier is implemented using CouchDB.

#Creating the CouchDB Database

Create the database on CouchDB running on ```http://127.0.0.1:5984```
using the installer.
```bash
>./installer.py --create=true --log=info
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

##Command line options
```bash
>./service.py --help
Usage: service.py [options]

This service implements a simple RESTful service that demonstrates how tor-
async-couchdb was intended to be used.

Options:
  -h, --help           show this help message and exit
  --port=PORT          port - default = 8445
  --ip=IP              ip - default = 127.0.0.1
  --database=DATABASE  database - default =
                       http://127.0.0.1:5984/tor_async_couchdb_sample_basic
```

##Startup
```bash
>./service.py
2015-04-22T11:56:57.724+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample_basic
```

#Exercising the Service's API

##Create
```bash
>curl -s -X POST http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "1-9e08c14213bb8b4386eea863de966d9e",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "fig",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

##Read
```bash
>curl -s http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "1-9e08c14213bb8b4386eea863de966d9e",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "fig",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

##Update
```bash
>curl -s -X PUT http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "2-233923144d85b62e26c13013e9d30eeb",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "kiwi",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>curl -s -X PUT http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179 | python -m json.tool
{
    "_id": "345d17dae686f2b435881085198afc39",
    "_rev": "3-fe7b3d270fa598b88d646687488aa766",
    "created_on": "2015-04-22T11:58:41.347308+00:00",
    "fruit": "orange",
    "fruit_id": "455aab1b747e40a89034877e2c963179",
    "updated_on": "2015-04-22T11:58:41.347308+00:00"
}
>
```

##Delete
```bash
>curl -s -X DELETE http://127.0.0.1:8445/v1.0/fruits/455aab1b747e40a89034877e2c963179
>
```

##Read All
```bash
>#create 10 fruit resources
>for i in `seq 10`; do curl -s -X POST http://127.0.0.1:8445/v1.0/fruits; done
>#lots of output cut
>curl -s http://127.0.0.1:8445/v1.0/fruits | python -m json.tool
>#lots of output cut
```

# Service's Data Model
```bash
curl http://127.0.0.1:5984/tor_async_couchdb_basic_sample/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
```
