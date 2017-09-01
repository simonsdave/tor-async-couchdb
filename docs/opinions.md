```tor-async-couchdb``` was created as a way to capture a very opinionated set of best practices
and learnings after operating and scaling a number of services that used CouchDB
and Tornado. The bullets below summarize these opinions.

* services should embrace eventual consistency
* thoughts on data models:
    * every document should have a versioned type property (ex *type=v9.99*)
    * documents are chunky aka retrieval of a single document should typically be all
    that's necessary to implement a RESTful service's endpoint
    ala standard NoSQL data model thinking
    * assume conflicts happen as part of regular operation
    * sensitive data at rest is an information security concern that must be addressed
        * each property should be evaluated against a data and information classification policy
        * [this](http://www.cmu.edu/iso/governance/guidelines/data-classification.html) is a good example of data classification policy
        * if a property is deemed sensitive it should ideally be hashed using [bcrypt](https://pypi.python.org/pypi/py-bcrypt/) if possible
        and otherwise [SHA3-512](http://en.wikipedia.org/wiki/SHA-3)
        * if a sensitive proprerty can't be hashed it should be encrypted using [Keyczar](http://www.keyczar.org/)
* direct tampering of data in the database is undesirable and therefore tamper resistance is both valued and a necessity
* to prevent unncessary fragmentation, CouchDB, not the service tier, should generate document IDs
* document retrieval should be done through views against document properties not document IDs
* one design document per view
* horizontally scaling CouchDB should be done using infrastructure (CouchDB 2.0 or Cloudant)
not application level sharding
