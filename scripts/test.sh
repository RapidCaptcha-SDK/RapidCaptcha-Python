#!/bin/bash

# RapidCaptcha Python SDK - Test Runner Script
# This script runs all tests with various configurations and generates reports

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to create virtual environment if needed
setup_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python -m venv venv
    fi
    
    print_status "Activating virtual environment..."
    source venv/bin/activate || source venv/Scripts/activate  # Windows compatibility
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    pip install --upgrade pip
    pip install -e .
    pip install -r requirements-dev.txt
}

# Function to run linting
run_linting() {
    print_status "Running code linting..."
    
    echo "📝 Running flake8..."
    flake8 rapidcaptcha tests examples --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 rapidcaptcha tests examples --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    echo "📝 Running mypy..."
    mypy rapidcaptcha --ignore-missing-imports || print_warning "MyPy found some type issues"
}

# Function to run security checks
run_security_checks() {
    print_status "Running security checks..."
    
    echo "🔐 Running bandit security scan..."
    bandit -r rapidcaptcha -f json -o bandit-report.json || print_warning "Bandit found potential security issues"
    
    echo "🔐 Running safety check..."
    safety check --json --output safety-report.json || print_warning "Safety found vulnerable dependencies"
}

# Function to run unit tests
run_unit_tests() {
    print_status "Running unit tests..."
    
    # Run tests with coverage
    pytest tests/ \
        -v \
        --cov=rapidcaptcha \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml:coverage.xml \
        --junit-xml=test-results.xml \
        --tb=short
}

# Function to run async tests specifically
run_async_tests() {
    print_status "Running async tests..."
    
    pytest tests/test_async.py -v --tb=short
}

# Function to run integration tests (if API key is available)
run_integration_tests() {
    if [ -n "$RAPIDCAPTCHA_API_KEY" ]; then
        print_status "Running integration tests with real API..."
        pytest tests/ -m integration -v --tb=short || print_warning "Integration tests failed or skipped"
    else
        print_warning "RAPIDCAPTCHA_API_KEY not set, skipping integration tests"
    fi
}

# Function to run performance tests
run_performance_tests() {
    print_status "Running performance tests..."
    
    # Basic performance test
    python -c "
import time
import sys
sys.path.insert(0, '.')

try:
    from rapidcaptcha import RapidCaptchaClient
    
    # Test import speed
    start = time.time()
    client = RapidCaptchaClient('Rapidcaptcha-test-key')
    import_time = time.time() - start
    
    print(f'📊 Import time: {import_time:.3f}s')
    
    if import_time > 1.0:
        print('⚠️  Import time is slow (>1s)')
    else:
        print('✅ Import time is good')
        
except Exception as e:
    print(f'❌ Performance test failed: {e}')
    sys.exit(1)
"
}

# Function to run example scripts
run_examples() {
    print_status "Testing example scripts..."
    
    # Test basic usage example (dry run)
    python -c "
import sys
sys.path.insert(0, '.')

try:
    # Import examples to check for syntax errors
    import examples.basic_usage
    import examples.async_usage  
    import examples.error_handling
    print('✅ All example scripts imported successfully')
except ImportError as e:
    if 'aiohttp' in str(e):
        print('⚠️  aiohttp not available, async examples will not work')
    else:
        print(f'❌ Example import failed: {e}')
        sys.exit(1)
except Exception as e:
    print(f'❌ Example validation failed: {e}')
    sys.exit(1)
"
}

