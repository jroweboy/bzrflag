let "number=$RANDOM % 10000 + 50000"
let "tanks=2"

./bin/bzrflag --red-tanks=${tanks} --green-tanks=${tanks} --blue-tanks=${tanks} --purple-tanks=${tanks}  --friendly-fire --red-port=${number} --green-port=50003 --default-true-positive=.97 --default-true-negative=.9 --occgrid-width=100 --no-report-obstacles $@ &
sleep 3
echo "Connect on ports ${number} or 50003"
python bzagents/agent_occgrid.py localhost ${number} &
#python bzagents/agent0.py localhost 50103 &
