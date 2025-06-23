#!/usr/bin/env python3
"""
Test runner script for the Lawrence project.
This script runs the test suite with proper configuration and reporting.
"""

import sys
import subprocess
import os

def run_tests():
    """Run the test suite with pytest."""
    print("🧪 Running Lawrence Test Suite")
    print("=" * 50)
    
    # Set up environment
    os.environ['PYTHONPATH'] = os.getcwd()
    
    # Run tests with coverage
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--tb=short',
        '--cov=src',
        '--cov-report=term-missing',
        '--cov-report=html:htmlcov',
        '--cov-report=xml',
        '--color=yes'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return 1

def run_unit_tests():
    """Run only unit tests."""
    print("🧪 Running Unit Tests Only")
    print("=" * 30)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/unit/',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1

def run_integration_tests():
    """Run only integration tests."""
    print("🧪 Running Integration Tests Only")
    print("=" * 35)
    
    cmd = [
        sys.executable, '-m', 'pytest',
        'tests/integration/',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Tests interrupted by user")
        return 1

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "unit":
            exit_code = run_unit_tests()
        elif sys.argv[1] == "integration":
            exit_code = run_integration_tests()
        else:
            print("Usage: python run_tests.py [unit|integration]")
            print("  unit: Run only unit tests")
            print("  integration: Run only integration tests")
            print("  (no args): Run all tests with coverage")
            exit_code = 1
    else:
        exit_code = run_tests()
    
    sys.exit(exit_code) 