# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2024-01-15

### Added

- Initial release of RapidCaptcha Python SDK
- Turnstile CAPTCHA solver with auto-detection support
- reCAPTCHA v2 solver with audio challenge method
- Full async/await support with aiohttp
- Synchronous API using requests
- Comprehensive error handling with custom exceptions
- Type hints and dataclass-based result objects
- Auto-detection of sitekeys from web pages
- Support for action and cdata parameters (Turnstile)
- Configurable timeouts and retry logic
- Convenience functions for quick solving
- Complete test coverage
- Documentation and examples

### Features

- **High Success Rates**: 85-95% for Turnstile, 75-85% for reCAPTCHA
- **Fast Processing**: 10-25 second average solve time for Turnstile
- **Auto-Detection**: Automatically detect sitekeys from target websites
- **Dual API**: Both synchronous and asynchronous support
- **Type Safety**: Full type hints for better development experience
- **Error Handling**: Comprehensive error categorization and handling
- **Flexible Configuration**: Configurable timeouts, retries, and polling

### Technical Details

- **Python Support**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Dependencies**: requests (sync), aiohttp (async)
- **Architecture**: Clean separation between sync and async operations
- **Testing**: 90%+ code coverage with pytest
- **CI/CD**: GitHub Actions for testing and publishing
- **Security**: Bandit security scanning, Safety dependency checking

### API Endpoints

- `POST /api/solve/turnstile` - Submit Turnstile solving task
- `POST /api/solve/recaptcha` - Submit reCAPTCHA solving task
- `GET /api/result/{task_id}` - Get task result
- `GET /` - Health check

### Examples

```python
from rapidcaptcha import RapidCaptchaClient

# Basic usage
client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")
result = client.solve_turnstile("https://example.com", auto_detect=True)

# Async usage
result = await client.solve_turnstile_async("https://example.com", auto_detect=True)

# Convenience function
from rapidcaptcha import solve_turnstile
result = solve_turnstile("Rapidcaptcha-YOUR-API-KEY", "https://example.com")
```
