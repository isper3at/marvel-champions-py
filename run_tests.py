#!/usr/bin/env python3
"""
Python test runner script.
Provides more flexibility than shell script.

Usage:
    python3 run_tests.py              # Run all tests
    python3 run_tests.py -k entities  # Run only entity tests
    python3 run_tests.py --verbose    # Verbose output
"""

import sys
import subprocess
from pymongo import MongoClient


def check_mongodb():
    """Check if MongoDB is running"""
    try:
        client = MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=2000)
        client.server_info()
        print("✅ MongoDB is running")
        return True
    except Exception:
        print("❌ MongoDB is not running!")
        print()
        print("Please start MongoDB:")
        print("  macOS:  brew services start mongodb-community")
        print("  Linux:  sudo systemctl start mongodb")
        print()
        return False


def check_pytest():
    """Check if pytest is installed"""
    try:
        subprocess.run(
            ['python3', '-m', 'pytest', '--version'],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        print("❌ pytest not installed!")
        print()
        print("Installing test dependencies...")
        subprocess.run(['pip3', 'install', '-r', 'requirements-dev.txt'], check=True)
        return True


def run_tests(args=None):
    """Run pytest with given arguments"""
    cmd = ['python3', '-m', 'pytest', 'tests/', '-v']
    
    if args:
        cmd.extend(args)
    
    # Add coverage by default if no specific args
    if not args or '--no-cov' not in args:
        cmd.extend(['--cov=.', '--cov-report=term-missing', '--cov-report=html'])
    
    print("Running tests...")
    print()
    
    result = subprocess.run(cmd)
    
    print()
    print("=" * 60)
    print("Test Results")
    print("=" * 60)
    print()
    
    if result.returncode == 0:
        print("✅ All tests passed!")
        print()
        print("Coverage report: htmlcov/index.html")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


def main():
    """Main test runner"""
    print("=" * 60)
    print("Marvel Champions Test Suite")
    print("=" * 60)
    print()
    
    # Check prerequisites
    if not check_mongodb():
        sys.exit(1)
    
    check_pytest()
    print()
    
    # Run tests with any command line args
    args = sys.argv[1:] if len(sys.argv) > 1 else None
    run_tests(args)


if __name__ == '__main__':
    main()
