#loadgen
A [locust](http://locust.io/) based utility which drives CRUD style
load through the sample services to demonstrate ```tor-async-couchdb```'s
conflict resolution logic.

[loadgen.sh](loadgen.sh) starts [locust](http://locust.io/) to drive
requests to a sample service which is assumed to be runing on
[http://127.0.0.1:8445](http://127.0.0.1:8445). When [locustfile.py](locustfile.py)
is loaded by [locust](http://locust.io/) it first issues a number
of ```POST``` requests to create a collection of fruit resources which are then
the target of ```GET``` and ```PUT``` requests [locust](http://locust.io/).

There are a few parameters
which can be tweak to control the shape and intensity of the generated traffic.

* total number of requests and number of concurrent requests
are configured in [loadgen.sh](loadgen.sh) - look for the
```--num-request``` and ```--clients``` [locust](http://locust.io/)
command line args
* the relative number of ```GET``` and ```PUT``` requests is controlled
by the ```_weight_get``` and ```_weight_put``` variables in
[locustfile.py](locustfile.py)
* the number of fruits initial created is defined by ```_number_fruits```
in [locustfile.py](locustfile.py)

Note - this should be obvious but in case not ...
the loadgen utility is designed to exercise ```tor-async-couchdb```'s
conflict resolution logic which is trigged when multiple requests attempt to
do things to the same resource.
The probability is a conflict being generated increases both as the number
of concurrent requests increases and the number of resources decreases.
