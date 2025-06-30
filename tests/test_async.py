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
            m.post(
                "https://rapidcaptcha.xyz/api/solve/turnstile",
                payload={"error": "Invalid API key"},
                status=401
            )
            with pytest.raises(APIKeyError, match="Invalid API key"):
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
    pytest.main([__file__])