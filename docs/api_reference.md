# API Reference

Complete API reference for RapidCaptcha Python SDK.

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
