let "number=$RANDOM % 10000 + 50000"

./bin/bzrflag --red-tanks=1 --friendly-fire --red-port=${number} --green-port=50003 --default-true-positive=.97 --default-true-negative=.9 --occgrid-width=100 --no-report-obstacles $@ &
sleep 3
echo "Connect on ports ${number} or 50003"
python bzagents/agent_occgrid.py localhost ${number} &
#python bzagents/agent0.py localhost 50103 &
