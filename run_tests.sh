#!/bin/bash

FILENAME="COMP445_TA4_W26.pdf"
SEGMENT=512
TIMEOUT=5.0
PROJECT_DIR=$(pwd)

run_scenario() {
    SCENARIO=$1
    NETEM_CMD=$2

    echo "--- $SCENARIO ---"

    # clear old netem rules
    ip netns exec ns_server tc qdisc del dev veth_server root 2>/dev/null

    # apply the netem rule
    ip netns exec ns_server tc qdisc add dev veth_server root netem $NETEM_CMD

    # start server in ns_server
    ip netns exec ns_server python3 $PROJECT_DIR/main.py serve --port 5005 &
    SERVER_PID=$!
    sleep 1

    # start client in ns_client
    ip netns exec ns_client python3 $PROJECT_DIR/main.py get \
        --host 10.0.0.1 \
        --port 5005 \
        --filename $FILENAME \
        --segment-size $SEGMENT \
        --timeout $TIMEOUT

    kill $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    sleep 1
}

# scenario 1: delay
run_scenario "DELAY 150ms + 20ms jitter" "delay 150ms 20ms"

# scenario 2: loss
run_scenario "LOSS 10%" "loss 10%"

echo "done."