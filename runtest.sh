./bin/bzrflag --world=maps/twoteams2.bzw --red-port=50100 --green-port=50103 --default-true-positive=.97 --default-true-negative=.9 --occgrid-width=100 --no-report-obstacles $@ &
sleep 3
echo "Connect on ports 50100 to 50103"
python bzagents/agent_occgrid.py localhost 50100 &
#python bzagents/agent0.py localhost 50103 &

