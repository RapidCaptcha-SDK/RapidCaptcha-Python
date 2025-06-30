"""
Test cases for RapidCaptcha client asynchronous operations
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch
import aioresponses

from rapidcaptcha import (
    RapidCaptchaClient, CaptchaResult, TaskStatus,
    APIKeyError, ValidationError, TaskNotFoundError,
    RateLimitError, TimeoutError
)


pytestmark = pytest.mark.asyncio


class TestAsyncHealthCheck:
    """Test async health check functionality"""
    
    async def test_health_check_async_success(self):
        """Test successful async health check"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/",
                payload={"status": "ok", "message": "API is healthy"},
                status=200
            )
            
            result = await client.health_check_async()
            
            assert result["status"] == "ok"
            assert result["message"] == "API is healthy"
    
    async def test_health_check_async_api_key_error(self):
        """Test async health check with invalid API key"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/",
                payload={"error": "Invalid API key"},
                status=401
            )
            
            with pytest.raises(Exception, match="Async internal server error"):
                await client.submit_turnstile_async("https://example.com", auto_detect=True)


class TestAsyncSemaphoreRateLimit:
    """Test async operations with semaphore for rate limiting"""
    
    async def test_batch_processing_with_semaphore(self):
        """Test batch processing with semaphore to respect rate limits"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests
        
        async def solve_with_semaphore(url, task_num):
            """Solve with semaphore to respect rate limits"""
            async with semaphore:
                return await client.solve_turnstile_async(url, auto_detect=True)
        
        urls = ["https://example.com"] * 4  # 4 identical URLs for demo
        
        with aioresponses.aioresponses() as m:
            # Setup responses for all tasks
            for i in range(1, 5):
                m.post(
                    "https://rapidcaptcha.xyz/api/solve/turnstile",
                    payload={"task_id": f"batch-task-{i}"},
                    status=202
                )
                m.get(
                    f"https://rapidcaptcha.xyz/api/result/batch-task-{i}",
                    payload={
                        "task_id": f"batch-task-{i}",
                        "status": "success",
                        "result": {
                            "turnstile_value": f"0.batch{i}...",
                            "elapsed_time_seconds": 10.0
                        }
                    },
                    status=200
                )
            
            # Process all URLs with rate limiting
            start_time = time.time()
            tasks = [
                solve_with_semaphore(url, i) 
                for i, url in enumerate(urls, 1)
            ]
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # All should succeed
            successful = sum(1 for r in results if r and r.is_success)
            assert successful == 4
            
            # Verify semaphore worked (should take some time due to rate limiting)
            assert elapsed < 5.0  # But not too long due to mocking


