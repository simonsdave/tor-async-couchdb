#Samples

#[basic](basic)
This service implements a simple RESTful service that
demonstrates how the basic features of ```tor-async-couchdb``` were intended to be used.
This is the first in a series of samples services.
We'll build on this basic sample service as we explore the more
advanced features of ```tor-async-couchdb```.

#[retry](retry)
This service implements a simple RESTful service that
builds on the [basic](basic) sample.
Specifically, this sample illustrates how
to implement on-write retry logic that works with CouchDB's
Multi-Version Concurrency Control (MVCC) approach to conflicts.

#[tests.py](tests.py)
Once you have spun up one of the sample services you can run
a sanity test suite against the service using a
[nose](https://nose.readthedocs.org/en/latest/) runnable
integration test suite in [tests.py](tests.py).
The test suite is hard-coded to talk to a service at
[http://127.0.0.1:8445](http://127.0.0.1:8445) so edit
the test if you are running the service at a different
endpoint.

```bash
>nosetests tests.py
...
----------------------------------------------------------------------
Ran 3 tests in 0.646s

OK
>
```

#[loadgen](loadgen)
A [locust](http://locust.io/) based utility which drives CRUD style
load through the sample services to demonstrate ```tor-async-couchdb```'s
conflict resolution logic.
