# API Reference

## Client Class

### RapidCaptchaClient

Main client class for interacting with RapidCaptcha API.

```python
class RapidCaptchaClient:
    def __init__(
        self,
        api_key: str,
        base_url: str = "https://rapidcaptcha.xyz",
        timeout: int = 300,
        max_retries: int = 3,
        retry_delay: float = 2.0
    )
```

#### Parameters

- **api_key** (str): Your RapidCaptcha API key (must start with 'Rapidcaptcha-')
- **base_url** (str, optional): API base URL. Defaults to "https://rapidcaptcha.xyz"
- **timeout** (int, optional): Maximum time to wait for task completion in seconds. Defaults to 300
- **max_retries** (int, optional): Maximum number of retries for failed requests. Defaults to 3
- **retry_delay** (float, optional): Delay between retries in seconds. Defaults to 2.0

#### Raises

- **APIKeyError**: If API key format is invalid

#### Example

```python
client = RapidCaptchaClient(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    timeout=120,
    max_retries=5
)
```

## Synchronous Methods

### health_check()

Check API health status.

```python
def health_check(self) -> Dict
```

#### Returns

Dict containing API health information

#### Raises

- **ImportError**: If requests library is not installed
- **APIKeyError**: If API key is invalid
- **RapidCaptchaError**: If API returns an error

#### Example

```python
health = client.health_check()
print(health["status"])  # "ok"
```

### submit_turnstile()

Submit Turnstile solving task.

```python
def submit_turnstile(
    self,
    url: str,
    sitekey: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
    auto_detect: bool = True
) -> str
```

#### Parameters

- **url** (str): Target website URL
- **sitekey** (str, optional): Turnstile sitekey
- **action** (str, optional): Turnstile action parameter
- **cdata** (str, optional): Turnstile cdata parameter
- **auto_detect** (bool, optional): Enable auto-detection of sitekey. Defaults to True

#### Returns

Task ID string

#### Raises

- **ValidationError**: If parameters are invalid
- **APIKeyError**: If API key is invalid
- **RateLimitError**: If rate limit is exceeded

#### Example

```python
task_id = client.submit_turnstile(
    url="https://example.com",
    sitekey="0x4AAAAAAABkMYinukE8nzKd",
    action="submit"
)
```

### submit_recaptcha()

Submit reCAPTCHA solving task.

```python
def submit_recaptcha(
    self,
    url: str,
    sitekey: Optional[str] = None,
    auto_detect: bool = True
) -> str
```

#### Parameters

- **url** (str): Target website URL
- **sitekey** (str, optional): reCAPTCHA sitekey
- **auto_detect** (bool, optional): Enable auto-detection of sitekey. Defaults to True

#### Returns

Task ID string

#### Example

```python
task_id = client.submit_recaptcha(
    url="https://example.com",
    auto_detect=True
)
```

### get_result()

Get task result by task ID.

```python
def get_result(self, task_id: str) -> CaptchaResult
```

#### Parameters

- **task_id** (str): Task ID returned from submit methods

#### Returns

CaptchaResult object

#### Raises

- **TaskNotFoundError**: If task is not found
- **ValidationError**: If task_id is invalid

#### Example

```python
result = client.get_result("task-123")
if result.is_success:
    print(result.turnstile_value)
```

### wait_for_result()

Wait for task completion and return result.

```python
def wait_for_result(self, task_id: str, poll_interval: float = 2.0) -> CaptchaResult
```

#### Parameters

- **task_id** (str): Task ID to wait for
- **poll_interval** (float, optional): Polling interval in seconds. Defaults to 2.0

#### Returns

CaptchaResult object when completed

#### Raises

- **TimeoutError**: If task doesn't complete within timeout

#### Example

```python
result = client.wait_for_result("task-123", poll_interval=1.0)
```

### solve_turnstile()

Solve Turnstile CAPTCHA (submit + wait for result).

```python
def solve_turnstile(
    self,
    url: str,
    sitekey: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
    auto_detect: bool = True,
    poll_interval: float = 2.0
) -> CaptchaResult
```

#### Parameters

