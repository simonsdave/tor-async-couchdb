#!/usr/bin/env bash
#
# this script starts each sample's service and runs a sanity
# check test. this script is intended to be run as part of
# the project's CI process.
#

set -e

run_sample() {
    SERVICE_DIR=$1
    UNIT_TESTS_DIR=$2

    DATABASE_HOST=http://couchdb:5984
    DATABASE=tor_async_couchdb_sample

    echo "running tests for sample \"$SERVICE_DIR\""

    docker run \
        --rm \
        --network "$DEV_ENV_NETWORK" \
        --volume "$DEV_ENV_SOURCE_CODE:/app" \
        "$DEV_ENV_DOCKER_IMAGE" \
        /app/samples/db_installer/installer.py "--host=$DATABASE_HOST" --delete=true --create=true

    SERVICE_CONTAINER_ID=$(docker run \
        -d \
        --rm \
        --name service \
        --network "$DEV_ENV_NETWORK" \
        --volume "$DEV_ENV_SOURCE_CODE:/app" \
        "$DEV_ENV_DOCKER_IMAGE" \
        "/app/samples/$SERVICE_DIR/service.py" "--database=$DATABASE_HOST/$DATABASE")

    docker run \
        --rm \
        --network "$DEV_ENV_NETWORK" \
        --volume "$DEV_ENV_SOURCE_CODE:/app" \
        "$DEV_ENV_DOCKER_IMAGE" \
        nosetests "/app/samples/$UNIT_TESTS_DIR/tests.py"

    docker kill "$SERVICE_CONTAINER_ID" > /dev/null

    echo "finished tests for sample \"$SERVICE_DIR\""
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
