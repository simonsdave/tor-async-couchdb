#!/usr/bin/env bash

#
# this shell script is used to run the load generator
#
# exit codes
#
#   0   always
#

set -e
set -x

SCRIPT_DIR_NAME="$( cd "$( dirname "$0" )" && pwd )"

TEMP_DIR=$(mktemp -d 2> /dev/null || mktemp -d -t DAS)
"$PWD/create_fruit.py" > "$TEMP_DIR/fruit_ids.js"

docker pull loadimpact/k6

DOCKER0IP=$(ifconfig docker0 | grep 'inet addr:' | sed -e 's/.*addr://g' | sed -e 's/ .*$//g')

docker \
    run \
    -v "$PWD":/k6output \
    -v "$TEMP_DIR":/k6imports \
    -e SERVICE_IP=$DOCKER0IP \
    -e SERVICE_PORT=8445 \
    -e PERCENT_GET=50 \
    -e PERCENT_PUT=50 \
    -i \
    loadimpact/k6 run --out json=/k6output/foo.json - <k6script.js
set +x

exit 0
