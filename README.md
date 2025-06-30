# RapidCaptcha Python SDK

[![PyPI version](https://badge.fury.io/py/rapidcaptcha.svg)](https://badge.fury.io/py/rapidcaptcha)
[![Python Support](https://img.shields.io/pypi/pyversions/rapidcaptcha.svg)](https://pypi.org/project/rapidcaptcha/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Official Python SDK for [RapidCaptcha](https://rapidcaptcha.xyz) - Fast, reliable CAPTCHA solving service with high success rates.

## 🚀 Features

- **High Success Rates**: 85-95% for Turnstile, 75-85% for reCAPTCHA
- **Fast Processing**: 10-25 second average solve time for Turnstile
- **Auto-Detection**: Automatically detect sitekeys from target websites
- **Dual API**: Both synchronous and asynchronous support
- **Type Safety**: Full type hints for better development experience
- **Error Handling**: Comprehensive error categorization and handling
- **Flexible Configuration**: Configurable timeouts, retries, and polling

## 📦 Installation

```bash
# Basic installation
pip install rapidcaptcha

# With async support
pip install rapidcaptcha[async]

# Development installation
pip install rapidcaptcha[dev]
```

## 🔑 Quick Start

### Get Your API Key

1. Sign up at [RapidCaptcha](https://rapidcaptcha.xyz)
2. Get your API key from the dashboard
3. Your API key format: `Rapidcaptcha-YOUR-API-KEY`

### Basic Usage

```python
from rapidcaptcha import RapidCaptchaClient

# Initialize client
client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

# Solve Turnstile CAPTCHA
result = client.solve_turnstile("https://example.com", auto_detect=True)

if result.is_success:
    print(f"Solved! Token: {result.turnstile_value}")
    print(f"Time taken: {result.elapsed_time_seconds}s")
else:
    print(f"Failed: {result.reason}")
```

### Convenience Functions

```python
from rapidcaptcha import solve_turnstile, solve_recaptcha

# Quick solve without creating client
result = solve_turnstile("Rapidcaptcha-YOUR-API-KEY", "https://example.com")
```

## 🔄 Async Support

```python
import asyncio
from rapidcaptcha import RapidCaptchaClient

async def solve_async():
    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

    # Async solving
    result = await client.solve_turnstile_async("https://example.com", auto_detect=True)

    if result.is_success:
        print(f"Token: {result.turnstile_value}")

# Run async function
asyncio.run(solve_async())
```

## 🛠️ Advanced Usage

### Manual Sitekey

```python
client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

result = client.solve_turnstile(
    url="https://example.com",
    sitekey="0x4AAAAAAABkMYinukE8nzKd",
    action="submit",
    auto_detect=False
)
```

### Custom Configuration

```python
client = RapidCaptchaClient(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    timeout=120,        # 2 minutes timeout
    max_retries=5,      # 5 retries for failed requests
    retry_delay=3.0     # 3 seconds between retries
)
```

### Manual Task Management

```python
# Submit task
task_id = client.submit_turnstile("https://example.com", auto_detect=True)
print(f"Task submitted: {task_id}")

# Check result manually
result = client.get_result(task_id)
if result.is_success:
    print(f"Solved: {result.turnstile_value}")

# Or wait for completion
result = client.wait_for_result(task_id, poll_interval=1.0)
```

### Concurrent Solving

```python
import asyncio

async def solve_multiple():
    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

    urls = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]

    # Solve concurrently
    tasks = [client.solve_turnstile_async(url, auto_detect=True) for url in urls]
    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        if result.is_success:
            print(f"URL {i+1}: ✅ {result.turnstile_value[:20]}...")
        else:
            print(f"URL {i+1}: ❌ {result.reason}")

asyncio.run(solve_multiple())
```

## 🛡️ Error Handling

```python
from rapidcaptcha import (
    RapidCaptchaClient, APIKeyError, RateLimitError,
    ValidationError, TaskNotFoundError, TimeoutError
)

client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

try:
    result = client.solve_turnstile("https://example.com", auto_detect=True)

    if result.is_success:
        print(f"Success: {result.turnstile_value}")
    else:
        print(f"Failed: {result.reason}")

except APIKeyError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded - please wait")
except ValidationError as e:
    print(f"Invalid parameters: {e}")
except TaskNotFoundError:
    print("Task not found")
except TimeoutError:
    print("Operation timed out")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## 📚 Supported CAPTCHA Types

### Cloudflare Turnstile

```python
# Auto-detection (recommended)
result = client.solve_turnstile("https://example.com", auto_detect=True)

# Manual sitekey
result = client.solve_turnstile(
    url="https://example.com",
    sitekey="0x4AAAAAAABkMYinukE8nzKd",
    action="submit",
    cdata="optional-cdata"
)
```

### reCAPTCHA v2

```python
# Auto-detection
result = client.solve_recaptcha("https://example.com", auto_detect=True)

# Manual sitekey
result = client.solve_recaptcha(
    url="https://example.com",
    sitekey="6Le-wvkSAAAAAPBMRTvw0Q4Muexq9bi0DJwx_mJ-"
)
```

## 📊 Result Object

The `CaptchaResult` object contains detailed information about the solving process:

```python
result = client.solve_turnstile("https://example.com", auto_detect=True)

# Status checking
print(f"Success: {result.is_success}")
print(f"Failed: {result.is_error}")
print(f"Pending: {result.is_pending}")

# Result data
print(f"Task ID: {result.task_id}")
print(f"Status: {result.status}")
print(f"Token: {result.turnstile_value}")
print(f"Time: {result.elapsed_time_seconds}s")
print(f"Sitekey used: {result.sitekey_used}")

# Error information (if failed)
if result.is_error:
    print(f"Reason: {result.reason}")
    print(f"Errors: {result.errors}")
```

## ⚙️ Configuration Options

| Parameter       | Type  | Default                    | Description                                     |
| --------------- | ----- | -------------------------- | ----------------------------------------------- |
| `api_key`       | str   | Required                   | Your RapidCaptcha API key                       |
| `base_url`      | str   | `https://rapidcaptcha.xyz` | API base URL                                    |
| `timeout`       | int   | `300`                      | Maximum time to wait for completion (seconds)   |
| `max_retries`   | int   | `3`                        | Maximum number of retries for failed requests   |
| `retry_delay`   | float | `2.0`                      | Delay between retries (seconds)                 |
| `poll_interval` | float | `2.0`                      | Polling interval for checking results (seconds) |

## 📈 Performance Tips

1. **Use Auto-Detection**: Let the API automatically detect sitekeys for better accuracy
2. **Async for Concurrency**: Use async methods when solving multiple CAPTCHAs
3. **Configure Timeouts**: Adjust timeouts based on your use case
4. **Handle Rate Limits**: Implement exponential backoff for rate limit errors
5. **Reuse Client**: Create one client instance and reuse it for multiple requests

## 🔧 Development

### Setting up Development Environment

```bash
# Clone repository
git clone https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python.git
cd RapidCaptcha-Python

# Install development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rapidcaptcha --cov-report=html

# Run async tests only
pytest tests/test_async.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black rapidcaptcha tests examples

# Lint code
flake8 rapidcaptcha tests examples

# Type checking
mypy rapidcaptcha

# Security check
bandit -r rapidcaptcha

# Check dependencies
safety check
```

## 📖 API Reference

### Client Methods

#### Synchronous Methods

- `health_check()` - Check API health
- `submit_turnstile()` - Submit Turnstile task
- `submit_recaptcha()` - Submit reCAPTCHA task
- `get_result()` - Get task result
- `wait_for_result()` - Wait for task completion
- `solve_turnstile()` - Complete Turnstile solving
- `solve_recaptcha()` - Complete reCAPTCHA solving

#### Asynchronous Methods

- `health_check_async()` - Async health check
- `submit_turnstile_async()` - Async submit Turnstile
- `submit_recaptcha_async()` - Async submit reCAPTCHA
- `get_result_async()` - Async get result
- `wait_for_result_async()` - Async wait for result
- `solve_turnstile_async()` - Async Turnstile solving
- `solve_recaptcha_async()` - Async reCAPTCHA solving

### Exception Classes

- `RapidCaptchaError` - Base exception
- `APIKeyError` - Invalid API key
- `ValidationError` - Invalid parameters
- `TaskNotFoundError` - Task not found
- `RateLimitError` - Rate limit exceeded
- `TimeoutError` - Operation timeout

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Steps to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs.rapidcaptcha.xyz](https://docs.rapidcaptcha.xyz)
- **API Reference**: [app.rapidcaptcha.xyz](https://app.rapidcaptcha.xyz)
- **GitHub Issues**: [Report bugs or request features](https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python/issues)
- **Discord**: Join our [Discord community](https://discord.gg/rapidcaptcha)
- **Email**: [support@rapidcaptcha.xyz](mailto:support@rapidcaptcha.xyz)

## 🎯 Roadmap

- [ ] Support for more CAPTCHA types (hCaptcha, GeeTest)
- [ ] Browser automation helpers
- [ ] Proxy support
- [ ] Advanced retry strategies
- [ ] Performance monitoring and metrics
- [ ] Plugin system for custom solvers

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!

---

**RapidCaptcha** - Fast, reliable, and easy-to-use CAPTCHA solving service.
