#!/usr/bin/env python

import datetime
import httplib
import json
import time
import uuid
import sys

import requests

base_url = "https://127.0.0.1:8445"


def create_database(host, db):
    url = "%s/%s" % (host, db)

    response = requests.get(url)
    if response.status_code == httplib.OK:
        response = requests.delete(url)
        if response.status_code != httplib.OK:
            print "Error deleting database '%s'" % url
            return False
        else:
            print "Successfully deleted database '%s'" % url

    response = requests.put(url)
    if response.status_code != httplib.CREATED:
        print "Error creating database '%s'" % url
        return False

    #
    # install view which grabs docs in conflict
    #
    url = "%s/%s/_design/conflicts" % (host, db)
    headers = {
        "Content-Type": "application/json",
    }
    view = (
        '{'
        '    "language": "javascript",'
        '    "views": {'
        '        "conflicts": {'
        '            "map": "function(doc) { if(doc._conflicts) { emit(doc._conflicts, null); } }"'
        '        }'
        '    }'
        '}'
    )
    response = requests.put(
        url,
        headers=headers,
        data=view)
    if response.status_code != httplib.CREATED:
        print "Error creating conflicts view"
        return False

    #
    # install view which grabs docs by doc id
    #
    url = "%s/%s/_design/docs_by_doc_id" % (host, db)
    headers = {
        "Content-Type": "application/json",
    }
    view = (
        '{'
        '    "language": "javascript",'
        '    "views": {'
        '        "docs_by_doc_id": {'
        '            "map": "function(doc) { emit(doc.doc_id, null); }"'
        '        }'
        '    }'
        '}'
    )
    response = requests.put(
        url,
        headers=headers,
        data=view)
    if response.status_code != httplib.CREATED:
        print "Error creating conflicts view"
        return False

    print "Successfully created database '%s'" % url
    return True


def trigger_replication(host, source_db, target_db):
    print "Firing replication from '%s' to '%s'" % (source_db, target_db)
    payload = {
        "source": source_db,
        "target": target_db,
    }
    headers = {
        "Content-Type": "application/json",
    }
    url = "%s/_replicate" % host
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload))
    if response.status_code != httplib.OK:
        print "Error firing replication from '%s' to '%s'" % (source_db, target_db)
        return False

    # :TODO: how do we wait for replication to complete?
    """
    print '+'*50
    print response
    print response.headers
    print json.dumps(response.json(), indent=4)
    print '+'*50
    """

    print "Successfully fired replication from '%s' to '%s'" % (source_db, target_db)
    return True


class Conflict(object):

    def __init__(self, current_rev, revs_in_conflict):
        object.__init__(self)

        self.current_rev = current_rev
        self.revs_in_conflict = revs_in_conflict


def get_conflicts(host, db):
    url = "%s/%s/_design/conflicts/_view/conflicts" % (host, db)
    response = requests.get(url)
    if response.status_code != httplib.OK:
        print "Error getting conflicts '%s':-(" % url
        return None

    conflicts = []

    for conflict in response.json()["rows"]:
        id = conflict["id"]
        original = get_document_by__id(host, db, id)
        conflicts.append(Conflict(original, []))

    return conflicts


def create_document(host, db):
    doc_id = uuid.uuid4().hex
    payload = {
        "doc_id": doc_id,
        "ts": datetime.datetime.now().isoformat(),
    }
    headers = {
        "Content-Type": "application/json",
    }
    url = "%s/%s" % (host, db)
    response = requests.post(
        url,
        headers=headers,
        data=json.dumps(payload))
    if response.status_code != httplib.CREATED:
        print "Error creating document '%s':-(" % url
        return None

    """
    print response.headers["location"]
    """

    fmt = "Successfully created doc (id = '%s') document on '%s/%s' :-("
    print fmt % (doc_id, host, db)
    return doc_id


def get_document_by_doc_id(host, db, doc_id):
    url_fmt = "%s/%s/_design/docs_by_doc_id/_view/docs_by_doc_id?key=%s&include_docs=true"
    url = url_fmt % (host, db, json.dumps(doc_id))
    response = requests.get(url)
    if response.status_code != httplib.OK:
        print "Error getting document '%s':-(" % url
        return None

    response = response.json()
    rows = response["rows"]
    assert 1 == len(rows)
    row = rows[0]
    doc = row["doc"]
    return doc


def get_document_by__id(host, db, id, rev=None):
    url = "%s/%s/%s" % (host, db, id)
    if rev is not None:
        url = "%s&rev=%s" % (url, rev)
    response = requests.get(url)
    if response.status_code != httplib.OK:
        print "Error getting document '%s':-(" % url
        return None

    return response.json()


def update_document(host, db, doc):
    doc["ts"] = datetime.datetime.now().isoformat()
    headers = {
        "Content-Type": "application/json",
    }
    url = "%s/%s/%s" % (host, db, doc["_id"])
    response = requests.put(
        url,
        headers=headers,
        data=json.dumps(doc))
    if response.status_code != httplib.CREATED:
        print "Error creating updating '%s':-(" % url
        return False

    fmt = "Successfully updated doc (doc_id = '%s') document on '%s/%s' :-("
    print fmt % (doc["doc_id"], host, db)

    return True


def assert_base_docs_equal(doc1, doc2):
    assert doc1 is not None
    assert doc2 is not None
    assert doc1["doc_id"] == doc2["doc_id"]


def assert_docs_equal(doc1, doc2):
    assert_base_docs_equal(doc1, doc2)
    assert doc1["ts"] == doc2["ts"]


def assert_docs_not_equal(doc1, doc2):
    assert_base_docs_equal(doc1, doc2)
    assert doc1["ts"] != doc2["ts"]


def main():
    host = "http://localhost:5984"
    db1 = "dave001"
    db2 = "dave002"

    create_database(host, db1)
    create_database(host, db2)

    doc_id = create_document(host, db1)
    assert doc_id
    doc = get_document_by_doc_id(host, db1, doc_id)

    assert trigger_replication(host, db1, db2)

    assert_docs_equal(
        get_document_by_doc_id(host, db1, doc_id),
        get_document_by_doc_id(host, db2, doc_id))

    assert update_document(host, db1, get_document_by_doc_id(host, db1, doc_id))

    assert_docs_not_equal(
        get_document_by_doc_id(host, db1, doc_id),
        get_document_by_doc_id(host, db2, doc_id))

    assert trigger_replication(host, db1, db2)

    assert_docs_equal(
        get_document_by_doc_id(host, db1, doc_id),
        get_document_by_doc_id(host, db2, doc_id))

    #
    # ...
    #

    assert update_document(host, db1, get_document_by_doc_id(host, db1, doc_id))
    assert update_document(host, db2, get_document_by_doc_id(host, db2, doc_id))

    assert_docs_not_equal(
        get_document_by_doc_id(host, db1, doc_id),
        get_document_by_doc_id(host, db2, doc_id))

    assert trigger_replication(host, db1, db2)

    time.sleep(1)

    assert_docs_not_equal(
        get_document_by_doc_id(host, db1, doc_id),
        get_document_by_doc_id(host, db2, doc_id))

    conflicts = get_conflicts(host, db1)
    assert 0 == len(conflicts)

    conflicts = get_conflicts(host, db2)
    assert 1 == len(conflicts)
    print conflicts

main()
