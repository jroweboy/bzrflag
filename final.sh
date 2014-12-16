#!/bin/bash

let "number1=$RANDOM % 10000 + 50000"
let "number2=$RANDOM % 10000 + 50000"
let "number3=$RANDOM % 10000 + 50000"
let "number4=$RANDOM % 10000 + 50000"
let "tanks=10"

./bin/bzrflag \
    --world="./maps/simple.bzw" \
    --red-tanks=${tanks} \
    --friendly-fire \
    --red-port=${number4} \
    --default-posnoise=5 \
    --time-limit=240 \
    --respawn-time=240 \
    --max-shots=3 \
    --default-tanks=10 \
    $@ &

    # --green-tanks=${tanks} \
    # --blue-tanks=${tanks} \
    # --purple-tanks=${tanks} \
    # --green-port=${number2} \
    # --blue-port=${number3} \
    # --purple-port=${number4} \
# 
#    --no-report-obstacles
#    --occgrid-width=100 \
#    --default-true-positive=.97 \
#    --default-true-negative=.9 \
#

sleep 1
# echo "ports: red ${number}, green ${number2}, blue ${number3}, purple ${number4}"
# python bzagents/kalman_sitting_duck.py localhost ${number1} &
# python bzagents/kalman_nonconformist.py localhost ${number2} &
# python bzagents/kalman_straight_line.py localhost ${number3} &


python bzagents/full_agent.py localhost ${number4} &
#python -m pdb bzagents/kalman_agent_rh_jr.py localhost ${number4}
