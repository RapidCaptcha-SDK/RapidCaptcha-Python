"""
RapidCaptcha Python SDK
Official Python client for RapidCaptcha API
"""

__version__ = "1.0.0"
__author__ = "RapidCaptcha Team"
__email__ = "support@rapidcaptcha.com"

from .client import (
    RapidCaptchaClient,
    CaptchaResult,
    CaptchaType,
    TaskStatus,
    RapidCaptchaError,
    APIKeyError,
    TaskNotFoundError,
    ValidationError,
    RateLimitError,
    TimeoutError,
    solve_turnstile,
    solve_recaptcha,
)

__all__ = [
    "RapidCaptchaClient",
    "CaptchaResult", 
    "CaptchaType",
    "TaskStatus",
    "RapidCaptchaError",
    "APIKeyError",
    "TaskNotFoundError",
    "ValidationError",
    "RateLimitError",
    "TimeoutError",
    "solve_turnstile",
    "solve_recaptcha",
]