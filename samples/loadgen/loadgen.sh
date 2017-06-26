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
# k6 runs in a docker container and talks to the service
# being tested on the docker0 bridge
#
SERVICE=http://$(ifconfig docker0 | grep 'inet addr:' | sed -e 's/.*addr://g' | sed -e 's/ .*$//g'):8445

usage() {
    echo "usage: `basename $0` [OPTION...]"
    echo ""
    echo "  -h, --help                          this message"
    echo "  -v                                  verbose output"
    echo "  -nf, --number-fruit [NUMBER FRUIT]  number fruit (50 = default)"
    echo "  -pg, --percent-get [PERCENT]        % get requests (100% = default)"
    echo "  -pp, --percent-put [PERCENT]        % put requests (0% = default)"
}

#
# parse command line arguments
#
VERBOSE=0
NUMBER_FRUIT=50
PERCENT_GET=100
PERCENT_PUT=0

while true
do
    OPTION=`echo ${1:-} | awk '{print tolower($0)}'`
    case "$OPTION" in
        -h|--help)
            shift
            usage
            exit 0
            ;;
        -v)
            shift
            VERBOSE=1
            ;;
        -nf|--number-fruit)
            shift
            NUMBER_FRUIT=$1
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

if [ $(($PERCENT_GET + $PERCENT_PUT)) != 100 ]; then
    echo "operation percentages must total to 100" >&2
    exit 1
fi

#
# initialize the database with a bunch of fruit
#
TEMP_DIR=$(mktemp -d 2> /dev/null || mktemp -d -t DAS)
"$SCRIPT_DIR_NAME/create_fruit.py" --number-fruit=$NUMBER_FRUIT --service=$SERVICE > "$TEMP_DIR/fruit_ids.js"

#
# always use latest version of k6
#
docker pull loadimpact/k6

#
# finally we get to do run the load test
#
docker \
    run \
    -v "$PWD":/k6output \
    -v "$TEMP_DIR":/k6imports \
    -e SERVICE=$SERVICE \
    -e PERCENT_GET=$PERCENT_GET \
    -e PERCENT_PUT=$PERCENT_PUT \
    -i \
    loadimpact/k6 run --out json=/k6output/foo.json - < "$SCRIPT_DIR_NAME/k6script.js"

exit 0
