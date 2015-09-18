# Health Endpoint Sample
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_health```
endpoint.
The [exponential backoff](../exp_backoff) sample includes an implementation
of a ```/_health``` endpoint that follows these architectural guidelines
and demonstrates how to use ```AsyncCouchDBHealthCheck```.

More specifically:

* a GET to ```/_health``` returns a 200 OK as long as the get can
reach the service
* a GET to ```/_health``` with the query string parameter ```quick```
set to ```false``` returns a 200 OK if all of the following are satisfied:
  * the service can reach CouchDB
  * the database is using @ least 1 MB of disk space and
  fragmentation level is less than 80
  * every view in the database is using @ least 1 MB of disk space and
  fragmentation level is less than 80

Demonstrating how the ```/_health``` endpoint works requires
some work but it's really pretty cool to see all the moving pieces
in action:-) Here's an overview of what we're going to do:

* start the [exponential backoff](../exp_backoff) sample
* in two [Bash](https://en.wikipedia.org/wiki/Bash_(Unix_shell)
start a while loop that sleeps for one second and the queries
the ```/_health``` endpoint - one of the while loops will use
```quick``` equals ```true``` and the other ```false```
* start a load test to create fragmentation in the database
and watch as the health checks got from ```green``` to ```yellow```
and finally to ```red```.   

Start the [exponential backoff](../exp_backoff) sample:

```bash
>./service.py
2015-09-18T02:20:04.785+00:00 INFO service service started and listening on http://127.0.0.1:8445 talking to database http://127.0.0.1:5984/tor_async_couchdb_sample
```

Issue a GET to the ```/_health``` endpoint to get a sense the response.

```bash
>curl -s http://127.0.0.1:8445/v1.0/_health | python -m json.tool
{
    "links": {
        "self": {
            "href": "http://127.0.0.1:8445/v1.0/_health"
        }
    },
    "status": "green"
}
>
```

Now let's add the quick query string parameter to the GET request.
Note the addition of view specific status.

```bash
>!curl
curl -s http://127.0.0.1:8445/v1.0/_health?quick=false | python -m json.tool
{
    "database": {
        "fragmentation": {
            "status": "green"
        },
        "views": {
            "fruit_by_fruit_id": {
                "status": "green"
            }
        }
    },
    "links": {
        "self": {
            "href": "http://127.0.0.1:8445/v1.0/_health"
        }
    },
    "status": "green"
}
>
```

```bash
>while true; do curl -s -o /dev/null -s -w '%{http_code}\n' http://127.0.0.1:8445/v1.0/_health; sleep 1; done
200
200
```
