./bin/bzrflag --world=maps/four_ls.bzw --friendly-fire --red-port=50100 --green-port=50101 --purple-port=50102 --blue-port=50103 $@ &
sleep 2
echo "Connect on ports 50100 to 50103"
python bzagents/agent_rh_jr.py localhost 50100 &
python bzagents/agent_rh_jr.py localhost 50101 &
python bzagents/really_dumb_agent.py localhost 50102 &
python bzagents/agent0.py localhost 50103 &

