# run_tests.py

import subprocess
import sys
import argparse
from datetime import datetime


def run_tests(args):
    """Run tests with specified options"""
    
    pytest_args = ["pytest", "test_graphql_api.py"]
    
    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")
    
    # Add specific test
    if args.test:
        pytest_args.extend(["-k", args.test])
    
    # Add markers
    if args.marker:
        pytest_args.extend(["-m", args.marker])
    
    # Add coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=.",
            "--cov-report=html",
            f"--cov-report=term-missing:{args.coverage_threshold}"
        ])
    
    # Add parallel execution
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # Add HTML report
    if args.html_report:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pytest_args.extend([
            "--html=reports/test_report_{}.html".format(timestamp),
            "--self-contained-html"
        ])
    
    # Add JUnit XML report (useful for CI/CD)
    if args.junit_xml:
        pytest_args.extend(["--junit-xml=reports/junit.xml"])
    
    # Run the tests
    result = subprocess.run(pytest_args)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run GraphQL API tests")
    
    parser.add_argument("-v", "--verbose", action="store_true", 
                       help="Verbose output")
    parser.add_argument("-t", "--test", type=str, 
                       help="Run specific test by name pattern")
    parser.add_argument("-m", "--marker", type=str, 
                       help="Run tests with specific marker")
    parser.add_argument("-c", "--coverage", action="store_true", 
                       help="Run with coverage report")
    parser.add_argument("--coverage-threshold", type=int, default=80,
                       help="Coverage threshold percentage")
    parser.add_argument("-p", "--parallel", type=int, 
                       help="Run tests in parallel with N workers")
    parser.add_argument("--html-report", action="store_true", 
                       help="Generate HTML test report")
    parser.add_argument("--junit-xml", action="store_true", 
                       help="Generate JUnit XML report")
    
    args = parser.parse_args()
    
    # Create reports directory if it doesn't exist
    import os
    os.makedirs("reports", exist_ok=True)
    
    # Run tests
    exit_code = run_tests(args)
    
    if exit_code == 0:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()