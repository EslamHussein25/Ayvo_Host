#!/bin/bash

# Start Node.js server in background (uncomment if needed)
echo "Starting server..."
node server.js &

cd controllers
# Activate your virtual environment
source venv/bin/activate

# Start Python server in background
python3 simple_server.py &

cd ../view/html/

open http://127.0.0.1:5000/view/html/index.html
# Optional: Keep the script running so you can see all output
echo "Both servers are running. Press Ctrl+C to stop."
wait
