let "number1=$RANDOM % 10000 + 50000"
let "number2=$RANDOM % 10000 + 50000"
let "number3=$RANDOM % 10000 + 50000"
let "number4=$RANDOM % 10000 + 50000"
let "tanks=1"

./bin/bzrflag \
    --world="./maps/simple.bzw" \
    --red-tanks=${tanks} \
    --green-tanks=${tanks} \
    --blue-tanks=${tanks} \
    --purple-tanks=${tanks} \
    --friendly-fire \
    --red-port=${number1} \
    --green-port=${number2} \
    --blue-port=${number3} \
    --purple-port=${number4} \
    --default-posnoise=5 \
    --occgrid-width=100 \
    --no-report-obstacles $@ &

#
#    --default-true-positive=.97 \
#    --default-true-negative=.9 \
#
sleep 3
echo "ports: red ${number}, green ${number2}, blue ${number3}, purple ${number4}"
python bzagents/kalman_sitting_duck.py localhost ${number1} &
python bzagents/kalman_nonconformist.py localhost ${number2} &
python bzagents/kalman_straight_line.py localhost ${number3} &
python bzagents/kalman_agent_rh_jr.py localhost ${number4} &
# python bzagents/agent_occgrid.py localhost ${number} &
#python bzagents/agent0.py localhost 50103 &