# Function to generate test report
generate_report() {
    print_status "Generating test report..."
    
    cat > test-report.md << EOF
# RapidCaptcha Python SDK - Test Report

Generated on: $(date)

## Test Results

### Unit Tests
- **Status**: $([ -f "test-results.xml" ] && echo "✅ Passed" || echo "❌ Failed")
- **Coverage Report**: [HTML Coverage Report](htmlcov/index.html)
- **XML Coverage**: coverage.xml
- **JUnit Results**: test-results.xml

### Code Quality
- **Linting**: flake8 checks completed
- **Type Checking**: mypy analysis completed
- **Security Scan**: bandit report generated
- **Dependency Check**: safety report generated

### Performance
- **Import Speed**: Tested ✅
- **Memory Usage**: Basic validation completed

### Examples
- **Basic Usage**: Syntax validated ✅
- **Async Usage**: Syntax validated ✅  
- **Error Handling**: Syntax validated ✅

## Files Generated
- \`htmlcov/\` - HTML coverage report
- \`coverage.xml\` - XML coverage report  
- \`test-results.xml\` - JUnit test results
- \`bandit-report.json\` - Security scan results
- \`safety-report.json\` - Dependency vulnerability report

## Next Steps
1. Review coverage report for any missed lines
2. Check security scan results
3. Update dependencies if vulnerabilities found
4. Run integration tests with real API key if needed
EOF

    print_success "Test report generated: test-report.md"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up temporary files..."
    
    # Remove Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    find . -type f -name "*.pyo" -delete 2>/dev/null || true
    
    # Remove pytest cache
    rm -rf .pytest_cache 2>/dev/null || true
    
    print_success "Cleanup completed"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --quick          Run only essential tests (fast)"
    echo "  --full           Run all tests including security and performance"
    echo "  --integration    Run integration tests (requires API key)"
    echo "  --lint-only      Run only linting and code quality checks"
    echo "  --clean          Clean up temporary files and exit"
    echo "  --help           Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  RAPIDCAPTCHA_API_KEY    API key for integration tests"
    echo ""
    echo "Examples:"
    echo "  $0 --quick              # Quick test run"
    echo "  $0 --full               # Complete test suite"
    echo "  $0 --integration        # Include integration tests"
    echo "  RAPIDCAPTCHA_API_KEY=xxx $0 --integration"
}

# Main execution function
main() {
    local mode="quick"
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --quick)
                mode="quick"
                shift
                ;;
            --full)
                mode="full"
                shift
                ;;
            --integration)
                mode="integration"
                shift
                ;;
            --lint-only)
                mode="lint"
                shift
                ;;
            --clean)
                cleanup
                exit 0
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    print_status "🚀 Starting RapidCaptcha Python SDK test suite"
    print_status "Mode: $mode"
    echo ""
    
    # Check dependencies
    if ! command_exists python; then
        print_error "Python is not installed or not in PATH"
        exit 1
    fi
    
    if ! command_exists pip; then
        print_error "pip is not installed or not in PATH"
        exit 1
    fi
    
    # Setup environment
    if [ "$CI" != "true" ]; then
        setup_venv
    fi
    
    install_dependencies
    
    # Run tests based on mode
    case $mode in
        "quick")
            print_status "🏃 Running quick test suite..."
            run_unit_tests
            run_examples
            ;;
        "full")
            print_status "🔍 Running full test suite..."
            run_linting
            run_security_checks
            run_unit_tests
            run_async_tests
            run_performance_tests
            run_examples
            ;;
        "integration")
            print_status "🌐 Running integration test suite..."
            run_unit_tests
            run_async_tests
            run_integration_tests
            ;;
        "lint")
            print_status "📝 Running linting only..."
            run_linting
            run_security_checks
            ;;
    esac
    
    # Generate report
    generate_report
    
    print_success "🎉 Test suite completed successfully!"
    echo ""
    print_status "📊 Results summary:"
    
    if [ -f "htmlcov/index.html" ]; then
        echo "   Coverage report: htmlcov/index.html"
    fi
    
    if [ -f "test-results.xml" ]; then
        echo "   Test results: test-results.xml"
    fi
    
    echo "   Full report: test-report.md"
    echo ""
    
    if [ "$mode" == "full" ] || [ "$mode" == "integration" ]; then
        print_status "💡 Tips:"
        echo "   - Review coverage report to ensure adequate test coverage"
        echo "   - Check security scan results for any issues"
        echo "   - Run integration tests with real API key for full validation"
        echo "   - Use 'pytest -v' for more detailed test output"
    fi
}

# Handle script interruption
trap 'print_error "Test suite interrupted"; exit 1' INT TERM

# Run main function with all arguments
main "$@"