"""
Test cases for RapidCaptcha client synchronous operations
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
import responses

from rapidcaptcha import (
    RapidCaptchaClient, CaptchaResult, TaskStatus,
    APIKeyError, ValidationError, TaskNotFoundError,
    RateLimitError, TimeoutError, solve_turnstile, solve_recaptcha
)


class TestRapidCaptchaClient:
    """Test RapidCaptchaClient class"""
    
    def test_init_valid_api_key(self):
        """Test client initialization with valid API key"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        assert client.api_key == "Rapidcaptcha-test-key"
        assert client.base_url == "https://rapidcaptcha.xyz"
        assert client.timeout == 300
        assert client.max_retries == 3
        assert client.retry_delay == 2.0
    
    def test_init_invalid_api_key(self):
        """Test client initialization with invalid API key"""
        with pytest.raises(APIKeyError, match="Invalid API key format"):
            RapidCaptchaClient("invalid-key")
        
        with pytest.raises(APIKeyError, match="Invalid API key format"):
            RapidCaptchaClient("")
        
        with pytest.raises(APIKeyError, match="Invalid API key format"):
            RapidCaptchaClient(None)
    
    def test_init_custom_parameters(self):
        """Test client initialization with custom parameters"""
        client = RapidCaptchaClient(
            api_key="Rapidcaptcha-test-key",
            base_url="https://custom.api.com",
            timeout=120,
            max_retries=5,
            retry_delay=1.5
        )
        assert client.base_url == "https://custom.api.com"
        assert client.timeout == 120
        assert client.max_retries == 5
        assert client.retry_delay == 1.5
    
    def test_validate_url(self):
        """Test URL validation"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        # Valid URLs
        client._validate_url("https://example.com")
        client._validate_url("http://test.com")
        
        # Invalid URLs
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url("")
        
        with pytest.raises(ValidationError, match="URL is required"):
            client._validate_url(None)
        
        with pytest.raises(ValidationError, match="must start with http"):
            client._validate_url("example.com")
        
        with pytest.raises(ValidationError, match="must start with http"):
            client._validate_url("ftp://example.com")


class TestHealthCheck:
    """Test health check functionality"""
    
    @responses.activate
    def test_health_check_success(self):
        """Test successful health check"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            json={"status": "ok", "message": "API is healthy"},
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.health_check()
        
        assert result["status"] == "ok"
        assert result["message"] == "API is healthy"
    
    @responses.activate
    def test_health_check_api_key_error(self):
        """Test health check with invalid API key"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            json={"error": "Invalid API key"},
            status=401
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(APIKeyError, match="Invalid API key"):
            client.health_check()


class TestTurnstileSubmission:
    """Test Turnstile task submission"""
    
    @responses.activate
    def test_submit_turnstile_auto_detect(self):
        """Test Turnstile submission with auto-detection"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"task_id": "test-task-123"},
            status=202
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        task_id = client.submit_turnstile(
            url="https://example.com",
            auto_detect=True
        )
        
        assert task_id == "test-task-123"
        
        # Check request payload
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["url"] == "https://example.com"
        assert payload["auto_detect"] is True
    
    @responses.activate
    def test_submit_turnstile_manual_sitekey(self):
        """Test Turnstile submission with manual sitekey"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"task_id": "test-task-456"},
            status=202
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        task_id = client.submit_turnstile(
            url="https://example.com",
            sitekey="0x4AAAAAAABkMYinukE8nzKd",
            action="submit",
            cdata="test-cdata",
            auto_detect=False
        )
        
        assert task_id == "test-task-456"
        
        # Check request payload
        request = responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["sitekey"] == "0x4AAAAAAABkMYinukE8nzKd"
        assert payload["action"] == "submit"
        assert payload["cdata"] == "test-cdata"
        assert payload["auto_detect"] is False
    
    def test_submit_turnstile_validation_errors(self):
        """Test Turnstile submission validation errors"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        # Invalid URL
        with pytest.raises(ValidationError):
            client.submit_turnstile("invalid-url")
        
        # No sitekey and auto_detect=False
        with pytest.raises(ValidationError, match="Either provide sitekey or enable auto_detect"):
            client.submit_turnstile("https://example.com", auto_detect=False)
    
    @responses.activate
    def test_submit_turnstile_rate_limit(self):
        """Test Turnstile submission rate limit error"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"error": "Rate limit exceeded"},
            status=429
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(RateLimitError, match="Rate limit exceeded"):
            client.submit_turnstile("https://example.com", auto_detect=True)


class TestRecaptchaSubmission:
    """Test reCAPTCHA task submission"""
    
    @responses.activate
    def test_submit_recaptcha_auto_detect(self):
        """Test reCAPTCHA submission with auto-detection"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/recaptcha",
            json={"task_id": "recaptcha-task-123"},
            status=202
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        task_id = client.submit_recaptcha(
            url="https://example.com",
            auto_detect=True
        )
        
        assert task_id == "recaptcha-task-123"
    
    @responses.activate
    def test_submit_recaptcha_manual_sitekey(self):
        """Test reCAPTCHA submission with manual sitekey"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/recaptcha",
            json={"task_id": "recaptcha-task-456"},
            status=202
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        task_id = client.submit_recaptcha(
            url="https://example.com",
            sitekey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
            auto_detect=False
        )
        
        assert task_id == "recaptcha-task-456"


class TestResultRetrieval:
    """Test result retrieval functionality"""
    
    @responses.activate
    def test_get_result_success(self):
        """Test successful result retrieval"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-123",
            json={
                "task_id": "test-task-123",
                "status": "success",
                "result": {
                    "turnstile_value": "0.abc123def456...",
                    "elapsed_time_seconds": 15.5,
                    "sitekey_used": "0x4AAAAAAABkMYinukE8nzKd"
                },
                "completed_at": "2024-01-15T10:30:00Z"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.get_result("test-task-123")
        
        assert result.task_id == "test-task-123"
        assert result.status == TaskStatus.SUCCESS
        assert result.turnstile_value == "0.abc123def456..."
        assert result.elapsed_time_seconds == 15.5
        assert result.sitekey_used == "0x4AAAAAAABkMYinukE8nzKd"
        assert result.completed_at == "2024-01-15T10:30:00Z"
        assert result.is_success
        assert not result.is_error
        assert not result.is_pending
    
    @responses.activate
    def test_get_result_pending(self):
        """Test pending result retrieval"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-456",
            json={
                "task_id": "test-task-456",
                "status": "pending"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.get_result("test-task-456")
        
        assert result.task_id == "test-task-456"
        assert result.status == TaskStatus.PENDING
        assert result.is_pending
        assert not result.is_success
        assert not result.is_error
    
    @responses.activate
    def test_get_result_error(self):
        """Test error result retrieval"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-789",
            json={
                "task_id": "test-task-789",
                "status": "error",
                "result": {
                    "reason": "Sitekey not found",
                    "errors": ["Invalid sitekey", "Page load failed"],
                    "sitekeys_tried": ["0x4AAAAAAABkMYinukE8nzKd"]
                }
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.get_result("test-task-789")
        
        assert result.task_id == "test-task-789"
        assert result.status == TaskStatus.ERROR
        assert result.reason == "Sitekey not found"
        assert result.errors == ["Invalid sitekey", "Page load failed"]
        assert result.sitekeys_tried == ["0x4AAAAAAABkMYinukE8nzKd"]
        assert result.is_error
        assert not result.is_success
        assert not result.is_pending
    
    @responses.activate
    def test_get_result_task_not_found(self):
        """Test task not found error"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/invalid-task",
            json={"error": "Task not found"},
            status=404
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(TaskNotFoundError, match="Task not found"):
            client.get_result("invalid-task")
    
    def test_get_result_validation_error(self):
        """Test get result validation error"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            client.get_result("")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            client.get_result(None)


class TestWaitForResult:
    """Test waiting for result functionality"""
    
    @responses.activate
    def test_wait_for_result_success(self):
        """Test successful wait for result"""
        # First call returns pending, second returns success
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-123",
            json={
                "task_id": "test-task-123",
                "status": "pending"
            },
            status=200
        )
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-123",
            json={
                "task_id": "test-task-123",
                "status": "success",
                "result": {
                    "turnstile_value": "0.abc123def456...",
                    "elapsed_time_seconds": 12.3
                }
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        start_time = time.time()
        result = client.wait_for_result("test-task-123", poll_interval=0.1)
        elapsed = time.time() - start_time
        
        assert result.is_success
        assert result.turnstile_value == "0.abc123def456..."
        assert elapsed < 1.0  # Should complete quickly
    
    @responses.activate 
    def test_wait_for_result_timeout(self):
        """Test wait for result timeout"""
        # Always return pending to trigger timeout
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-timeout",
            json={
                "task_id": "test-task-timeout",
                "status": "pending"
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key", timeout=1)  # 1 second timeout
        
        with pytest.raises(TimeoutError, match="did not complete within 1 seconds"):
            client.wait_for_result("test-task-timeout", poll_interval=0.1)


class TestSolveMethods:
    """Test complete solve methods"""
    
    @responses.activate
    def test_solve_turnstile_success(self):
        """Test complete Turnstile solving"""
        # Submit response
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"task_id": "test-task-123"},
            status=202
        )
        
        # Result response
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/test-task-123",
            json={
                "task_id": "test-task-123",
                "status": "success",
                "result": {
                    "turnstile_value": "0.abc123def456...",
                    "elapsed_time_seconds": 18.7,
                    "sitekey_used": "0x4AAAAAAABkMYinukE8nzKd"
                }
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.solve_turnstile("https://example.com", auto_detect=True)
        
        assert result.is_success
        assert result.turnstile_value == "0.abc123def456..."
        assert result.elapsed_time_seconds == 18.7
        assert result.sitekey_used == "0x4AAAAAAABkMYinukE8nzKd"
    
    @responses.activate
    def test_solve_recaptcha_success(self):
        """Test complete reCAPTCHA solving"""
        # Submit response
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/recaptcha",
            json={"task_id": "recaptcha-task-456"},
            status=202
        )
        
        # Result response
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/recaptcha-task-456",
            json={
                "task_id": "recaptcha-task-456",
                "status": "success",
                "result": {
                    "token": "03AGdBq25SxXT-pmSeBXjzScW-EiocHwwpwqJRCAI7...",
                    "elapsed_time_seconds": 25.4
                }
            },
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        result = client.solve_recaptcha("https://example.com", auto_detect=True)
        
        assert result.is_success
        assert result.token == "03AGdBq25SxXT-pmSeBXjzScW-EiocHwwpwqJRCAI7..."
        assert result.elapsed_time_seconds == 25.4


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @responses.activate
    def test_solve_turnstile_function(self):
        """Test solve_turnstile convenience function"""
        # Submit response
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"task_id": "convenience-task-123"},
            status=202
        )
        
        # Result response
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/convenience-task-123",
            json={
                "task_id": "convenience-task-123",
                "status": "success",
                "result": {
                    "turnstile_value": "0.convenience123...",
                    "elapsed_time_seconds": 14.2
                }
            },
            status=200
        )
        
        result = solve_turnstile("Rapidcaptcha-test-key", "https://example.com", auto_detect=True)
        
        assert result.is_success
        assert result.turnstile_value == "0.convenience123..."
        assert result.elapsed_time_seconds == 14.2
    
    @responses.activate
    def test_solve_recaptcha_function(self):
        """Test solve_recaptcha convenience function"""
        # Submit response
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/recaptcha",
            json={"task_id": "convenience-recaptcha-456"},
            status=202
        )
        
        # Result response
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/api/result/convenience-recaptcha-456",
            json={
                "task_id": "convenience-recaptcha-456",
                "status": "success",
                "result": {
                    "token": "03AGdBq25convenience...",
                    "elapsed_time_seconds": 22.1
                }
            },
            status=200
        )
        
        result = solve_recaptcha("Rapidcaptcha-test-key", "https://example.com", auto_detect=True)
        
        assert result.is_success
        assert result.token == "03AGdBq25convenience..."
        assert result.elapsed_time_seconds == 22.1


