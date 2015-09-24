# CouchDB Database Installer
[installer.py](installer.py) demonstrates how to use ```tor-async-couchdb```
to create a CouchDB database installer. The database created by
the installer is used for each of the ```tor-async-couchdb```
samples.

#Creating the CouchDB Database

Create the database on CouchDB running on ```http://127.0.0.1:5984```
using the installer.
```bash
>./installer.py --log=info --delete=true --create=true
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Deleting database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Successfully deleted database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Successfully created database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design documents in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit' in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave/tor-async-couchdb/samples/db_installer/design_docs/fruit_by_fruit.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit_id' in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave/tor-async-couchdb/samples/db_installer/design_docs/fruit_by_fruit_id.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id'
INFO:tor_async_couchdb.installer:Creating seed documents in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave/tor-async-couchdb/samples/db_installer/seed_docs/apple.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/053003c8a02820f0b1468add4f14d602' from '/Users/dave/tor-async-couchdb/samples/db_installer/seed_docs/apple.json'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave/tor-async-couchdb/samples/db_installer/seed_docs/conflicts.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/053003c8a02820f0b1468add4f14daf0' from '/Users/dave/tor-async-couchdb/samples/db_installer/seed_docs/conflicts.json'
>
```

# Data Model

There's only one document type in the sample database = Fruits.

All timestamps a represented as strings with the format
"YYYY-MM-DDTHH:MM:SS.MMMMMM+00:00" which is important because
in this format sorting strings that are actually dates
will work as you expect.

If a document property is mutable then a conflict resolution
strategy must be identified
  * N/A = no conflict resolution strategy because the property is immutable
  * latest by updated_on timestamp = use the property that is most recent as defined by the document's updated_on timestamp
  * latest = only useful for datetime/timestamp properties; the most recent of n dates

| Attribute | Type | Mutable | Conflict Resolution Strategy | Comments |
|:---------:|:----:|:-------:|:----------------------------:|:--------:|
| type | string | no | N/A | always = "fruit_v1.0" |
| fruit | string | yes | latest by updated_on timestamp | |
| created_on | string (timestamp) | no | N/A | |
| updated_on | string (timestamp) | yes | latest | |

# API

## fruit_by_fruit_id

```bash
(env)>curl -s 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id/_view/fruit_by_fruit_id?include_docs=true' | python -m json.tool
{
    "offset": 0,
    "rows": [
        {
            "doc": {
                "_id": "053003c8a02820f0b1468add4f14d602",
                "_rev": "1-ecf6cb723837bcc689623d9ec48953ce",
                "created_on": "2015-06-17T19:54:02.133017+00:00",
                "fruit": "apple",
                "fruit_id": "e370582d3894489192a679533e4f01ef",
                "type": "fruit_v1.0",
                "updated_on": "2015-06-17T19:54:02.133017+00:00"
            },
            "id": "053003c8a02820f0b1468add4f14d602",
            "key": "e370582d3894489192a679533e4f01ef",
            "value": null
        }
    ],
    "total_rows": 1
}
```

## fruit_by_fruit

```bash
>curl -s 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit/_view/fruit_by_fruit?include_docs=true' | python -m json.tool
{
    "offset": 0,
    "rows": [
        {
            "doc": {
                "_id": "053003c8a02820f0b1468add4f14d602",
                "_rev": "1-ecf6cb723837bcc689623d9ec48953ce",
                "created_on": "2015-06-17T19:54:02.133017+00:00",
                "fruit": "apple",
                "fruit_id": "e370582d3894489192a679533e4f01ef",
                "type": "fruit_v1.0",
                "updated_on": "2015-06-17T19:54:02.133017+00:00"
            },
            "id": "053003c8a02820f0b1468add4f14d602",
            "key": "apple",
            "value": null
        }
    ],
    "total_rows": 1
}
>
```
