"""
Test cases for RapidCaptcha error handling and exception scenarios
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
import responses

from rapidcaptcha import (
    RapidCaptchaClient, CaptchaResult, TaskStatus,
    RapidCaptchaError, APIKeyError, ValidationError, 
    TaskNotFoundError, RateLimitError, TimeoutError
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and properties"""
    
    def test_rapidcaptcha_error_base(self):
        """Test RapidCaptchaError as base exception"""
        error = RapidCaptchaError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)
    
    def test_api_key_error_inheritance(self):
        """Test APIKeyError inherits from RapidCaptchaError"""
        error = APIKeyError("Invalid API key")
        assert isinstance(error, RapidCaptchaError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid API key"
    
    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from RapidCaptchaError"""
        error = ValidationError("Invalid parameters")
        assert isinstance(error, RapidCaptchaError)
        assert isinstance(error, Exception)
        assert str(error) == "Invalid parameters"
    
    def test_task_not_found_error_inheritance(self):
        """Test TaskNotFoundError inherits from RapidCaptchaError"""
        error = TaskNotFoundError("Task not found")
        assert isinstance(error, RapidCaptchaError)
        assert isinstance(error, Exception)
        assert str(error) == "Task not found"
    
    def test_rate_limit_error_inheritance(self):
        """Test RateLimitError inherits from RapidCaptchaError"""
        error = RateLimitError("Rate limit exceeded")
        assert isinstance(error, RapidCaptchaError)
        assert isinstance(error, Exception)
        assert str(error) == "Rate limit exceeded"
    
    def test_timeout_error_inheritance(self):
        """Test TimeoutError inherits from RapidCaptchaError"""
        error = TimeoutError("Operation timed out")
        assert isinstance(error, RapidCaptchaError)
        assert isinstance(error, Exception)
        assert str(error) == "Operation timed out"


class TestAPIKeyValidation:
    """Test API key validation errors"""
    
    def test_api_key_empty_string(self):
        """Test API key validation with empty string"""
        with pytest.raises(APIKeyError, match="Invalid API key format"):
            RapidCaptchaClient("")
    
    def test_api_key_none(self):
        """Test API key validation with None"""
        with pytest.raises(APIKeyError, match="Invalid API key format"):
            RapidCaptchaClient(None)
    
    def test_api_key_wrong_format(self):
        """Test API key validation with wrong format"""
        invalid_keys = [
            "invalid-key",
            "rapidcaptcha-key",  # lowercase
            "RapidCaptcha-key",  # wrong case
            "Rapidcaptcha",      # no dash
            "key-Rapidcaptcha",  # wrong order
            "123456789",         # numbers only
            "Rapidcaptcha-",     # empty suffix
        ]
        
        for key in invalid_keys:
            with pytest.raises(APIKeyError, match="Invalid API key format"):
                RapidCaptchaClient(key)
    
    def test_api_key_valid_format(self):
        """Test API key validation with valid format"""
        valid_keys = [
            "Rapidcaptcha-test",
            "Rapidcaptcha-abc123",
            "Rapidcaptcha-ABC123DEF456",
            "Rapidcaptcha-very-long-key-with-dashes-123",
        ]
        
        for key in valid_keys:
            # Should not raise an exception
            client = RapidCaptchaClient(key)
            assert client.api_key == key


class TestURLValidation:
    """Test URL validation errors"""
    
    def test_url_validation_empty_string(self):
        """Test URL validation with empty string"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url("")
    
    def test_url_validation_none(self):
        """Test URL validation with None"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url(None)
    
    def test_url_validation_non_string(self):
        """Test URL validation with non-string"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url(123)
        
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url([])
    
    def test_url_validation_invalid_schemes(self):
        """Test URL validation with invalid schemes"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        invalid_urls = [
            "example.com",
            "www.example.com", 
            "ftp://example.com",
            "file:///path/to/file",
            "mailto:test@example.com",
            "javascript:alert('xss')",
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError, match="must start with http"):
                client._validate_url(url)
    
    def test_url_validation_valid_schemes(self):
        """Test URL validation with valid schemes"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "https://www.example.com",
            "https://sub.example.com/path?query=1",
            "http://localhost:8080",
            "https://127.0.0.1:3000/test",
        ]
        
        for url in valid_urls:
            # Should not raise an exception
            client._validate_url(url)


