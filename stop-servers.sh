#!/bin/bash

# Marvel Champions - Simple Server Shutdown
# Calls shutdown endpoints on running servers and kills npm process

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Attempt graceful backend shutdown via HTTP endpoint
echo "Stopping backend server..."
curl -s -X POST http://localhost:5000/shutdown 2>/dev/null
sleep 1

# Kill npm/frontend process
echo "Stopping frontend server..."
if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
    frontend_pid=$(cat "$SCRIPT_DIR/.frontend.pid")
    if ps -p $frontend_pid > /dev/null 2>&1; then
        kill $frontend_pid 2>/dev/null || true
        sleep 1
    fi
    rm -f "$SCRIPT_DIR/.frontend.pid"
fi

# Force kill any remaining process on port 3000
echo "Ensuring port 3000 is released..."
if command -v lsof &> /dev/null; then
    remaining_pids=$(lsof -ti:3000 2>/dev/null || echo "")
    if [ ! -z "$remaining_pids" ]; then
        echo "Forcing kill of processes on port 3000..."
        for pid in $remaining_pids; do
            kill -9 $pid 2>/dev/null || true
        done
        sleep 1
    fi
fi

# Cleanup backend pid file
rm -f "$SCRIPT_DIR/.backend.pid"

echo "Servers stopped"
