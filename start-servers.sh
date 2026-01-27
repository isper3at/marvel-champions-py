#!/bin/bash

###############################################################################
# Marvel Champions - Server Startup Script
# 
# This script starts both the backend (Flask) and frontend (React) servers
# for the Marvel Champions game.
#
# Usage: ./start-servers.sh [options]
#
# Options:
#   --backend-only    Start only the backend server
#   --frontend-only   Start only the frontend server
#   --help            Show this help message
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Configuration
BACKEND_PORT=5000
FRONTEND_PORT=3000
MONGODB_PORT=27017

# Functions
print_header() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  Marvel Champions - Server Startup"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
}

print_info() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

check_port() {
    local port=$1
    local service=$2
    if nc -z localhost "$port" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

start_backend() {
    echo ""
    echo -e "${BLUE}Starting Backend Server...${NC}"
    
    # Check if backend port is in use
    if check_port $BACKEND_PORT "Backend"; then
        print_warning "Backend port $BACKEND_PORT is already in use"
        return 1
    fi
    
    # Determine Python executable
    local python_exe="python3"
    if [ -f "$SCRIPT_DIR/venv/bin/python3" ]; then
        python_exe="$SCRIPT_DIR/venv/bin/python3"
    fi
    
    # Check if Python is available
    if ! command -v "$python_exe" &> /dev/null && ! [ -f "$python_exe" ]; then
        print_error "Python is not available"
        return 1
    fi
    
    # Check if backend directory exists
    if [ ! -f "$SCRIPT_DIR/src/app.py" ]; then
        print_error "Backend app file not found at src/app.py"
        return 1
    fi
    
    # Start backend in background
    cd "$SCRIPT_DIR"
    "$python_exe" src/app.py > logs/backend.log 2>&1 &
    local backend_pid=$!
    
    # Wait for backend to start
    sleep 2
    
    if check_port $BACKEND_PORT "Backend"; then
        print_info "Backend server started on http://localhost:$BACKEND_PORT (PID: $backend_pid)"
        echo $backend_pid > .backend.pid
        return 0
    else
        print_error "Backend server failed to start. Check logs/backend.log"
        return 1
    fi
}

start_frontend() {
    echo ""
    echo -e "${BLUE}Starting Frontend Server...${NC}"
    
    # Check if frontend port is in use
    if check_port $FRONTEND_PORT "Frontend"; then
        print_warning "Frontend port $FRONTEND_PORT is already in use"
        return 1
    fi
    
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        return 1
    fi
    
    # Check if frontend directory exists
    if [ ! -d "$SCRIPT_DIR/ui" ]; then
        print_error "Frontend directory not found at ui/"
        return 1
    fi
    
    # Check if dependencies are installed
    if [ ! -d "$SCRIPT_DIR/ui/node_modules" ]; then
        print_warning "Frontend dependencies not installed. Installing now..."
        cd "$SCRIPT_DIR/ui"
        npm install || {
            print_error "Failed to install frontend dependencies"
            return 1
        }
    fi
    
    # Start frontend in background
    cd "$SCRIPT_DIR/ui"
    REACT_APP_API_URL="http://localhost:$BACKEND_PORT" npm start > ../logs/frontend.log 2>&1 &
    local frontend_pid=$!
    
    # Wait for frontend to start
    sleep 3
    
    if check_port $FRONTEND_PORT "Frontend"; then
        print_info "Frontend server started on http://localhost:$FRONTEND_PORT (PID: $frontend_pid)"
        echo $frontend_pid > ../.frontend.pid
        return 0
    else
        print_warning "Frontend server may be starting. Check logs/frontend.log"
        echo $frontend_pid > ../.frontend.pid
        return 0
    fi
}

check_mongodb() {
    echo ""
    echo -e "${BLUE}Checking MongoDB...${NC}"
    
    if check_port $MONGODB_PORT "MongoDB"; then
        print_info "MongoDB is running on localhost:$MONGODB_PORT"
        return 0
    else
        print_warning "MongoDB is not running on localhost:$MONGODB_PORT"
        print_warning "If MongoDB is not running locally, please start it before using the application"
        return 1
    fi
}

stop_servers() {
    echo ""
    echo -e "${BLUE}Stopping servers...${NC}"
    
    if [ -f "$SCRIPT_DIR/.backend.pid" ]; then
        local backend_pid=$(cat "$SCRIPT_DIR/.backend.pid")
        if kill $backend_pid 2>/dev/null; then
            print_info "Backend server stopped"
        fi
        rm "$SCRIPT_DIR/.backend.pid"
    fi
    
    if [ -f "$SCRIPT_DIR/.frontend.pid" ]; then
        local frontend_pid=$(cat "$SCRIPT_DIR/.frontend.pid")
        if kill $frontend_pid 2>/dev/null; then
            print_info "Frontend server stopped"
        fi
        rm "$SCRIPT_DIR/.frontend.pid"
    fi
}

show_help() {
    cat << EOF
Marvel Champions - Server Startup Script

Usage: ./start-servers.sh [options]

Options:
  --backend-only    Start only the backend server
  --frontend-only   Start only the frontend server
  --stop            Stop both servers
  --help            Show this help message

Examples:
  ./start-servers.sh                 # Start both servers
  ./start-servers.sh --backend-only  # Start only the backend
  ./start-servers.sh --frontend-only # Start only the frontend
  ./start-servers.sh --stop          # Stop both servers

After starting:
  Backend:  http://localhost:$BACKEND_PORT
  Frontend: http://localhost:$FRONTEND_PORT
  API Docs: http://localhost:$BACKEND_PORT/api/docs

Log files:
  Backend:  logs/backend.log
  Frontend: logs/frontend.log

EOF
}

# Main execution
main() {
    local start_backend=true
    local start_frontend=true
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --backend-only)
                start_frontend=false
                shift
                ;;
            --frontend-only)
                start_backend=false
                shift
                ;;
            --stop)
                stop_servers
                exit 0
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    print_header
    
    # Create logs directory if it doesn't exist
    mkdir -p "$SCRIPT_DIR/logs"
    
    # Check MongoDB
    check_mongodb || true
    
    # Start servers
    backend_success=true
    frontend_success=true
    
    if [ "$start_backend" = true ]; then
        start_backend || backend_success=false
    fi
    
    if [ "$start_frontend" = true ]; then
        start_frontend || frontend_success=false
    fi
    
    # Summary
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}  Startup Summary"
    echo -e "${BLUE}╚════════════════════════════════════════════════════╝${NC}"
    
    if [ "$start_backend" = true ]; then
        if [ "$backend_success" = true ]; then
            print_info "Backend:  http://localhost:$BACKEND_PORT"
        else
            print_error "Backend failed to start"
        fi
    fi
    
    if [ "$start_frontend" = true ]; then
        if [ "$frontend_success" = true ]; then
            print_info "Frontend: http://localhost:$FRONTEND_PORT"
        else
            print_error "Frontend failed to start"
        fi
    fi
    
    if [ "$backend_success" = true ] && [ "$frontend_success" = true ]; then
        echo ""
        print_info "All servers started successfully!"
        echo ""
        echo "To stop the servers, run:"
        echo "  ./start-servers.sh --stop"
        echo ""
    else
        echo ""
        print_error "Some servers failed to start. Check the log files."
        exit 1
    fi
}

# Run main function
main "$@"