class TestCaptchaResult:
    """Test CaptchaResult class"""
    
    def test_captcha_result_success(self):
        """Test CaptchaResult for successful solve"""
        result = CaptchaResult(
            task_id="test-123",
            status=TaskStatus.SUCCESS,
            turnstile_value="0.abc123...",
            elapsed_time_seconds=15.5,
            sitekey_used="0x4AAAAAAABkMYinukE8nzKd"
        )
        
        assert result.is_success
        assert not result.is_error
        assert not result.is_pending
        assert "SUCCESS" in str(result)
        assert "test-123" in str(result)
    
    def test_captcha_result_error(self):
        """Test CaptchaResult for failed solve"""
        result = CaptchaResult(
            task_id="test-456",
            status=TaskStatus.ERROR,
            reason="Sitekey not found",
            errors=["Invalid sitekey"]
        )
        
        assert result.is_error
        assert not result.is_success
        assert not result.is_pending
        assert "ERROR" in str(result)
        assert "Sitekey not found" in str(result)
    
    def test_captcha_result_pending(self):
        """Test CaptchaResult for pending solve"""
        result = CaptchaResult(
            task_id="test-789",
            status=TaskStatus.PENDING
        )
        
        assert result.is_pending
        assert not result.is_success
        assert not result.is_error
        assert "PENDING" in str(result)
        assert "test-789" in str(result)


