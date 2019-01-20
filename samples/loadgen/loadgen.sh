#!/usr/bin/env bash

#
# this shell script is used to run the load generator
#
# exit codes
#
#   0   always
#

SCRIPT_DIR_NAME="$( cd "$( dirname "$0" )" && pwd )"

#
# some utility functions
#
usage() {
    echo "usage: $(basename "$0") [OPTION...]"
    echo ""
    echo "  -h, --help                              this message"
    echo "  -v, --verbose                           verbose output"
    echo "  -k6di, --k6-docker-image [IMAGE NAME]   k6 docker image (loadimpact/k6:0.16.0 = default)"
    echo "  -nf, --number-fruit [NUMBER FRUIT]      number fruit (50 = default)"
    echo "  -cur, --concurrency [NUMBER]            concurrency level (10 = default)"
    echo "  -dur, --duration [DURATION]             duration (1m = default)"
    echo "  -pg, --percent-get [PERCENT]            % get requests (100% = default)"
    echo "  -pp, --percent-put [PERCENT]            % put requests (0% = default)"
}

echo_if_verbose() {
    if [ "1" -eq "${VERBOSE:-0}" ]; then
        echo "${1:-}"
    fi
    return 0
}

echo_to_stderr() {
    echo "${1:-}" >&2
    return 0
}

#
# parse command line arguments
#
VERBOSE=0
NUMBER_FRUIT=50
PERCENT_GET=100
PERCENT_PUT=0
CONCURRENCY=10
DURATION=1m
# k6 runs in a docker container and talks to the service
# being tested on the docker0 bridge
SERVICE=http://$(ifconfig docker0 | grep 'inet addr:' | sed -e 's/.*addr://g' | sed -e 's/ .*$//g'):8445
# version 0.16.0 is the last known version that works correctly
K6_DOCKER_IMAGE=loadimpact/k6:0.16.0

while true
do
    case "${1,,}" in
        -h|--help)
            shift
            usage
            exit 0
            ;;
        -v|--verbose)
            shift
            VERBOSE=1
            ;;
        -k6di|--k6-docker-image)
            shift
            K6_DOCKER_IMAGE=$1
            shift
            ;;
        -nf|--number-fruit)
            shift
            NUMBER_FRUIT=$1
            shift
            ;;
        -cur|--concurrency)
            shift
            CONCURRENCY=$1
            shift
            ;;
        -dur|--duration)
            shift
            DURATION=$1
            shift
            ;;
        -pg|--percent-get)
            shift
            PERCENT_GET=$1
            shift
            ;;
        -pp|--percent-put)
            shift
            PERCENT_PUT=$1
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ $# != 0 ]; then
    usage
    exit 1
fi

if [ $((PERCENT_GET + PERCENT_PUT)) != 100 ]; then
    echo_to_stderr "operation percentages must total to 100" >&2
    exit 1
fi

echo_if_verbose "config: number of fruit = $NUMBER_FRUIT"
echo_if_verbose "config: % get = $PERCENT_GET"
echo_if_verbose "config: % put = $PERCENT_PUT"
echo_if_verbose "config: concurrency = $CONCURRENCY"
echo_if_verbose "config: duration = $DURATION"
echo_if_verbose "config: service = $SERVICE"
echo_if_verbose "config: K6 docker image = $K6_DOCKER_IMAGE"

#
# initialize the database with a bunch of fruit
#
FRUIT_IDS_DOT_JS_DIR=$(mktemp -d 2> /dev/null || mktemp -d -t DAS)
FRUIT_IDS_DOT_JS="$FRUIT_IDS_DOT_JS_DIR/fruit_ids.js"
if ! "$SCRIPT_DIR_NAME/create_fruit.py" "--number-fruit=$NUMBER_FRUIT" "--service=$SERVICE" > "$FRUIT_IDS_DOT_JS"; then
    echo_to_stderr "Error creating fruit"
    exit 1
fi
echo_if_verbose "config: fruit IDs = $FRUIT_IDS_DOT_JS"

#
# config k6output
#
K6_OUTPUT_DIR=$(mktemp -d 2> /dev/null || mktemp -d -t DAS)
K6_OUTPUT_DOT_JSON="k6-output.json"
echo_if_verbose "config: k6 output in directory = $K6_OUTPUT_DIR"

#
# finally we get to do run the load test
#
docker pull "$K6_DOCKER_IMAGE"
docker \
    run \
    -v "$K6_OUTPUT_DIR":/k6output \
    -v "$FRUIT_IDS_DOT_JS_DIR":/k6imports \
    -e "SERVICE=$SERVICE" \
    -e "PERCENT_GET=$PERCENT_GET" \
    -e "PERCENT_PUT=$PERCENT_PUT" \
    -i \
    "$K6_DOCKER_IMAGE" run --vus "$CONCURRENCY" --duration "$DURATION" --out json=/k6output/k6-output.json - < "$SCRIPT_DIR_NAME/k6script.js"

#
# translate k6 json output to something that can be used
# as input to analyze_restful_api_load_test_results
#
# :TODO: gotta be a more efficient way to do this:-(
#
jq -c 'select(.metric == "http_req_duration" and .type == "Point" and .data.tags.method == "GET" and .data.tags.status == "200") | [.data.time, "GET", 1, .data.tags.vu, .data.value] | @tsv' \
    < "$K6_OUTPUT_DIR/$K6_OUTPUT_DOT_JSON" \
    > "$K6_OUTPUT_DIR/get_success.tsv"

jq -c 'select(.metric == "http_req_duration" and .type == "Point" and .data.tags.method == "GET" and .data.tags.status != "200") | [.data.time, "GET", 0, .data.tags.vu, .data.value] | @tsv' \
    < "$K6_OUTPUT_DIR/$K6_OUTPUT_DOT_JSON" \
    > "$K6_OUTPUT_DIR/get_failure.tsv"

jq -c 'select(.metric == "http_req_duration" and .type == "Point" and .data.tags.method == "PUT" and .data.tags.status == "200") | [.data.time, "PUT", 1, .data.tags.vu, .data.value] | @tsv' \
    < "$K6_OUTPUT_DIR/$K6_OUTPUT_DOT_JSON" \
    > "$K6_OUTPUT_DIR/put_success.tsv"

jq -c 'select(.metric == "http_req_duration" and .type == "Point" and .data.tags.method == "PUT" and .data.tags.status != "200") | [.data.time, "PUT", 0, .data.tags.vu, .data.value] | @tsv' \
    < "$K6_OUTPUT_DIR/$K6_OUTPUT_DOT_JSON" \
    > "$K6_OUTPUT_DIR/put_failure.tsv"

K6_OUTPUT_DOT_TSV=$K6_OUTPUT_DIR/k6-output.tsv

find "$K6_OUTPUT_DIR" -regex '.*/\(put\|get\|post\|delete\)_\(failure\|success\)\.tsv' |
    sed -e 's/"//g' |
    sed -e 's/\\t/\t/g' \
    > "$K6_OUTPUT_DOT_TSV"

exit 0
