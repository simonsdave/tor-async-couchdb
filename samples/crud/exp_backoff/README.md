# Exponential Backoff Strategy Sample
This service implements a simple RESTful service that
builds on the [retry sample](../retry).
Specifically, this sample illustrates how
to realize an exponential backoff strategy during on-write retry.
If you compare the [retry sample's async actions logic](../retry/async_actions.py)
with [this sample's async action logic](async_actions.py) you'll
see the introduction of the exponential backoff strategy when conflicts are detected.

Everything ITO creating the CouchDB database, running the service, etc
is the same as for [retry sample](../retry). The only outward difference
you should be able to detect between this sample and the [retry sample](../retry)
can be found in the service's logs after running a stress test.
More specifically, try grepping the service's logs per the example
below. Contention levels created by the [load generator](../loadgen) 
will determine how many retries are attempted.

```bash
(env)>grep "Conflict detected updating fruit" service.log
2015-05-01T10:42:32.562+00:00 INFO async_actions Conflict detected updating fruit '1ea993fd52754b6cb5264da70e93a03d' - waiting for a bit
2015-05-01T10:42:32.618+00:00 INFO async_actions Conflict detected updating fruit '1ea993fd52754b6cb5264da70e93a03d' - retrying update after waiting 55 ms
2015-05-01T10:42:32.737+00:00 INFO async_actions Conflict detected updating fruit 'dfd16c86bf2240cf9fc5cb6b2f9fb280' - waiting for a bit
2015-05-01T10:42:32.798+00:00 INFO async_actions Conflict detected updating fruit 'dfd16c86bf2240cf9fc5cb6b2f9fb280' - retrying update after waiting 60 ms
2015-05-01T10:42:32.839+00:00 INFO async_actions Conflict detected updating fruit 'dfd16c86bf2240cf9fc5cb6b2f9fb280' - waiting for a bit
2015-05-01T10:42:32.887+00:00 INFO async_actions Conflict detected updating fruit 'dfd16c86bf2240cf9fc5cb6b2f9fb280' - retrying update after waiting 47 ms
```
