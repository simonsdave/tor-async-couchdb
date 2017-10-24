# Change Log
All notable changes to this project will be documented in this file.
Format of this file follows [these](http://keepachangelog.com/) guidelines.
This project adheres to [Semantic Versioning](http://semver.org/).

## [%RELEASE_VERSION%] - [%RELEASE_DATE%]

### Added
- SIGINT handler to all samples which is helpful for scripting tests

### Changed
- tornado 4.4 -> 4.5.2
- pep8 1.7.0 -> 1.7.1

### Removed
- ...

## [0.50.1] - [2017-02-12]

### Changed
- fixed silly install bug introduced in 0.50.0

## [0.50.0] - [2017-01-08]

### Changed
- refine & simplify samples given the samples form the primary project documenation
- python-dateutil 2.4.2 -> 2.6.0
- tornado 4.4.1 -> 4.4
- locustio 0.7.3 -> 0.7.5
- python-keyczar 0.715 -> 0.716
- mock 1.3.0 -> 2.0.0
- flake8 2.5.1 -> 2.5.3

## [0.40.0] - [2016-01-13]

### Changed
- removed constraint on pycurl rev; pycurl now needs to be >= 7.19.5.1
- fixed exp_backoff sample
- allow a document ID to be specified when a document is first written
to CouchDB; also added AsyncModelRetrieverByDocumentID which allows
retrieval of a document by document ID; these capabilities are the
recommended pattern for using tor-async-couchdb but there are scenarios
where it is useful

## [0.20.0] - [2015-10-26]

### Changed
- requests added to setup.py so DB installer just works

### Added
- /_health sample using AsyncCouchDBHealthCheck
- AsyncDatabaseMetricsRetriever async action to retrieve database metrics
- /_metrics sample using new AsyncDatabaseMetricsRetriever

## [0.12.0] - [2015-08-21]

### Changed
- ton of async_model_actions.py refactoring
- material improvement in samples
- added AsyncCouchDBHealthCheck integration tests
- all samples now use ```tornado.curl_httpclient.CurlAsyncHTTPClient``` - see
[this](http://tornado.readthedocs.org/en/latest/httpclient.html) for a quick
explaination of why ```curl_httpclient``` is used instead of ```simple_httpclient```
- if available, detailed timing info describing phases of the interaction
with CouchDB now generates an info level log - see
[this](http://tornado.readthedocs.org/en/latest/httpclient.html#response-objects)
Tornado info and [this](http://curl.haxx.se/libcurl/c/curl_easy_getinfo.html#TIMES)
libcurl info for a description of the timing details. the log message will look
something like:

```
2015-08-20T11:52:46.335+00:00 INFO async_model_actions CouchDB took 17.26 ms
to respond with 200 to 'GET' against >>>http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id/_view/fruit_by_fruit_id?key=%222c794f79e43f4c2093d0fb7057ef978e%22&include_docs=true<<< -
timing detail: q=12.06 ms n=0.01 ms c=0.02 ms p=0.04 ms s=16.81 ms t=16.96 ms r=0.00 ms
```

## [0.11.0] - [2015-06-17]

### Changed
- aync_model_actions.AsyncModelsRetriever enable querying via start/end keys
- installer skip pre-existing databases and design document

## [0.10.0] - [2015-05-26]
### Added
- async_model_actions.AsyncDeleter enables async deletion

### Changed
- installer loads *.json files from regular directory (instead of *.py from
  python package)
- AsyncPersister now requires dictionaries returned by as_doc_for_store()
  in derived classes of Model always return a type property of the form
  ^[^\s]+_v\d+\.\d+$ - this change is key to enabling automated conflict
  resolution
- Update dependencies

## [0.9.2] - [2015-03-01]
- not really the initial release but intro'ed CHANGELOG.md late