- **url** (str): Target website URL
- **sitekey** (str, optional): Turnstile sitekey
- **action** (str, optional): Turnstile action parameter
- **cdata** (str, optional): Turnstile cdata parameter
- **auto_detect** (bool, optional): Enable auto-detection of sitekey. Defaults to True
- **poll_interval** (float, optional): Polling interval in seconds. Defaults to 2.0

#### Returns

CaptchaResult object

#### Example

```python
result = client.solve_turnstile(
    url="https://example.com",
    auto_detect=True,
    poll_interval=1.0
)

if result.is_success:
    print(f"Solved: {result.turnstile_value}")
else:
    print(f"Failed: {result.reason}")
```

### solve_recaptcha()

Solve reCAPTCHA (submit + wait for result).

```python
def solve_recaptcha(
    self,
    url: str,
    sitekey: Optional[str] = None,
    auto_detect: bool = True,
    poll_interval: float = 2.0
) -> CaptchaResult
```

#### Parameters

- **url** (str): Target website URL
- **sitekey** (str, optional): reCAPTCHA sitekey
- **auto_detect** (bool, optional): Enable auto-detection of sitekey. Defaults to True
- **poll_interval** (float, optional): Polling interval in seconds. Defaults to 2.0

#### Returns

CaptchaResult object

#### Example

```python
result = client.solve_recaptcha(
    url="https://example.com",
    auto_detect=True
)
```

## Asynchronous Methods

All synchronous methods have asynchronous counterparts with `_async` suffix.

### health_check_async()

Async version of health_check().

```python
async def health_check_async(self) -> Dict
```

#### Example

```python
health = await client.health_check_async()
```

### submit_turnstile_async()

Async version of submit_turnstile().

```python
async def submit_turnstile_async(
    self,
    url: str,
    sitekey: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
    auto_detect: bool = True
) -> str
```

### submit_recaptcha_async()

Async version of submit_recaptcha().

```python
async def submit_recaptcha_async(
    self,
    url: str,
    sitekey: Optional[str] = None,
    auto_detect: bool = True
) -> str
```

### get_result_async()

Async version of get_result().

```python
async def get_result_async(self, task_id: str) -> CaptchaResult
```

### wait_for_result_async()

Async version of wait_for_result().

```python
async def wait_for_result_async(
    self,
    task_id: str,
    poll_interval: float = 2.0
) -> CaptchaResult
```

### solve_turnstile_async()

Async version of solve_turnstile().

```python
async def solve_turnstile_async(
    self,
    url: str,
    sitekey: Optional[str] = None,
    action: Optional[str] = None,
    cdata: Optional[str] = None,
    auto_detect: bool = True,
    poll_interval: float = 2.0
) -> CaptchaResult
```

#### Example

```python
result = await client.solve_turnstile_async(
    url="https://example.com",
    auto_detect=True
)
```

### solve_recaptcha_async()

Async version of solve_recaptcha().

```python
async def solve_recaptcha_async(
    self,
    url: str,
    sitekey: Optional[str] = None,
    auto_detect: bool = True,
    poll_interval: float = 2.0
) -> CaptchaResult
```

## Result Classes

### CaptchaResult

Result object for CAPTCHA solving operations.

```python
@dataclass
class CaptchaResult:
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
```

#### Properties

- **is_success** (bool): Check if the solve was successful
- **is_error** (bool): Check if the solve failed
- **is_pending** (bool): Check if the solve is still pending

#### Methods

- \***\*str**()\*\*: String representation of the result

#### Example

```python
result = client.solve_turnstile("https://example.com")

print(f"Success: {result.is_success}")
print(f"Task ID: {result.task_id}")
print(f"Status: {result.status}")

if result.is_success:
    print(f"Token: {result.turnstile_value}")
    print(f"Time: {result.elapsed_time_seconds}s")
    print(f"Sitekey: {result.sitekey_used}")
elif result.is_error:
    print(f"Reason: {result.reason}")
    print(f"Errors: {result.errors}")
```

## Enums

### TaskStatus

Enumeration of task statuses.

```python
class TaskStatus(Enum):
    PENDING = "pending"
    SUCCESS = "success"
    ERROR = "error"
```

### CaptchaType

Enumeration of supported CAPTCHA types.

```python
class CaptchaType(Enum):
    TURNSTILE = "turnstile"
    RECAPTCHA = "recaptcha"
```

