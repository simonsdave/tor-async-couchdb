#!/usr/bin/env bash
#
# this script starts each sample's service and runs a sanity
# check test. this script is intended to be run as part of
# the project's CI process.
#

SCRIPT_DIR_NAME="$( cd "$( dirname "$0" )" && pwd )"

run_crud_sample() {
    pushd "$SCRIPT_DIR_NAME" >& /dev/null
    SAMPLE_DIR=crud/$1
    echo "running tests for sample \"$SAMPLE_DIR\""
    "./db_installer/installer.py" --delete=true --create=true
    SERVICE_DOT_PY=./$SAMPLE_DIR/service.py
    SERVICE_OUTPUT=$(mktemp)
    "$SERVICE_DOT_PY" >& "$SERVICE_OUTPUT" &
    SERVICE_PID=$!
    sleep 1
    ps --pid $SERVICE_PID >& /dev/null
    if [ $? -ne 0 ]; then
        echo "error starting \"$SERVICE_DOT_PY\". pre-req's installed?" >&2
        exit 1
    fi

    nosetests crud

    kill -INT $SERVICE_PID
    rm "$SERVICE_OUTPUT"
    "./db_installer/installer.py" --delete=true --create=true
    echo "finished tests for sample \"$SAMPLE_DIR\""
    popd >& /dev/null
}

run_non_crud_sample() {
    pushd "$SCRIPT_DIR_NAME" >& /dev/null
    SAMPLE_DIR=$1
    echo "running tests for sample \"$SAMPLE_DIR\""
    "./db_installer/installer.py" --delete=true --create=true
    SERVICE_DOT_PY=./$SAMPLE_DIR/service.py
    SERVICE_OUTPUT=$(mktemp)
    "$SERVICE_DOT_PY" >& "$SERVICE_OUTPUT" &
    SERVICE_PID=$!
    sleep 1
    ps --pid $SERVICE_PID >& /dev/null
    if [ $? -ne 0 ]; then
        echo "error starting \"$SERVICE_DOT_PY\". pre-req's installed?" >&2
        exit 1
    fi

    nosetests $SAMPLE_DIR

    kill -INT $SERVICE_PID
    rm "$SERVICE_OUTPUT"
    echo "finished tests for sample \"$SAMPLE_DIR\""
    popd >& /dev/null
}

run_crud_sample basic
run_crud_sample retry
run_crud_sample exp_backoff
run_non_crud_sample health
run_non_crud_sample metrics

exit 0
