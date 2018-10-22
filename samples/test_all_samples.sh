#!/usr/bin/env bash
#
# this script starts each sample's service and runs a sanity
# check test. this script is intended to be run as part of
# the project's CI process.
#

set -e

SCRIPT_DIR_NAME="$( cd "$( dirname "$0" )" && pwd )"

run_sample() {
    SAMPLE_DIR=$1
    UNIT_TESTS_DIR=$2
    DATABASE_HOST=http://172.17.0.1:5984
    DATABASE=tor_async_couchdb_sample
    echo "running tests for sample \"$SAMPLE_DIR\""

    pushd "$SCRIPT_DIR_NAME" >& /dev/null || exit 1


    "./db_installer/installer.py" \
        --delete=true \
        --create=true \
        --host=$DATABASE_HOST \
        --database=$DATABASE
    SERVICE_DOT_PY=./$SAMPLE_DIR/service.py
    SERVICE_OUTPUT=$(mktemp)
    "$SERVICE_DOT_PY" --database=$DATABASE_HOST/$DATABASE >& "$SERVICE_OUTPUT" &
    SERVICE_PID=$!
    sleep 1
    if ! ps --pid $SERVICE_PID >& /dev/null; then
        echo "error starting \"$SERVICE_DOT_PY\". pre-req's installed?" >&2
        exit 1
    fi

    nosetests "$UNIT_TESTS_DIR"

    kill -INT $SERVICE_PID
    rm "$SERVICE_OUTPUT"
    "./db_installer/installer.py" \
        --delete=true \
        --create=false \
        --host=$DATABASE_HOST \
        --database=$DATABASE
    echo "finished tests for sample \"$SAMPLE_DIR\""

    popd >& /dev/null || exit 1
}

run_crud_sample() {
    run_sample "crud/$1" crud
}

run_non_crud_sample() {
    run_sample "$1" "$1"
}

run_crud_sample basic
run_crud_sample retry
run_crud_sample exp_backoff
run_non_crud_sample health
run_non_crud_sample metrics

exit 0