## Exception Classes

### RapidCaptchaError

Base exception for RapidCaptcha errors.

```python
class RapidCaptchaError(Exception):
    pass
```

### APIKeyError

Raised when API key is invalid or missing.

```python
class APIKeyError(RapidCaptchaError):
    pass
```

### ValidationError

Raised when request parameters are invalid.

```python
class ValidationError(RapidCaptchaError):
    pass
```

### TaskNotFoundError

Raised when task ID is not found.

```python
class TaskNotFoundError(RapidCaptchaError):
    pass
```

### RateLimitError

Raised when rate limit is exceeded.

```python
class RateLimitError(RapidCaptchaError):
    pass
```

### TimeoutError

Raised when operation times out.

```python
class TimeoutError(RapidCaptchaError):
    pass
```

#### Exception Handling Example

```python
from rapidcaptcha import (
    RapidCaptchaClient, APIKeyError, RateLimitError,
    ValidationError, TaskNotFoundError, TimeoutError
)

client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

try:
    result = client.solve_turnstile("https://example.com", auto_detect=True)
    print(f"Success: {result.turnstile_value}")

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

## Convenience Functions

### solve_turnstile()

Convenience function to solve Turnstile CAPTCHA without creating a client instance.

```python
def solve_turnstile(api_key: str, url: str, **kwargs) -> CaptchaResult
```

#### Parameters

- **api_key** (str): Your RapidCaptcha API key
- **url** (str): Target website URL
- **kwargs**: Additional arguments (sitekey, action, cdata, auto_detect, etc.)

#### Returns

CaptchaResult object

#### Example

```python
from rapidcaptcha import solve_turnstile

result = solve_turnstile(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    url="https://example.com",
    auto_detect=True
)
```

### solve_recaptcha()

Convenience function to solve reCAPTCHA without creating a client instance.

```python
def solve_recaptcha(api_key: str, url: str, **kwargs) -> CaptchaResult
```

#### Parameters

- **api_key** (str): Your RapidCaptcha API key
- **url** (str): Target website URL
- **kwargs**: Additional arguments (sitekey, auto_detect, etc.)

#### Returns

CaptchaResult object

#### Example

```python
from rapidcaptcha import solve_recaptcha

result = solve_recaptcha(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    url="https://example.com",
    auto_detect=True
)
```

## Configuration Options

### Client Configuration

| Parameter     | Type  | Default                    | Description                                   |
| ------------- | ----- | -------------------------- | --------------------------------------------- |
| `api_key`     | str   | Required                   | Your RapidCaptcha API key                     |
| `base_url`    | str   | `https://rapidcaptcha.xyz` | API base URL                                  |
| `timeout`     | int   | `300`                      | Maximum time to wait for completion (seconds) |
| `max_retries` | int   | `3`                        | Maximum number of retries for failed requests |
| `retry_delay` | float | `2.0`                      | Delay between retries (seconds)               |

### Method Parameters

| Parameter       | Type  | Default  | Description                                 |
| --------------- | ----- | -------- | ------------------------------------------- |
| `url`           | str   | Required | Target website URL                          |
| `sitekey`       | str   | None     | CAPTCHA sitekey (optional with auto_detect) |
| `action`        | str   | None     | Turnstile action parameter                  |
| `cdata`         | str   | None     | Turnstile cdata parameter                   |
| `auto_detect`   | bool  | True     | Enable automatic sitekey detection          |
| `poll_interval` | float | 2.0      | Polling interval for result checking        |

## Advanced Usage

### Custom Headers

The client automatically sets appropriate headers:

```python
headers = {
    "X-API-Key": self.api_key,
    "Content-Type": "application/json",
    "User-Agent": f"RapidCaptcha-Python-SDK/{__version__}"
}
```

### Timeout Configuration

```python
# Configure different timeouts
client = RapidCaptchaClient(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    timeout=120  # 2 minutes for task completion
)

# Per-request timeout
result = client.solve_turnstile(
    url="https://example.com",
    poll_interval=1.0  # Check every 1 second
)
```

### Retry Logic

