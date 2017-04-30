# Health
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_metrics```
endpoint.
This sample includes an implementation of a ```/_metrics``` endpoint that
follows these architectural guidelines and demonstrates how to use
the ```AsyncDatabaseMetricsRetriever``` class.

Create an empty database using the [sample database installer](../db_installer)

```bash
>./installer.py --log=info --delete=true --create=true
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Deleting database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Successfully deleted database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Successfully created database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design documents in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit' in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/db_installer/design_docs/fruit_by_fruit.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit_id' in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/db_installer/design_docs/fruit_by_fruit_id.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id'
INFO:tor_async_couchdb.installer:Creating seed documents in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/db_installer/seed_docs/apple.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/05d4d63d0f0338cebd34f97a8600041d' from '/Users/dave.simons/tor-async-couchdb/samples/db_installer/seed_docs/apple.json'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/db_installer/seed_docs/conflicts.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://127.0.0.1:5984/tor_async_couchdb_sample/05d4d63d0f0338cebd34f97a86000769' from '/Users/dave.simons/tor-async-couchdb/samples/db_installer/seed_docs/conflicts.json'
```

Start the sample:

```bash
>./service.py
2015-09-23T12:20:16.998+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample
```

Issue a GET to the ```/_metrics``` endpoint to get a sense the response.

```bash
>curl -s http://127.0.0.1:8445/v1.0/_metrics | jq .
{
  "links": {
    "self": {
      "href": "http://127.0.0.1:8445/v1.0/_metrics"
    }
  },
  "database": {
    "fragmentation": 70,
    "dataSize": 1265,
    "diskSize": 4197,
    "views": {
      "fruit_by_color": {
        "fragmentation": 100,
        "dataSize": 0,
        "diskSize": 51
      },
      "fruit_by_fruit_id": {
        "fragmentation": 100,
        "dataSize": 0,
        "diskSize": 51
      }
    },
    "docCount": 4
  }
}
>
```

An exercise left the the reader ... run the [loadgen](../loadgen) utility
and the query the ```/_metrics``` to get a sense of how the database's
data shape evolves.
