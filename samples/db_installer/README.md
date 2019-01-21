# CouchDB Database Installer

[installer.py](installer.py) demonstrates how to use ```tor-async-couchdb```
to create a CouchDB database installer. The database created by
the installer is used for each of the ```tor-async-couchdb```
samples.

> Remember [cfg4dev](../../cfg4dev) started a docker container
> called ```couchdb``` on the docker network named by the environment
> variable ```DEV_ENV_NETWORK``` - knowing this will help explain some
> of the syntax in the docs below.

## ```installer.py``` Command Line Options

```bash
> docker run \
    --rm \
    --network "$DEV_ENV_NETWORK" \
    --volume "$DEV_ENV_SOURCE_CODE:/app" \
    "$DEV_ENV_DOCKER_IMAGE" \
    /app/samples/db_installer/installer.py --help
Usage: installer.py [options]

This utility used to create and/or delete the CouchDB database for
tor_async_couchdb's basic sample.

Options:
  -h, --help            show this help message and exit
  --log=LOGGING_LEVEL   logging level
                        [DEBUG,INFO,WARNING,ERROR,CRITICAL,FATAL] - default =
                        ERROR
  --host=HOST           where's CouchDB running - default =
                        http://127.0.0.1:5984
  --database=DATABASE   database - default = tor_async_couchdb_sample
  --creds=CREDS         creds - optional; format = user:password
  --delete=DELETE       delete before creating database - default = False
  --create=CREATE       create database - default = True
  --createdesign=CREATE_DESIGN_DOCS
                        create design docs - default = True
  --createseed=CREATE_SEED_DOCS
                        create seed docs - default = True
  --seeddocsigner=SEED_DOC_SIGNER_DIR_NAME
                        sign seed docs with this signer - default =
  --verify_host_ssl_cert=VERIFY_HOST_SSL_CERT
                        verify host's SSL certificate - default = True
>
```

## Creating the CouchDB Database

Create the database on CouchDB running on ```http://127.0.0.1:5984```
using the installer.
```bash
> docker run \
    --rm \
    --network "$DEV_ENV_NETWORK" \
    --volume "$DEV_ENV_SOURCE_CODE:/app" \
    "$DEV_ENV_DOCKER_IMAGE" \
    /app/samples/db_installer/installer.py --log=info --host=http://couchdb:5984 --delete=true --create=true
INFO:tor_async_couchdb.installer:Deleting database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Successfully deleted database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Creating database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Successfully created database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Creating design documents in database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit_id' in database 'tor_async_couchdb_sample' on 'http://couchdb:5984' from file '/app/samples/db_installer/design_docs/fruit_by_fruit_id.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://couchdb:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_color' in database 'tor_async_couchdb_sample' on 'http://couchdb:5984' from file '/app/samples/db_installer/design_docs/fruit_by_color.json'
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://couchdb:5984/tor_async_couchdb_sample/_design/fruit_by_color'
INFO:tor_async_couchdb.installer:Creating seed documents in database 'tor_async_couchdb_sample' on 'http://couchdb:5984'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://couchdb:5984' from file '/app/samples/db_installer/seed_docs/red.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://couchdb:5984/tor_async_couchdb_sample/26bd565b785a603781f0e91ce8001c12' from '/app/samples/db_installer/seed_docs/red.json'
INFO:tor_async_couchdb.installer:Creating seed doc in database 'tor_async_couchdb_sample' on 'http://couchdb:5984' from file '/app/samples/db_installer/seed_docs/conflicts.json'
INFO:tor_async_couchdb.installer:Successfully created seed doc 'http://couchdb:5984/tor_async_couchdb_sample/26bd565b785a603781f0e91ce800208b' from '/app/samples/db_installer/seed_docs/conflicts.json'
>
```

## Data Model

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
| color | string | yes | latest by updated_on timestamp | |
| created_on | string (timestamp) | no | N/A | |
| updated_on | string (timestamp) | yes | latest | |

## API

### fruit_by_fruit_id

```bash
(env)>curl -s 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_fruit_id/_view/fruit_by_fruit_id?include_docs=true' | jq .
{
    "offset": 0,
    "rows": [
        {
            "doc": {
                "_id": "053003c8a02820f0b1468add4f14d602",
                "_rev": "1-ecf6cb723837bcc689623d9ec48953ce",
                "created_on": "2015-06-17T19:54:02.133017+00:00",
                "color": "red",
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

### fruit_by_color

```bash
>curl -s 'http://127.0.0.1:5984/tor_async_couchdb_sample/_design/fruit_by_color/_view/fruit_by_color?include_docs=true' | jq .
{
    "offset": 0,
    "rows": [
        {
            "doc": {
                "_id": "053003c8a02820f0b1468add4f14d602",
                "_rev": "1-ecf6cb723837bcc689623d9ec48953ce",
                "created_on": "2015-06-17T19:54:02.133017+00:00",
                "color": "red",
                "fruit_id": "e370582d3894489192a679533e4f01ef",
                "type": "fruit_v1.0",
                "updated_on": "2015-06-17T19:54:02.133017+00:00"
            },
            "id": "053003c8a02820f0b1468add4f14d602",
            "key": "red",
            "value": null
        }
    ],
    "total_rows": 1
}
>
```
