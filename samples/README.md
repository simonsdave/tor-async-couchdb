# Samples
The samples below demonstrate how to use the capabilities
of ```tor-async-couchdb```.
The first sample ([basic](crud/basic)) is very simple and uses only the fundamental
features of ```tor-async-couchdb```. Subsequent samples build on
[basic](crud/basic) exercising increasingly more advanced features
of ```tor-async-couchdb```.

Before running any of the samples you'll need to install
some pre-reqs.

```bash
>pip install -r requirements.txt
.
.
.
>
```

In terms of the structure of the samples.
Each of the samples is structured in the same way and follows
a [Data, context and interaction (DCI)](http://en.wikipedia.org/wiki/Data,_context_and_interaction)
style of paradigm.
	* model.py contains model classes (DCI's *data*)
	* async_action.py contains classes that implement async operations which operate on models (DCI's *interaction*)
	* service.py contains all Tornado request handlers and the service's mainline - request handlers
	  create instances of async actions to async'ly operate on models (DCI's *context*)

## [basic](crud/basic)
This service implements a simple RESTful service that
demonstrates how the foundational features of ```tor-async-couchdb```
are intended to be used.

## [retry](crud/retry)
This service implements a simple RESTful service that
builds on the [basic](crud/basic) sample.
Specifically, this sample illustrates how
to implement on-write retry logic that works with CouchDB's
Multi-Version Concurrency Control (MVCC) approach to conflicts.

## [exponential backoff](crud/exp_backoff)
This service implements a simple RESTful service that
builds on the [retry](crud/retry) sample.
Specifically, this sample illustrates how
to refine [retry](crud/retry)'s retry logic using
and an exponential backoff strategy.

## multi-master
WIP

## [health](health)
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_health```
endpoint.
This sample includes an implementation of a ```/_health``` endpoint that
follows these architectural guidelines and demonstrates how to use
the ```AsyncCouchDBHealthCheck``` class.

## [metrics](metrics)
As described in [these](https://github.com/simonsdave/microservice-architecture)
architectural guidelines, all services should implement a ```/_metrics```
endpoint.
This sample includes an implementation of a ```/_metrics``` endpoint that
follows these architectural guidelines and demonstrates how to use
the ```AsyncDatabaseMetricsRetriever``` class.

## tampering
WIP

## hash and encrypt
WIP

# Utilities

## [db_installer](db_installer)
[db_installer](db_installer) demonstrates how to use ```tor-async-couchdb```
to create a CouchDB database installer. The database created by
the installer is used for each of the ```tor-async-couchdb```
samples.

## [test_all_samples.sh](test_all_samples.sh)
This shell script runs each sample service through a simple set
of sanity tests.

```bash
>nosetests tests.py
...
----------------------------------------------------------------------
Ran 3 tests in 0.646s

OK
>
```

## [loadgen](loadgen)
A [locust](http://locust.io/) based utility which drives CRUD style
load through the sample services to demonstrate ```tor-async-couchdb```'s
conflict resolution logic.
