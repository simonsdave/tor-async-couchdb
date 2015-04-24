#!/usr/bin/env bash

SCRIPT_DIR_NAME="$( cd "$( dirname "$0" )" && pwd )"

LOG_FILE_NAME=$(python -c "import os; f, _ = os.path.splitext(os.path.basename(\"$0\")); print f")
LOG_FILE_NAME="$SCRIPT_DIR_NAME/$LOG_FILE_NAME.tsv"

rm "$LOG_FILE_NAME" >& /dev/null

locust \
	--loglevel=INFO \
    --locustfile="$SCRIPT_DIR_NAME/locustfile.py" \
    --no-web \
    --num-request=1000 \
    --clients=25 \
    --hatch-rate=5 \
	--logfile="$LOG_FILE_NAME"

exit 0