class TestHTTPErrorHandling:
    """Test HTTP error response handling"""
    
    @responses.activate
    def test_handle_401_unauthorized(self):
        """Test handling 401 Unauthorized response"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            json={"error": "Invalid API key"},
            status=401
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(APIKeyError, match="Invalid API key"):
            client.health_check()
    
    @responses.activate
    def test_handle_404_not_found(self):
        """Test handling 404 Not Found response"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/non-existent-task",
            json={"error": "Task not found or expired"},
            status=404
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(TaskNotFoundError, match="Task not found"):
            client.get_result("non-existent-task")
    
    @responses.activate
    def test_handle_429_rate_limit(self):
        """Test handling 429 Rate Limit response"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"error": "Rate limit exceeded", "retry_after": 60},
            status=429
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client.submit_turnstile("https://example.com", auto_detect=True)
    
    @responses.activate
    def test_handle_400_bad_request_with_message(self):
        """Test handling 400 Bad Request with error message"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"message": "Invalid URL format provided"},
            status=400
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(ValidationError, match="Invalid URL format provided"):
            client.submit_turnstile("https://example.com", auto_detect=True)
    
    @responses.activate
    def test_handle_400_bad_request_without_message(self):
        """Test handling 400 Bad Request without error message"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"error": "Bad request"},
            status=400
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(ValidationError, match="Bad request"):
            client.submit_turnstile("https://example.com", auto_detect=True)
    
    @responses.activate
    def test_handle_500_server_error(self):
        """Test handling 500 Internal Server Error"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"message": "Internal server error"},
            status=500
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RapidCaptchaError, match="Internal server error"):
            client.submit_turnstile("https://example.com", auto_detect=True)
    
    @responses.activate
    def test_handle_unknown_error_status(self):
        """Test handling unknown error status"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"message": "Service temporarily unavailable"},
            status=503
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RapidCaptchaError, match="Service temporarily unavailable"):
            client.submit_turnstile("https://example.com", auto_detect=True)


class TestJSONErrorHandling:
    """Test JSON parsing error handling"""
    
    @responses.activate
    def test_handle_invalid_json_response(self):
        """Test handling invalid JSON response"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            body="Invalid JSON response <html>Error page</html>",
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RapidCaptchaError, match="Invalid JSON response"):
            client.health_check()
    
    @responses.activate
    def test_handle_empty_response(self):
        """Test handling empty response"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            body="",
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RapidCaptchaError, match="Invalid JSON response"):
            client.health_check()
    
    @responses.activate
    def test_handle_error_response_invalid_json(self):
        """Test handling error response with invalid JSON"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            body="Internal Server Error",
            status=500
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RapidCaptchaError, match="HTTP 500: Internal Server Error"):
            client.submit_turnstile("https://example.com", auto_detect=True)