class TestAsyncImportError:
    """Test behavior when aiohttp library is not available"""
    
    async def test_submit_turnstile_async_no_aiohttp(self):
        """Test async submit turnstile without aiohttp library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_AIOHTTP', False):
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.submit_turnstile_async("https://example.com", auto_detect=True)
    
    async def test_submit_recaptcha_async_no_aiohttp(self):
        """Test async submit recaptcha without aiohttp library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_AIOHTTP', False):
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.submit_recaptcha_async("https://example.com", auto_detect=True)
    
    async def test_get_result_async_no_aiohttp(self):
        """Test async get result without aiohttp library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_AIOHTTP', False):
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.get_result_async("test-task-123")


class TestAsyncEdgeCases:
    """Test async edge cases and error scenarios"""
    
    async def test_solve_turnstile_async_immediate_error(self):
        """Test async Turnstile solving with immediate error"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # Submit response
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "immediate-error-task"},
                status=202
            )
            
            # Result response - immediate error
            m.get(
                "https://rapidcaptcha.xyz/api/result/immediate-error-task",
                payload={
                    "task_id": "immediate-error-task",
                    "status": "error",
                    "result": {
                        "reason": "Invalid sitekey format",
                        "errors": ["Sitekey validation failed"]
                    }
                },
                status=200
            )
            
            result = await client.solve_turnstile_async("https://example.com", auto_detect=True)
            
            assert result.is_error
            assert result.reason == "Invalid sitekey format"
            assert result.errors == ["Sitekey validation failed"]
    
    async def test_solve_multiple_with_exceptions(self):
        """Test solving multiple CAPTCHAs where some raise exceptions"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # Task 1: Success
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "exception-task-1"},
                status=202
            )
            m.get(
                "https://rapidcaptcha.xyz/api/result/exception-task-1",
                payload={
                    "task_id": "exception-task-1",
                    "status": "success",
                    "result": {"turnstile_value": "0.success..."}
                },
                status=200
            )
            
            # Task 2: Rate limit error
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"error": "Rate limit exceeded"},
                status=429
            )
            
            # Task 3: Success
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "exception-task-3"},
                status=202
            )
            m.get(
                "https://rapidcaptcha.xyz/api/result/exception-task-3",
                payload={
                    "task_id": "exception-task-3",
                    "status": "success",
                    "result": {"turnstile_value": "0.success2..."}
                },
                status=200
            )
            
            # Solve with exception handling
            tasks = [
                client.solve_turnstile_async("https://example1.com", auto_detect=True),
                client.solve_turnstile_async("https://example2.com", auto_detect=True),
                client.solve_turnstile_async("https://example3.com", auto_detect=True)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check results
            assert results[0].is_success
            assert results[0].turnstile_value == "0.success..."
            
            assert isinstance(results[1], RateLimitError)
            
            assert results[2].is_success
            assert results[2].turnstile_value == "0.success2..."
    
    async def test_async_context_manager_simulation(self):
        """Test async operation in context manager style"""
        async def async_solve_context():
            """Simulate using client in async context"""
            client = RapidCaptchaClient("Rapidcaptcha-test-key")
            
            with aioresponses.aioresponses() as m:
                m.post(
                    "https://rapidcaptcha.xyz/api/solve/turnstile",
                    payload={"task_id": "context-task"},
                    status=202
                )
                m.get(
                    "https://rapidcaptcha.xyz/api/result/context-task",
                    payload={
                        "task_id": "context-task",
                        "status": "success",
                        "result": {"turnstile_value": "0.context..."}
                    },
                    status=200
                )
                
                return await client.solve_turnstile_async("https://example.com", auto_detect=True)
        
        result = await async_solve_context()
        assert result.is_success
        assert result.turnstile_value == "0.context..."


class TestAsyncPerformance:
    """Test async performance characteristics"""
    
    async def test_concurrent_vs_sequential_performance(self):
        """Compare concurrent vs sequential solving performance"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        urls = ["https://example.com"] * 3
        
        with aioresponses.aioresponses() as m:
            # Setup responses for all tasks
            for i in range(1, 4):
                m.post(
                    "https://rapidcaptcha.xyz/api/solve/turnstile",
                    payload={"task_id": f"perf-task-{i}"},
                    status=202
                )
                m.get(
                    f"https://rapidcaptcha.xyz/api/result/perf-task-{i}",
                    payload={
                        "task_id": f"perf-task-{i}",
                        "status": "success",
                        "result": {"turnstile_value": f"0.perf{i}..."}
                    },
                    status=200
                )
            
            # Test concurrent execution
            start_time = time.time()
            concurrent_tasks = [
                client.solve_turnstile_async(url, auto_detect=True) 
                for url in urls
            ]
            concurrent_results = await asyncio.gather(*concurrent_tasks)
            concurrent_time = time.time() - start_time
            
            # All should succeed
            assert all(r.is_success for r in concurrent_results)
            
            # Should be very fast due to mocking
            assert concurrent_time < 1.0


