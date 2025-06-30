import os
import time
from typing import Optional
from rapidcaptcha import (
    RapidCaptchaClient, CaptchaResult,
    RapidCaptchaError, APIKeyError, TaskNotFoundError,
    ValidationError, RateLimitError, TimeoutError
)

def basic_error_handling_example():
    """Basic error handling example"""
    print("🛡️ Basic Error Handling Example")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY", "invalid-key")
    
    try:
        # This will raise APIKeyError due to invalid format
        client = RapidCaptchaClient("invalid-key-format")
        result = client.health_check()
        
    except APIKeyError as e:
        print(f"✅ Caught API key error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def comprehensive_error_handling_example():
    """Comprehensive error handling example"""
    print("\n🛡️ Comprehensive Error Handling")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    # Test different error scenarios
    test_cases = [
        {
            "name": "Invalid URL",
            "func": lambda: client.solve_turnstile("invalid-url"),
            "expected": ValidationError
        },
        {
            "name": "Empty URL",
            "func": lambda: client.solve_turnstile(""),
            "expected": ValidationError
        },
        {
            "name": "No sitekey and auto_detect=False",
            "func": lambda: client.solve_turnstile("https://example.com", auto_detect=False),
            "expected": ValidationError
        }
    ]
    
    for test in test_cases:
        try:
            print(f"\n🧪 Testing: {test['name']}")
            test["func"]()
            print(f"   ❌ Expected {test['expected'].__name__} but got no error")
        except test["expected"] as e:
            print(f"   ✅ Correctly caught {test['expected'].__name__}: {e}")
        except Exception as e:
            print(f"   ⚠️ Got unexpected error {type(e).__name__}: {e}")

def robust_solving_with_retries():
    """Robust solving with retry logic"""
    print("\n🔄 Robust Solving with Retries")
    print("-" * 35)
    
    def solve_with_retries(
        url: str, 
        max_attempts: int = 3,
        backoff_factor: float = 2.0
    ) -> Optional[CaptchaResult]:
        """
        Solve CAPTCHA with retry logic and exponential backoff
        
        Args:
            url: Target URL
            max_attempts: Maximum retry attempts
            backoff_factor: Multiplier for delay between retries
            
        Returns:
            CaptchaResult if successful, None if all attempts failed
        """
        api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
        if not api_key:
            print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
            return None
        
        client = RapidCaptchaClient(api_key)
        
        for attempt in range(max_attempts):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_attempts}")
                
                result = client.solve_turnstile(url, auto_detect=True)
                
                if result.is_success:
                    print(f"✅ Success on attempt {attempt + 1}")
                    return result
                else:
                    print(f"❌ Failed: {result.reason}")
                
            except RateLimitError:
                wait_time = 60 * backoff_factor ** attempt
                print(f"⏱️ Rate limited, waiting {wait_time:.0f}s...")
                time.sleep(wait_time)
                
            except (APIKeyError, ValidationError) as e:
                print(f"❌ Configuration error (won't retry): {e}")
                break
                
            except TimeoutError:
                print(f"⏰ Timeout on attempt {attempt + 1}")
                
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
            
            # Wait before next attempt (except for last attempt)
            if attempt < max_attempts - 1:
                wait_time = 5 * backoff_factor ** attempt
                print(f"⏱️ Waiting {wait_time:.0f}s before retry...")
                time.sleep(wait_time)
        
        print(f"❌ All {max_attempts} attempts failed")
        return None
    
    # Test the robust solving function
    result = solve_with_retries("https://2captcha.com/demo/cloudflare-turnstile")
    
    if result:
        print(f"🎉 Final result: Success!")
        print(f"   Token: {result.turnstile_value[:50]}...")
    else:
        print("💔 Could not solve after all retries")

def task_not_found_handling():
    """Handle TaskNotFoundError"""
    print("\n🔍 Task Not Found Handling")
    print("-" * 30)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        # Try to get result for non-existent task
        print("🔍 Trying to get result for invalid task ID...")
        result = client.get_result("invalid-task-id")
        print(f"❌ Expected TaskNotFoundError but got: {result}")
        
    except TaskNotFoundError as e:
        print(f"✅ Correctly caught TaskNotFoundError: {e}")
    except Exception as e:
        print(f"⚠️ Got unexpected error: {e}")

def timeout_handling_example():
    """Timeout handling example"""
    print("\n⏰ Timeout Handling Example")
    print("-" * 30)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    # Create client with very short timeout
    client = RapidCaptchaClient(api_key, timeout=5)  # 5 second timeout
    
    try:
        print("⏰ Solving with very short timeout (5s)...")
        result = client.solve_turnstile(
            "https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        if result.is_success:
            print(f"✅ Surprisingly fast success: {result.elapsed_time_seconds}s")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except TimeoutError as e:
        print(f"✅ Correctly caught TimeoutError: {e}")
    except Exception as e:
        print(f"⚠️ Got unexpected error: {e}")

def network_error_simulation():
    """Simulate network errors"""
    print("\n🌐 Network Error Simulation")
    print("-" * 30)
    
    # Test with invalid base URL
    try:
        print("🌐 Testing with invalid base URL...")
        client = RapidCaptchaClient(
            api_key="Rapidcaptcha-test-key",
            base_url="https://invalid-domain-that-does-not-exist.com"
        )
        
        result = client.health_check()
        print(f"❌ Expected network error but got: {result}")
        
    except Exception as e:
        print(f"✅ Correctly caught network error: {type(e).__name__}: {e}")

def error_information_extraction():
    """Extract detailed error information"""
    print("\n📋 Error Information Extraction")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        # Submit a task and get detailed result
        print("📤 Submitting task...")
        task_id = client.submit_turnstile(
            "https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        print(f"✅ Task submitted: {task_id}")
        
        # Wait for result and check for detailed error info
        result = client.wait_for_result(task_id)
        
        print("📋 Detailed result information:")
        print(f"   Status: {result.status}")
        print(f"   Task ID: {result.task_id}")
        
        if result.is_success:
            print(f"   ✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
            print(f"   Sitekey used: {result.sitekey_used}")
            if result.sitekeys_tried:
                print(f"   Sitekeys tried: {len(result.sitekeys_tried)}")
        else:
            print(f"   ❌ Failed!")
            print(f"   Reason: {result.reason}")
            if result.errors:
                print(f"   Errors: {result.errors}")
            if result.sitekeys_tried:
                print(f"   Sitekeys tried: {result.sitekeys_tried}")
        
        if result.completed_at:
            print(f"   Completed at: {result.completed_at}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        
        # Extract additional error information if available
        if hasattr(e, 'response'):
            print(f"   HTTP Status: {e.response.status_code}")
        if hasattr(e, '__cause__'):
            print(f"   Cause: {e.__cause__}")

def main():
    """Main function to run all error handling examples"""
    print("🚀 RapidCaptcha Python SDK - Error Handling Examples")
    print("=" * 60)
    
    # Run all error handling examples
    basic_error_handling_example()
    comprehensive_error_handling_example()
    robust_solving_with_retries()
    task_not_found_handling()
    timeout_handling_example()
    network_error_simulation()
    error_information_extraction()
    
    print("\n✅ All error handling examples completed!")
    print("\n💡 Key Takeaways:")
    print("   • Always handle specific exception types")
    print("   • Implement retry logic for transient errors")
    print("   • Use exponential backoff for rate limits")
    print("   • Extract detailed error information when available")
    print("   • Don't retry configuration errors (API key, validation)")

if __name__ == "__main__":
    main()