class TestTimeoutErrors:
    """Test timeout error scenarios"""
    
    @responses.activate
    def test_wait_for_result_timeout(self):
        """Test wait_for_result timeout"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/timeout-task",
            json={
                "task_id": "timeout-task",
                "status": "pending"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key", timeout=1)  # 1 second timeout
        
        with pytest.raises(TimeoutError, match="did not complete within 1 seconds"):
            client.wait_for_result("timeout-task", poll_interval=0.1)
    
    @responses.activate
    def test_solve_turnstile_timeout(self):
        """Test solve_turnstile timeout"""
        # Submit response
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"task_id": "timeout-solve-task"},
            status=202
        )
        
        # Always pending response
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/timeout-solve-task",
            json={
                "task_id": "timeout-solve-task",
                "status": "pending"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key", timeout=1)  # 1 second timeout
        
        with pytest.raises(TimeoutError, match="did not complete within 1 seconds"):
            client.solve_turnstile("https://example.com", auto_detect=True, poll_interval=0.1)


class TestValidationErrors:
    """Test parameter validation errors"""
    
    def test_submit_turnstile_no_sitekey_no_autodetect(self):
        """Test submit_turnstile with no sitekey and auto_detect=False"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Either provide sitekey or enable auto_detect"):
            client.submit_turnstile("https://example.com", auto_detect=False)
    
    def test_submit_recaptcha_no_sitekey_no_autodetect(self):
        """Test submit_recaptcha with no sitekey and auto_detect=False"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Either provide sitekey or enable auto_detect"):
            client.submit_recaptcha("https://example.com", auto_detect=False)
    
    def test_get_result_empty_task_id(self):
        """Test get_result with empty task ID"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            client.get_result("")
    
    def test_get_result_none_task_id(self):
        """Test get_result with None task ID"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            client.get_result(None)


class TestLibraryImportErrors:
    """Test behavior when required libraries are not available"""
    
    def test_sync_operations_without_requests(self):
        """Test sync operations when requests library is not available"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_REQUESTS', False):
            # Test various sync methods
            with pytest.raises(ImportError, match="requests library is required"):
                client.health_check()
            
            with pytest.raises(ImportError, match="requests library is required"):
                client.submit_turnstile("https://example.com", auto_detect=True)
            
            with pytest.raises(ImportError, match="requests library is required"):
                client.submit_recaptcha("https://example.com", auto_detect=True)
            
            with pytest.raises(ImportError, match="requests library is required"):
                client.get_result("test-task")
    
    @pytest.mark.asyncio
    async def test_async_operations_without_aiohttp(self):
        """Test async operations when aiohttp library is not available"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_AIOHTTP', False):
            # Test various async methods
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.health_check_async()
            
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.submit_turnstile_async("https://example.com", auto_detect=True)
            
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.submit_recaptcha_async("https://example.com", auto_detect=True)
            
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.get_result_async("test-task")


class TestErrorResultParsing:
    """Test parsing of error results from API"""
    
    @responses.activate
    def test_parse_detailed_error_result(self):
        """Test parsing detailed error result with multiple fields"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/detailed-error-task",
            json={
                "task_id": "detailed-error-task",
                "status": "error",
                "result": {
                    "reason": "Multiple sitekey validation failures",
                    "errors": [
                        "Primary sitekey not found on page",
                        "Fallback sitekey authentication failed",
                        "Page load timeout exceeded"
                    ],
                    "sitekeys_tried": [
                        "0x4AAAAAAABkMYinukE8nzKd",
                        "0x4AAAAAAABkMYinukE8nzKe",
                        "0x4AAAAAAABkMYinukE8nzKf"
                    ],
                    "elapsed_time_seconds": 45.7
                },
                "completed_at": "2024-01-15T10:35:22Z"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.get_result("detailed-error-task")
        
        assert result.is_error
        assert result.task_id == "detailed-error-task"
        assert result.reason == "Multiple sitekey validation failures"
        assert len(result.errors) == 3
        assert "Primary sitekey not found on page" in result.errors
        assert len(result.sitekeys_tried) == 3
        assert "0x4AAAAAAABkMYinukE8nzKd" in result.sitekeys_tried
        assert result.elapsed_time_seconds == 45.7
        assert result.completed_at == "2024-01-15T10:35:22Z"
    
    @responses.activate
    def test_parse_minimal_error_result(self):
        """Test parsing minimal error result with only basic fields"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/minimal-error-task",
            json={
                "task_id": "minimal-error-task",
                "status": "error",
                "result": {
                    "reason": "Simple error"
                }
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.get_result("minimal-error-task")
        
        assert result.is_error
        assert result.task_id == "minimal-error-task"
        assert result.reason == "Simple error"