if __name__ == "__main__":
    pytest.main([__file__])raises(APIKeyError, match="Invalid API key"):
                await client.health_check_async()
    
    async def test_health_check_async_no_aiohttp(self):
        """Test async health check without aiohttp library"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with patch('rapidcaptcha.client.HAS_AIOHTTP', False):
            with pytest.raises(ImportError, match="aiohttp library is required"):
                await client.health_check_async()


class TestAsyncTurnstileSubmission:
    """Test async Turnstile task submission"""
    
    async def test_submit_turnstile_async_auto_detect(self):
        """Test async Turnstile submission with auto-detection"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "async-task-123"},
                status=202
            )
            
            task_id = await client.submit_turnstile_async(
                url="https://example.com",
                auto_detect=True
            )
            
            assert task_id == "async-task-123"
    
    async def test_submit_turnstile_async_manual_sitekey(self):
        """Test async Turnstile submission with manual sitekey"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "async-task-456"},
                status=202
            )
            
            task_id = await client.submit_turnstile_async(
                url="https://example.com",
                sitekey="0x4AAAAAAABkMYinukE8nzKd",
                action="submit",
                cdata="test-cdata",
                auto_detect=False
            )
            
            assert task_id == "async-task-456"
    
    async def test_submit_turnstile_async_validation_errors(self):
        """Test async Turnstile submission validation errors"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        # Invalid URL
        with pytest.raises(ValidationError):
            await client.submit_turnstile_async("invalid-url")
        
        # No sitekey and auto_detect=False
        with pytest.raises(ValidationError, match="Either provide sitekey or enable auto_detect"):
            await client.submit_turnstile_async("https://example.com", auto_detect=False)
    
    async def test_submit_turnstile_async_rate_limit(self):
        """Test async Turnstile submission rate limit error"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"error": "Rate limit exceeded"},
                status=429
            )
            
            with pytest.raises(RateLimitError, match="Rate limit exceeded"):
                await client.submit_turnstile_async("https://example.com", auto_detect=True)


class TestAsyncRecaptchaSubmission:
    """Test async reCAPTCHA task submission"""
    
    async def test_submit_recaptcha_async_auto_detect(self):
        """Test async reCAPTCHA submission with auto-detection"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/recaptcha",
                payload={"task_id": "async-recaptcha-123"},
                status=202
            )
            
            task_id = await client.submit_recaptcha_async(
                url="https://example.com",
                auto_detect=True
            )
            
            assert task_id == "async-recaptcha-123"
    
    async def test_submit_recaptcha_async_manual_sitekey(self):
        """Test async reCAPTCHA submission with manual sitekey"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/recaptcha",
                payload={"task_id": "async-recaptcha-456"},
                status=202
            )
            
            task_id = await client.submit_recaptcha_async(
                url="https://example.com",
                sitekey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-",
                auto_detect=False
            )
            
            assert task_id == "async-recaptcha-456"


class TestAsyncResultRetrieval:
    """Test async result retrieval functionality"""
    
    async def test_get_result_async_success(self):
        """Test successful async result retrieval"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-task-123",
                payload={
                    "task_id": "async-task-123",
                    "status": "success",
                    "result": {
                        "turnstile_value": "0.async123def456...",
                        "elapsed_time_seconds": 16.8,
                        "sitekey_used": "0x4AAAAAAABkMYinukE8nzKd"
                    },
                    "completed_at": "2024-01-15T10:30:00Z"
                },
                status=200
            )
            
            result = await client.get_result_async("async-task-123")
            
            assert result.task_id == "async-task-123"
            assert result.status == TaskStatus.SUCCESS
            assert result.turnstile_value == "0.async123def456..."
            assert result.elapsed_time_seconds == 16.8
            assert result.sitekey_used == "0x4AAAAAAABkMYinukE8nzKd"
            assert result.completed_at == "2024-01-15T10:30:00Z"
            assert result.is_success
    
    async def test_get_result_async_pending(self):
        """Test async pending result retrieval"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-task-456",
                payload={
                    "task_id": "async-task-456",
                    "status": "pending"
                },
                status=200
            )
            
            result = await client.get_result_async("async-task-456")
            
            assert result.task_id == "async-task-456"
            assert result.status == TaskStatus.PENDING
            assert result.is_pending
    
    async def test_get_result_async_error(self):
        """Test async error result retrieval"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-task-789",
                payload={
                    "task_id": "async-task-789",
                    "status": "error",
                    "result": {
                        "reason": "Async sitekey not found",
                        "errors": ["Invalid sitekey", "Page load failed"],
                        "sitekeys_tried": ["0x4AAAAAAABkMYinukE8nzKd"]
                    }
                },
                status=200
            )
            
            result = await client.get_result_async("async-task-789")
            
            assert result.task_id == "async-task-789"
            assert result.status == TaskStatus.ERROR
            assert result.reason == "Async sitekey not found"
            assert result.errors == ["Invalid sitekey", "Page load failed"]
            assert result.sitekeys_tried == ["0x4AAAAAAABkMYinukE8nzKd"]
            assert result.is_error
    
    async def test_get_result_async_task_not_found(self):
        """Test async task not found error"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.get(
                "https://rapidcaptcha.xyz/api/result/invalid-async-task",
                payload={"error": "Task not found"},
                status=404
            )
            
            with pytest.raises(TaskNotFoundError, match="Task not found"):
                await client.get_result_async("invalid-async-task")
    
    async def test_get_result_async_validation_error(self):
        """Test async get result validation error"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            await client.get_result_async("")
        
        with pytest.raises(ValidationError, match="Task ID is required"):
            await client.get_result_async(None)


