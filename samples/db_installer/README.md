#CouchDB Database Installer
```installer.py``` demonstrates how to use ```tor-async-couchdb```
to create a CouchDB database installer. The database created by
the installer is used for each of the ```tor-async-couchdb```
samples.

#Creating the CouchDB Database

Create the database on CouchDB running on ```http://127.0.0.1:5984```
using the installer.
```bash
>./installer.py --create=true --log=info
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Creating database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Successfully created database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design documents in database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984'
INFO:tor_async_couchdb.installer:Creating design doc 'fruit_by_fruit_id' in database 'tor_async_couchdb_sample_basic' on 'http://127.0.0.1:5984' from file '/Users/dave.simons/tor-async-couchdb/samples/basic/design_docs/fruit_by_fruit_id.py'
INFO:requests.packages.urllib3.connectionpool:Starting new HTTP connection (1): 127.0.0.1
INFO:tor_async_couchdb.installer:Successfully created design doc 'http://127.0.0.1:5984/tor_async_couchdb_sample_basic/_design/fruit_by_fruit_id'
```
