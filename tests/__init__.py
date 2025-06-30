"""
RapidCaptcha Python SDK Test Suite

This package contains comprehensive tests for the RapidCaptcha Python SDK including:
- Unit tests for synchronous operations
- Unit tests for asynchronous operations  
- Error handling and exception tests
- Integration tests (when API key is available)
- Performance and load tests

Test files:
- test_client.py: Synchronous client functionality tests
- test_async.py: Asynchronous client functionality tests
- test_errors.py: Error handling and exception tests

Usage:
    # Run all tests
    pytest tests/
    
    # Run specific test file
    pytest tests/test_client.py
    
    # Run with coverage
    pytest tests/ --cov=rapidcaptcha
    
    # Run async tests only
    pytest tests/test_async.py
    
    # Run with verbose output
    pytest tests/ -v
"""