class TestAsyncWaitForResult:
    """Test async waiting for result functionality"""
    
    async def test_wait_for_result_async_success(self):
        """Test successful async wait for result"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # First call returns pending
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-wait-123",
                payload={
                    "task_id": "async-wait-123",
                    "status": "pending"
                },
                status=200
            )
            
            # Second call returns success
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-wait-123",
                payload={
                    "task_id": "async-wait-123",
                    "status": "success",
                    "result": {
                        "turnstile_value": "0.asyncwait123...",
                        "elapsed_time_seconds": 13.7
                    }
                },
                status=200
            )
            
            start_time = time.time()
            result = await client.wait_for_result_async("async-wait-123", poll_interval=0.1)
            elapsed = time.time() - start_time
            
            assert result.is_success
            assert result.turnstile_value == "0.asyncwait123..."
            assert elapsed < 1.0  # Should complete quickly
    
    async def test_wait_for_result_async_timeout(self):
        """Test async wait for result timeout"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key", timeout=1)  # 1 second timeout
        
        with aioresponses.aioresponses() as m:
            # Always return pending to trigger timeout
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-timeout-task",
                payload={
                    "task_id": "async-timeout-task",
                    "status": "pending"
                },
                status=200,
                repeat=True
            )
            
            with pytest.raises(TimeoutError, match="did not complete within 1 seconds"):
                await client.wait_for_result_async("async-timeout-task", poll_interval=0.1)


class TestAsyncSolveMethods:
    """Test async complete solve methods"""
    
    async def test_solve_turnstile_async_success(self):
        """Test complete async Turnstile solving"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # Submit response
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "async-solve-123"},
                status=202
            )
            
            # Result response
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-solve-123",
                payload={
                    "task_id": "async-solve-123",
                    "status": "success",
                    "result": {
                        "turnstile_value": "0.asyncsolve123...",
                        "elapsed_time_seconds": 19.4,
                        "sitekey_used": "0x4AAAAAAABkMYinukE8nzKd"
                    }
                },
                status=200
            )
            
            result = await client.solve_turnstile_async("https://example.com", auto_detect=True)
            
            assert result.is_success
            assert result.turnstile_value == "0.asyncsolve123..."
            assert result.elapsed_time_seconds == 19.4
            assert result.sitekey_used == "0x4AAAAAAABkMYinukE8nzKd"
    
    async def test_solve_recaptcha_async_success(self):
        """Test complete async reCAPTCHA solving"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # Submit response
            m.post(
                "https://rapidcaptcha.xyz/api/solve/recaptcha",
                payload={"task_id": "async-recaptcha-solve-456"},
                status=202
            )
            
            # Result response
            m.get(
                "https://rapidcaptcha.xyz/api/result/async-recaptcha-solve-456",
                payload={
                    "task_id": "async-recaptcha-solve-456",
                    "status": "success",
                    "result": {
                        "token": "03AGdBq25AsyncRecaptcha...",
                        "elapsed_time_seconds": 26.8
                    }
                },
                status=200
            )
            
            result = await client.solve_recaptcha_async("https://example.com", auto_detect=True)
            
            assert result.is_success
            assert result.token == "03AGdBq25AsyncRecaptcha..."
            assert result.elapsed_time_seconds == 26.8