```python
# Configure retry behavior
client = RapidCaptchaClient(
    api_key="Rapidcaptcha-YOUR-API-KEY",
    max_retries=5,      # Try up to 5 times
    retry_delay=3.0     # Wait 3 seconds between retries
)
```

### Async Context Manager Pattern

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
    tasks = [
        client.solve_turnstile_async(url, auto_detect=True)
        for url in urls
    ]

    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        if result.is_success:
            print(f"URL {i+1}: ✅ {result.turnstile_value[:20]}...")
        else:
            print(f"URL {i+1}: ❌ {result.reason}")

# Run the async function
asyncio.run(solve_multiple())
```

## Error Handling Best Practices

### Comprehensive Error Handling

```python
import time
from rapidcaptcha import *

def robust_solve(url: str, max_attempts: int = 3):
    """Solve CAPTCHA with robust error handling and retries"""

    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

    for attempt in range(max_attempts):
        try:
            result = client.solve_turnstile(url, auto_detect=True)

            if result.is_success:
                return result
            else:
                print(f"Attempt {attempt + 1} failed: {result.reason}")

        except RateLimitError:
            wait_time = 60 * (2 ** attempt)  # Exponential backoff
            print(f"Rate limited, waiting {wait_time}s...")
            time.sleep(wait_time)

        except (APIKeyError, ValidationError) as e:
            print(f"Configuration error: {e}")
            break  # Don't retry configuration errors

        except TimeoutError:
            print(f"Timeout on attempt {attempt + 1}")

        except Exception as e:
            print(f"Unexpected error: {e}")

        if attempt < max_attempts - 1:
            time.sleep(5)  # Wait before retry

    return None
```

### Logging Integration

```python
import logging
from rapidcaptcha import RapidCaptchaClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

try:
    logger.info("Starting CAPTCHA solve...")
    result = client.solve_turnstile("https://example.com", auto_detect=True)

    if result.is_success:
        logger.info(f"CAPTCHA solved in {result.elapsed_time_seconds}s")
        logger.debug(f"Token: {result.turnstile_value[:20]}...")
    else:
        logger.warning(f"CAPTCHA solve failed: {result.reason}")

except Exception as e:
    logger.error(f"CAPTCHA solve error: {e}", exc_info=True)
```

## Performance Optimization

### Concurrent Processing

```python
import asyncio
from rapidcaptcha import RapidCaptchaClient

async def process_batch(urls, concurrency_limit=5):
    """Process multiple URLs with concurrency limit"""

    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")
    semaphore = asyncio.Semaphore(concurrency_limit)

    async def solve_with_limit(url):
        async with semaphore:
            return await client.solve_turnstile_async(url, auto_detect=True)

    # Process all URLs concurrently with limit
    tasks = [solve_with_limit(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results
    successful = []
    failed = []

    for url, result in zip(urls, results):
        if isinstance(result, Exception):
            failed.append((url, str(result)))
        elif result.is_success:
            successful.append((url, result.turnstile_value))
        else:
            failed.append((url, result.reason))

    return successful, failed
```

### Connection Reuse

The client automatically reuses connections when using the same instance:

```python
# Good: Reuse client instance
client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")

for url in urls:
    result = client.solve_turnstile(url, auto_detect=True)
    # Process result...

# Avoid: Creating new client for each request
for url in urls:
    client = RapidCaptchaClient("Rapidcaptcha-YOUR-API-KEY")  # Inefficient
    result = client.solve_turnstile(url, auto_detect=True)
```

## Version Information

```python
import rapidcaptcha

print(f"SDK Version: {rapidcaptcha.__version__}")
print(f"Author: {rapidcaptcha.__author__}")
print(f"Email: {rapidcaptcha.__email__}")
```

## Support and Resources

- **Documentation**: [docs.rapidcaptcha.xyz](https://docs.rapidcaptcha.xyz)
- **API Dashboard**: [app.rapidcaptcha.xyz](https://app.rapidcaptcha.xyz)
- **GitHub Repository**: [RapidCaptcha-Python](https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python)
- **Issue Tracker**: [GitHub Issues](https://github.com/RapidCaptcha-SDK/RapidCaptcha-Python/issues)
- **Email Support**: [support@rapidcaptcha.xyz](mailto:support@rapidcaptcha.xyz)