class TestErrorHandling:
    """Test error handling in responses"""
    
    @responses.activate
    def test_handle_response_validation_error(self):
        """Test handling validation error response"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"message": "Invalid URL format"},
            status=400
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(ValidationError, match="Invalid URL format"):
            client.submit_turnstile("https://example.com", auto_detect=True)
    
    @responses.activate
    def test_handle_response_json_decode_error(self):
        """Test handling invalid JSON response"""
        responses.add(
            responses.GET,
            "https://rapidcaptcha.xyz/",
            body="Invalid JSON response",
            status=200
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(Exception):  # Should raise JSON decode error
            client.health_check()
    
    @responses.activate
    def test_handle_response_unknown_error(self):
        """Test handling unknown error response"""
        responses.add(
            responses.POST,
            "https://rapidcaptcha.xyz/api/solve/turnstile",
            json={"message": "Internal server error"},
            status=500
        )
        
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        with pytest.raises(Exception, match="Internal server error"):
            client.submit_turnstile("https://example.com", auto_detect=True)


class TestRequestsImportError:
    """Test behavior when requests library is not available"""
    
    def test_health_check_no_requests(self):
        """Test health check without requests library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_REQUESTS', False):
            with pytest.raises(ImportError, match="requests library is required"):
                client.health_check()
    
    def test_submit_turnstile_no_requests(self):
        """Test submit turnstile without requests library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_REQUESTS', False):
            with pytest.raises(ImportError, match="requests library is required"):
                client.submit_turnstile("https://example.com", auto_detect=True)


if __name__ == "__main__":
    pytest.main([__file__])