"""
RapidCaptcha Python SDK
Official Python client for RapidCaptcha API

Installation:
    pip install rapidcaptcha

Usage:
    from rapidcaptcha import RapidCaptchaClient
    
    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")
    result = client.solve_turnstile("https://example.com", auto_detect=True)
    
    if result.is_success:
        print(f"Token: {result.turnstile_value}")
"""

__version__ = "1.0.0"
__author__ = "Galkurta"
__email__ = "support@rapidcaptcha.xyz"

import asyncio
import time
import json
from typing import Dict, Optional, Union, List
from dataclasses import dataclass
from enum import Enum

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class CaptchaType(Enum):
    TURNSTILE = "turnstile"
    RECAPTCHA = "recaptcha"


class TaskStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"


@dataclass
class CaptchaResult:
    """Result object for CAPTCHA solving"""
    task_id: str
    status: TaskStatus
    token: Optional[str] = None
    turnstile_value: Optional[str] = None
    elapsed_time_seconds: Optional[float] = None
    sitekey_used: Optional[str] = None
    sitekeys_tried: Optional[List[str]] = None
    reason: Optional[str] = None
    errors: Optional[List[str]] = None
    completed_at: Optional[str] = None

    @property
    def is_success(self) -> bool:
        """Check if the solve was successful"""
        return self.status == TaskStatus.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if the solve failed"""
        return self.status == TaskStatus.ERROR

    @property
    def is_pending(self) -> bool:
        """Check if the solve is still pending"""
        return self.status == TaskStatus.PENDING

    def __str__(self) -> str:
        if self.is_success:
            token = self.token or self.turnstile_value
            return f"CaptchaResult(SUCCESS, task_id={self.task_id}, token={token[:20]}..., time={self.elapsed_time_seconds}s)"
        elif self.is_error:
            return f"CaptchaResult(ERROR, task_id={self.task_id}, reason={self.reason})"
        else:
            return f"CaptchaResult(PENDING, task_id={self.task_id})"


class RapidCaptchaError(Exception):
    """Base exception for RapidCaptcha errors"""
    pass


class APIKeyError(RapidCaptchaError):
    """Raised when API key is invalid or missing"""
    pass


class TaskNotFoundError(RapidCaptchaError):
    """Raised when task ID is not found"""
    pass


class ValidationError(RapidCaptchaError):
    """Raised when request parameters are invalid"""
    pass


class RateLimitError(RapidCaptchaError):
    """Raised when rate limit is exceeded"""
    pass


class TimeoutError(RapidCaptchaError):
    """Raised when operation times out"""
    pass


class RapidCaptchaClient:
    """
    RapidCaptcha API Client
    
    Supports both sync and async operations for solving CAPTCHA challenges.
    
    Example:
        >>> client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")
        >>> result = client.solve_turnstile("https://example.com", auto_detect=True)
        >>> if result.is_success:
        ...     print(f"Solved: {result.turnstile_value}")
    """
    
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://rapidcaptcha.xyz",
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 2.0
    ):
        """
        Initialize RapidCaptcha client
        
        Args:
            api_key: Your RapidCaptcha API key (starts with 'Rapidcaptcha-')
            base_url: API base URL (default: https://rapidcaptcha.xyz)
            timeout: Maximum time to wait for task completion in seconds
            max_retries: Maximum number of retries for failed requests
            retry_delay: Delay between retries in seconds
            
        Raises:
            APIKeyError: If API key format is invalid
        """
        if (
            not isinstance(api_key, str)
            or not api_key
            or not api_key.startswith("Rapidcaptcha-")
            or api_key == "Rapidcaptcha-"
        ):
            raise APIKeyError("Invalid API key format. Must start with 'Rapidcaptcha-' and have a non-empty suffix")
        
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "User-Agent": f"RapidCaptcha-Python-SDK/{__version__}"
        }

    def _validate_url(self, url: str) -> None:
        """Validate URL parameter"""
        if not url or not isinstance(url, str):
            raise ValidationError("URL is required and must be a string")
        if not url.startswith(("http://", "https://")):
            raise ValidationError("URL must start with http:// or https://")

    def _handle_response(self, response, expected_status: int = 200) -> Dict:
        """Handle HTTP response and raise appropriate exceptions"""
        if response.status_code == 401:
            raise APIKeyError("Invalid API key")
        elif response.status_code == 404:
            raise TaskNotFoundError("Task not found or expired")
        elif response.status_code == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status_code == 400:
            try:
                error_data = response.json()
                raise ValidationError(error_data.get('message', 'Bad request'))
            except (json.JSONDecodeError, KeyError):
                raise ValidationError("Bad request")
        elif response.status_code != expected_status:
            try:
                error_data = response.json()
                raise RapidCaptchaError(f"API error: {error_data.get('message', 'Unknown error')}")
            except json.JSONDecodeError:
                raise RapidCaptchaError(f"HTTP {response.status_code}: {response.text}")
        
        try:
            return response.json()
        except json.JSONDecodeError:
            raise RapidCaptchaError("Invalid JSON response from API")

    def health_check(self) -> Dict:
        """
        Check API health status
        
        Returns:
            Dict containing API health information
            
        Raises:
            ImportError: If requests library is not installed
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for sync operations. Install with: pip install requests")
        
        response = requests.get(f"{self.base_url}/", headers=self.headers, timeout=10)
        return self._handle_response(response)

    def submit_turnstile(
        self,
        url: str,
        sitekey: Optional[str] = None,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        auto_detect: bool = True
    ) -> str:
        """
        Submit Turnstile solving task
        
        Args:
            url: Target website URL
            sitekey: Turnstile sitekey (optional if auto_detect=True)
            action: Turnstile action parameter (optional)
            cdata: Turnstile cdata parameter (optional)
            auto_detect: Enable auto-detection of sitekey
            
        Returns:
            Task ID string
            
        Raises:
            ValidationError: If parameters are invalid
            APIKeyError: If API key is invalid
            RateLimitError: If rate limit is exceeded
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for sync operations. Install with: pip install requests")
        
        self._validate_url(url)
        
        if not sitekey and not auto_detect:
            raise ValidationError("Either provide sitekey or enable auto_detect")
        
        payload = {
            "url": url,
            "auto_detect": auto_detect
        }
        
        if sitekey:
            payload["sitekey"] = sitekey
        if action:
            payload["action"] = action
        if cdata:
            payload["cdata"] = cdata
        
        response = requests.post(
            f"{self.base_url}/api/solve/turnstile",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        result = self._handle_response(response, 202)
        return result["task_id"]

    def submit_recaptcha(
        self,
        url: str,
        sitekey: Optional[str] = None,
        auto_detect: bool = True
    ) -> str:
        """
        Submit reCAPTCHA solving task
        
        Args:
            url: Target website URL
            sitekey: reCAPTCHA sitekey (optional if auto_detect=True)
            auto_detect: Enable auto-detection of sitekey
            
        Returns:
            Task ID string
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for sync operations. Install with: pip install requests")
        
        self._validate_url(url)
        
        if not sitekey and not auto_detect:
            raise ValidationError("Either provide sitekey or enable auto_detect")
        
        payload = {
            "url": url,
            "auto_detect": auto_detect
        }
        
        if sitekey:
            payload["sitekey"] = sitekey
        
        response = requests.post(
            f"{self.base_url}/api/solve/recaptcha",
            headers=self.headers,
            json=payload,
            timeout=30
        )
        
        result = self._handle_response(response, 202)
        return result["task_id"]

    def get_result(self, task_id: str) -> CaptchaResult:
        """
        Get task result by task ID
        
        Args:
            task_id: Task ID returned from submit methods
            
        Returns:
            CaptchaResult object
            
        Raises:
            TaskNotFoundError: If task is not found
        """
        if not HAS_REQUESTS:
            raise ImportError("requests library is required for sync operations. Install with: pip install requests")
        
        if not task_id:
            raise ValidationError("Task ID is required")
        
        response = requests.get(
            f"{self.base_url}/api/result/{task_id}",
            headers={"X-API-Key": self.api_key},
            timeout=30
        )
        
        data = self._handle_response(response)
        
        # Parse result data
        result_data = data.get("result", {})
        status = TaskStatus(data.get("status", "pending"))
        
        return CaptchaResult(
            task_id=data.get("task_id", task_id),
            status=status,
            token=result_data.get("token"),
            turnstile_value=result_data.get("turnstile_value"),
            elapsed_time_seconds=result_data.get("elapsed_time_seconds"),
            sitekey_used=result_data.get("sitekey_used"),
            sitekeys_tried=result_data.get("sitekeys_tried"),
            reason=result_data.get("reason"),
            errors=result_data.get("errors"),
            completed_at=data.get("completed_at")
        )

    def wait_for_result(self, task_id: str, poll_interval: float = 2.0) -> CaptchaResult:
        """
        Wait for task completion and return result
        
        Args:
            task_id: Task ID to wait for
            poll_interval: Polling interval in seconds
            
        Returns:
            CaptchaResult object when completed
            
        Raises:
            TimeoutError: If task doesn't complete within timeout
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            result = self.get_result(task_id)
            
            if result.is_success or result.is_error:
                return result
            
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {self.timeout} seconds")

    def solve_turnstile(
        self,
        url: str,
        sitekey: Optional[str] = None,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        auto_detect: bool = True,
        poll_interval: float = 2.0
    ) -> CaptchaResult:
        """
        Solve Turnstile CAPTCHA (submit + wait for result)
        
        Args:
            url: Target website URL
            sitekey: Turnstile sitekey (optional if auto_detect=True)
            action: Turnstile action parameter (optional)
            cdata: Turnstile cdata parameter (optional)
            auto_detect: Enable auto-detection of sitekey
            poll_interval: Polling interval in seconds
            
        Returns:
            CaptchaResult object
            
        Example:
            >>> result = client.solve_turnstile("https://example.com", auto_detect=True)
            >>> if result.is_success:
            ...     print(f"Solved: {result.turnstile_value}")
        """
        task_id = self.submit_turnstile(url, sitekey, action, cdata, auto_detect)
        return self.wait_for_result(task_id, poll_interval)

    def solve_recaptcha(
        self,
        url: str,
        sitekey: Optional[str] = None,
        auto_detect: bool = True,
        poll_interval: float = 2.0
    ) -> CaptchaResult:
        """
        Solve reCAPTCHA (submit + wait for result)
        
        Args:
            url: Target website URL
            sitekey: reCAPTCHA sitekey (optional if auto_detect=True)
            auto_detect: Enable auto-detection of sitekey
            poll_interval: Polling interval in seconds
            
        Returns:
            CaptchaResult object
        """
        task_id = self.submit_recaptcha(url, sitekey, auto_detect)
        return self.wait_for_result(task_id, poll_interval)

    # Async methods
    async def _handle_response_async(self, response, expected_status: int = 200) -> Dict:
        """Handle async HTTP response"""
        if response.status == 401:
            raise APIKeyError("Invalid API key")
        elif response.status == 404:
            raise TaskNotFoundError("Task not found or expired")
        elif response.status == 429:
            raise RateLimitError("Rate limit exceeded")
        elif response.status == 400:
            try:
                error_data = await response.json()
                raise ValidationError(error_data.get('message', 'Bad request'))
            except (json.JSONDecodeError, KeyError):
                raise ValidationError("Bad request")
        elif response.status != expected_status:
            try:
                error_data = await response.json()
                raise RapidCaptchaError(f"API error: {error_data.get('message', 'Unknown error')}")
            except:
                text = await response.text()
                raise RapidCaptchaError(f"HTTP {response.status}: {text}")
        
        return await response.json()

    async def health_check_async(self) -> Dict:
        """Async version of health_check"""
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp library is required for async operations. Install with: pip install aiohttp")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/", headers=self.headers, timeout=10) as response:
                return await self._handle_response_async(response)

    async def submit_turnstile_async(
        self,
        url: str,
        sitekey: Optional[str] = None,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        auto_detect: bool = True
    ) -> str:
        """Async version of submit_turnstile"""
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp library is required for async operations. Install with: pip install aiohttp")
        
        self._validate_url(url)
        
        if not sitekey and not auto_detect:
            raise ValidationError("Either provide sitekey or enable auto_detect")
        
        payload = {
            "url": url,
            "auto_detect": auto_detect
        }
        
        if sitekey:
            payload["sitekey"] = sitekey
        if action:
            payload["action"] = action
        if cdata:
            payload["cdata"] = cdata
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/solve/turnstile",
                headers=self.headers,
                json=payload,
                timeout=30
            ) as response:
                result = await self._handle_response_async(response, 202)
                return result["task_id"]

    async def submit_recaptcha_async(
        self,
        url: str,
        sitekey: Optional[str] = None,
        auto_detect: bool = True
    ) -> str:
        """Async version of submit_recaptcha"""
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp library is required for async operations. Install with: pip install aiohttp")
        
        self._validate_url(url)
        
        if not sitekey and not auto_detect:
            raise ValidationError("Either provide sitekey or enable auto_detect")
        
        payload = {
            "url": url,
            "auto_detect": auto_detect
        }
        
        if sitekey:
            payload["sitekey"] = sitekey
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/solve/recaptcha",
                headers=self.headers,
                json=payload,
                timeout=30
            ) as response:
                result = await self._handle_response_async(response, 202)
                return result["task_id"]

    async def get_result_async(self, task_id: str) -> CaptchaResult:
        """Async version of get_result"""
        if not HAS_AIOHTTP:
            raise ImportError("aiohttp library is required for async operations. Install with: pip install aiohttp")
        
        if not task_id:
            raise ValidationError("Task ID is required")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/api/result/{task_id}",
                headers={"X-API-Key": self.api_key},
                timeout=30
            ) as response:
                data = await self._handle_response_async(response)
                
                # Parse result data
                result_data = data.get("result", {})
                status = TaskStatus(data.get("status", "pending"))
                
                return CaptchaResult(
                    task_id=data.get("task_id", task_id),
                    status=status,
                    token=result_data.get("token"),
                    turnstile_value=result_data.get("turnstile_value"),
                    elapsed_time_seconds=result_data.get("elapsed_time_seconds"),
                    sitekey_used=result_data.get("sitekey_used"),
                    sitekeys_tried=result_data.get("sitekeys_tried"),
                    reason=result_data.get("reason"),
                    errors=result_data.get("errors"),
                    completed_at=data.get("completed_at")
                )

    async def wait_for_result_async(self, task_id: str, poll_interval: float = 2.0) -> CaptchaResult:
        """Async version of wait_for_result"""
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            result = await self.get_result_async(task_id)
            
            if result.is_success or result.is_error:
                return result
            
            await asyncio.sleep(poll_interval)
        
        raise TimeoutError(f"Task {task_id} did not complete within {self.timeout} seconds")

    async def solve_turnstile_async(
        self,
        url: str,
        sitekey: Optional[str] = None,
        action: Optional[str] = None,
        cdata: Optional[str] = None,
        auto_detect: bool = True,
        poll_interval: float = 2.0
    ) -> CaptchaResult:
        """Async version of solve_turnstile"""
        task_id = await self.submit_turnstile_async(url, sitekey, action, cdata, auto_detect)
        return await self.wait_for_result_async(task_id, poll_interval)

    async def solve_recaptcha_async(
        self,
        url: str,
        sitekey: Optional[str] = None,
        auto_detect: bool = True,
        poll_interval: float = 2.0
    ) -> CaptchaResult:
        """Async version of solve_recaptcha"""
        task_id = await self.submit_recaptcha_async(url, sitekey, auto_detect)
        return await self.wait_for_result_async(task_id, poll_interval)


# Convenience functions
def solve_turnstile(api_key: str, url: str, **kwargs) -> CaptchaResult:
    """
    Convenience function to solve Turnstile CAPTCHA
    
    Args:
        api_key: Your RapidCaptcha API key
        url: Target website URL
        **kwargs: Additional arguments (sitekey, action, cdata, auto_detect, etc.)
        
    Returns:
        CaptchaResult object
        
    Example:
        >>> result = solve_turnstile("Rapidcaptcha-YOUR-KEY", "https://example.com")
        >>> print(result.turnstile_value)
    """
    client = RapidCaptchaClient(api_key)
    return client.solve_turnstile(url, **kwargs)


def solve_recaptcha(api_key: str, url: str, **kwargs) -> CaptchaResult:
    """
    Convenience function to solve reCAPTCHA
    
    Args:
        api_key: Your RapidCaptcha API key
        url: Target website URL
        **kwargs: Additional arguments (sitekey, auto_detect, etc.)
        
    Returns:
        CaptchaResult object
    """
    client = RapidCaptchaClient(api_key)
    return client.solve_recaptcha(url, **kwargs)


# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Example usage
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if api_key:
        print("🚀 Testing RapidCaptcha Python SDK")
        
        client = RapidCaptchaClient(api_key)
        
        # Health check
        try:
            health = client.health_check()
            print(f"✅ API Status: {health['status']}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            exit(1)
        
        # Test Turnstile solving
        print("\n🔄 Testing Turnstile solver...")
        try:
            result = client.solve_turnstile(
                url="https://2captcha.com/demo/cloudflare-turnstile",
                auto_detect=True
            )
            
            if result.is_success:
                print(f"✅ Turnstile solved!")
                print(f"   Token: {result.turnstile_value[:50]}...")
                print(f"   Time: {result.elapsed_time_seconds}s")
                print(f"   Sitekey used: {result.sitekey_used}")
            else:
                print(f"❌ Turnstile failed: {result.reason}")
                
        except Exception as e:
            print(f"❌ Turnstile error: {e}")
        
        # Test async (if aiohttp is available)
        if HAS_AIOHTTP:
            print("\n🔄 Testing async capabilities...")
            
            async def test_async():
                try:
                    result = await client.solve_turnstile_async(
                        url="https://2captcha.com/demo/cloudflare-turnstile",
                        auto_detect=True
                    )
                    print(f"✅ Async Turnstile: {result.is_success}")
                except Exception as e:
                    print(f"❌ Async error: {e}")
            
            asyncio.run(test_async())
        
        print("\n✅ SDK test completed!")
    else:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable for testing")
        print("   Example: export RAPIDCAPTCHA_API_KEY='Rapidcaptcha-YOUR-KEY'")