#!/bin/bash
# Test runner script

set -e

echo "=================================="
echo "Marvel Champions Test Suite"
echo "=================================="
echo ""

# Check if MongoDB is running
echo "Checking MongoDB connection..."
if ! mongosh --eval "db.version()" > /dev/null 2>&1; then
    echo "❌ MongoDB is not running!"
    echo ""
    echo "Please start MongoDB:"
    echo "  macOS:  brew services start mongodb-community"
    echo "  Linux:  sudo systemctl start mongodb"
    echo ""
    exit 1
fi
echo "✅ MongoDB is running"
echo ""

# Check if pytest is installed
if ! python3 -m pytest --version > /dev/null 2>&1; then
    echo "❌ pytest not installed!"
    echo ""
    echo "Installing test dependencies..."
    pip3 install -r requirements-dev.txt
    echo ""
fi

# Run tests
echo "Running tests..."
echo ""

# Run with coverage
python3 -m pytest tests/ -v --cov=. --cov-report=term-missing --cov-report=html

echo ""
echo "=================================="
echo "Test Results"
echo "=================================="
echo ""
echo "Coverage report generated in htmlcov/index.html"
echo ""
