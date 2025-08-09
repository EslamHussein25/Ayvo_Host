#!/bin/bash

echo "stop servers..."

# Find and kill the Python server (simple_server.py)
PY_PIDS=$(ps aux | grep '[s]imple_server.py' | awk '{print $2}')
if [ -n "$PY_PIDS" ]; then
    echo "Killing Python server(s) with PID(s): $PY_PIDS"
    kill $PY_PIDS
else
    echo "No running Python server (simple_server.py) found."
fi

# Find and kill the Node.js server (server.js)
NODE_PIDS=$(ps aux | grep '[n]ode server.js' | awk '{print $2}')
if [ -n "$NODE_PIDS" ]; then
    echo "Killing Node.js server(s) with PID(s): $NODE_PIDS"
    kill $NODE_PIDS
else
    echo "No running Node.js server (server.js) found."
fi

echo "Done."
