# Health
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_health```
endpoint.
This sample includes an implementation of a ```/_health``` endpoint that
follows these architectural guidelines and demonstrates how to use
the ```AsyncCouchDBHealthCheck``` class.

An overview of the ```/_health``` endpoint's behavior:

* a GET to ```/_health``` returns 200 OK if the service is healthy
and 503 Service Unavailable if there's a health problem
* "health" is "calculated" by the service and depends on the presence
and value of query string parameter ```quick``` in the ```/_health``` request
* if ```quick``` isn't a query string parameter or if it's value is
```true``` then 200 OK is always returned
* if the value of ```quick``` is
```false``` ```/_health``` uses ```AsyncCouchDBHealthCheck``` to confirm
the app tier can successfully make requests to required CouchDB database

The steps below describe how to run this sample and
interact with the ```/_health``` endpoint.

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

```bash
>curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | jq .
{
  "status": "green",
  "links": {
    "self": {
      "href": "http://127.0.0.1:8445/v1.0/_health?quick=false"
    }
  }
}
>
```

Did the service do anything differently? Yes but to see this we'll have
to look at service.py's logs. From the logs below, you'll see the two
GET requests we issued above. Notice that right before the second GET
returned there's a log entry indicating a request was made to
```http://127.0.0.1:5984/tor_async_couchdb_sample```.

```bash
>./service.py
2015-09-23T12:36:21.114+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample
2015-09-23T12:36:23.665+00:00 INFO web 200 GET /v1.0/_health (127.0.0.1) 0.99ms
2015-09-23T12:36:26.388+00:00 INFO async_model_actions CouchDB took 2.32 ms to respond with 200 to 'GET' against >>>http://127.0.0.1:5984/tor_async_couchdb_sample/<<< - timing detail: q=0.68 ms n=0.02 ms c=0.24 ms p=0.28 ms s=1.40 ms t=1.88 ms r=0.00 ms
2015-09-23T12:36:26.388+00:00 INFO web 200 GET /v1.0/_health?quick=false (127.0.0.1) 3.80ms
```

Let's have a bit of fun ...

Start a while loop that repeats a GET to ```/_health?quick=true```

```bash
>while true; do curl -s -o /dev/null -s -w '%{http_code}\n' http://127.0.0.1:8445/v1.0/_health?quick=true; sleep 1; done
200
200
.
.
.
```

Start another while loop that repeats a ```/_health?quick=false```

```bash
>while true; do curl -s -o /dev/null -s -w '%{http_code}\n' http://127.0.0.1:8445/v1.0/_health?quick=false; sleep 1; done
200
200
.
.
.
```

Start a while loop which endlessly creates and deletes the sample database

```bash
>while true; do ./installer.py --log=error --delete=true --create=false; sleep 5; ./installer.py --log=error --delete=false --create=true; sleep 5; done
```

What you'll see is that our ```/_health?quick=true``` loop keeps coming
back with 200 OK but ```/_health?quick=false``` shows 5 or 6 200 OKs followed
by 5 ot 6 503 Service Unavailable.

An exercise left to the reader ... try shutting down and restarting CouchDB
to understand the impact on the response from ```/_health?quick=false```