class TestAsyncConcurrentSolving:
    """Test concurrent async solving"""
    
    async def test_concurrent_turnstile_solving(self):
        """Test solving multiple Turnstile CAPTCHAs concurrently"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        urls = [
            "https://example1.com",
            "https://example2.com",
            "https://example3.com"
        ]
        
        with aioresponses.aioresponses() as m:
            # Submit responses
            for i, url in enumerate(urls, 1):
                m.post(
                    "https://rapidcaptcha.xyz/api/solve/turnstile",
                    payload={"task_id": f"concurrent-task-{i}"},
                    status=202
                )
            
            # Result responses
            for i in range(1, len(urls) + 1):
                m.get(
                    f"https://rapidcaptcha.xyz/api/result/concurrent-task-{i}",
                    payload={
                        "task_id": f"concurrent-task-{i}",
                        "status": "success",
                        "result": {
                            "turnstile_value": f"0.concurrent{i}...",
                            "elapsed_time_seconds": 15.0 + i
                        }
                    },
                    status=200
                )
            
            # Solve concurrently
            tasks = [
                client.solve_turnstile_async(url, auto_detect=True) 
                for url in urls
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks)
            elapsed = time.time() - start_time
            
            # Check results
            for i, result in enumerate(results, 1):
                assert result.is_success
                assert result.turnstile_value == f"0.concurrent{i}..."
                assert result.elapsed_time_seconds == 15.0 + i
            
            # Should be faster than sequential execution
            assert elapsed < 2.0  # Much faster than 3 * 15 seconds
    
    async def test_concurrent_mixed_results(self):
        """Test concurrent solving with mixed success/failure results"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            # Task 1: Success
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "mixed-task-1"},
                status=202
            )
            m.get(
                "https://rapidcaptcha.xyz/api/result/mixed-task-1",
                payload={
                    "task_id": "mixed-task-1",
                    "status": "success",
                    "result": {"turnstile_value": "0.success..."}
                },
                status=200
            )
            
            # Task 2: Error
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "mixed-task-2"},
                status=202
            )
            m.get(
                "https://rapidcaptcha.xyz/api/result/mixed-task-2",
                payload={
                    "task_id": "mixed-task-2",
                    "status": "error",
                    "result": {"reason": "Failed to solve"}
                },
                status=200
            )
            
            # Task 3: Success
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"task_id": "mixed-task-3"},
                status=202
            )
            m.get(
                "https://rapidcaptcha.xyz/api/result/mixed-task-3",
                payload={
                    "task_id": "mixed-task-3",
                    "status": "success",
                    "result": {"turnstile_value": "0.success2..."}
                },
                status=200
            )
            
            # Solve concurrently
            tasks = [
                client.solve_turnstile_async("https://example1.com", auto_detect=True),
                client.solve_turnstile_async("https://example2.com", auto_detect=True),
                client.solve_turnstile_async("https://example3.com", auto_detect=True)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Check results
            assert results[0].is_success
            assert results[0].turnstile_value == "0.success..."
            
            assert results[1].is_error
            assert results[1].reason == "Failed to solve"
            
            assert results[2].is_success
            assert results[2].turnstile_value == "0.success2..."


class TestAsyncErrorHandling:
    """Test async error handling"""
    
    async def test_handle_response_async_validation_error(self):
        """Test handling async validation error response"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"message": "Async invalid URL format"},
                status=400
            )
            
            with pytest.raises(ValidationError, match="Async invalid URL format"):
                await client.submit_turnstile_async("https://example.com", auto_detect=True)
    
    async def test_handle_response_async_unknown_error(self):
        """Test handling async unknown error response"""
        client = RapidCaptchaClient("Rapidcaptcha-test-key")
        
        with aioresponses.aioresponses() as m:
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"message": "Async internal server error"},
                status=500
            )
            
            with pytest.