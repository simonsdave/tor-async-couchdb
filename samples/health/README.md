# Health Endpoint Sample
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_health```
endpoint.
The [exponential backoff](../exp_backoff) sample includes an implementation
of a ```/_health``` endpoint that follows these architectural guidelines
and demonstrates the use of ```AsyncCouchDBHealthCheck```.

> Note - you will get more from this sample if you:
> * have read and roughly understand [this blog](https://plus.google.com/+rkalla/posts/CyvwRcvh4vv)
which does a great job at explaining CouchDB's file format
> * remember that fragmentation can be thought of as the %
of a database or view's disk space being used to store old
document versions and/or metadata - see
[this](http://docs.couchdb.org/en/latest/config/compaction.html#compaction-daemon-rules)
for reference
> * have looked at the [exponential backoff](../exp_backoff) sample
> * have run the [sample database](../db_installer) utility
> * have run the [loadgen](../loadgen) utility
> * are familiar with both
[cURL](http://curl.haxx.se/) and [jq](https://stedolan.github.io/jq/)


More specifically:

* a GET to ```/_health``` returns 200 OK if the service is healthy
and 503 Service Unavailable if there's a health problem
* a GET to ```/_health``` returns a 200 OK as long as the GET can
reach the service
* a GET to ```/_health``` with the query string parameter ```quick```
set to ```false``` returns a 200 OK if all of the following are satisfied:
  * the GET can reach the service
  * the service can reach CouchDB
  * the CouchDB database is using @ least 1 MB of disk space and
  database fragmentation is less than 80
  * every view in the CouchDB database is using @ least 1 MB of disk space and
  fragmentation level is less than 80

Demonstrating how the ```/_health``` endpoint works requires
some work but it's really pretty cool to see all the moving pieces
in action:-) Here's an overview of what we're going to do:

* start the [exponential backoff](../exp_backoff) sample
* start some [bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)
while loops that query the ```/_health``` endpoint, sleep
and then repeat the loop - you'll see why more than one while loop
in a little bit
* start a load test to create fragmentation in the database
and watch as the health checks go from ```green``` to ```yellow```
and finally to ```red```.   

Create an empty database using [sample database](../db_installer)

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

Start the [exponential backoff](../exp_backoff) sample:

```bash
>./service.py
2015-09-18T02:20:04.785+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample
```

Issue a GET to the ```/_health``` endpoint to get a sense the response.

```bash
>curl -s http://127.0.0.1:8445/v1.0/_health | jq .
{
  "status": "green",
  "links": {
    "self": {
      "href": "http://127.0.0.1:8445/v1.0/_health"
    }
  }
}
>
```

Now let's add the quick query string parameter to the GET request.
Note the addition of database and view specific statuses.

```bash
>curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | jq .
{
  "status": "green",
  "links": {
    "self": {
      "href": "http://127.0.0.1:8445/v1.0/_health"
    }
  },
  "database": {
    "fragmentationStatus": "green",
    "views": {
      "fruit_by_fruit": {
        "fragmentationStatus": "green"
      },
      "fruit_by_fruit_id": {
        "fragmentationStatus": "green"
      }
    }
  }
}
>
```

Start the first while loop that repeats a ```/_health?quick=true``` once
every second.

```bash
>while true; do curl -s -o /dev/null -s -w '%{http_code}\n' http://127.0.0.1:8445/v1.0/_health?quick=true; sleep 1; done
200
200
.
.
.
```

Start a second while loop that repeats a ```/_health?quick=false``` once
every second.

```bash
>while true; do curl -s -o /dev/null -s -w '%{http_code}\n' http://127.0.0.1:8445/v1.0/_health?quick=false; sleep 1; done
200
200
.
.
.
```

Start a while loop that shows the status of
the database fragmentation

```bash
>while true; do curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | jq -c '.database.fragmentationStatus' | sed -e 's/\"//g'; sleep 1; done
green
green
.
.
.
```

Start a while loop that shows the status of
the fruit_by_fruit's view fragmentation

```bash
>while true; do curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | jq -c 'database.views.fruit_by_fruit.fragmentationStatus' | sed -e 's/\"//g'; sleep 1; done
green
green
.
.
.
```

Start a while loop that shows the status of
the fruit_by_fruit_id's view fragmentation

```bash
>while true; do curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | jq -c '.database.views.fruit_by_fruit_id.fragmentationStatus' | sed -e 's/\"//g'; sleep 1; done
green
green
.
.
.
```

```bash
while true; do curl -s http://127.0.0.1:8445/v1.0/_metrics | jq -c '.database.fragmentation' | sed -e 's/\"//g'; sleep 1; done
```

```bash
curl -H "Content-Type: application/json" -X POST http://localhost:5984/tor_async_couchdb_sample/_compact
```

To force fragmentation in the services database as quickly as possible
we configure the load generator to:
* minimize conflict 1/ lots of docs
* go quickly so 1/ lots of clients 2/ lots of writes
