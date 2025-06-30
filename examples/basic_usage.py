import os
import time
from rapidcaptcha import RapidCaptchaClient, solve_turnstile

def basic_turnstile_example():
    """Basic Turnstile solving example"""
    print("🔄 Basic Turnstile Example")
    print("-" * 30)
    
    # Get API key from environment
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    # Initialize client
    client = RapidCaptchaClient(api_key)
    
    # Health check
    try:
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Solve Turnstile with auto-detection
    try:
        print("\n🔍 Solving Turnstile with auto-detection...")
        result = client.solve_turnstile(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
            print(f"   Sitekey used: {result.sitekey_used}")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def manual_sitekey_example():
    """Manual sitekey example"""
    print("\n🔧 Manual Sitekey Example")
    print("-" * 30)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        print("🔍 Solving Turnstile with manual sitekey...")
        result = client.solve_turnstile(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            sitekey="3x00000000000000000000FF",  # Demo sitekey
            action="submit",
            auto_detect=False
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def convenience_function_example():
    """Convenience function example"""
    print("\n⚡ Convenience Function Example")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    try:
        print("🔍 Using convenience function...")
        result = solve_turnstile(
            api_key=api_key,
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def manual_task_management_example():
    """Manual task management example"""
    print("\n🎛️ Manual Task Management Example")
    print("-" * 40)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        # Submit task
        print("📤 Submitting task...")
        task_id = client.submit_turnstile(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        print(f"✅ Task submitted: {task_id}")
        
        # Poll for result manually
        print("🔄 Polling for result...")
        attempt = 0
        while attempt < 30:  # Max 30 attempts (60 seconds)
            attempt += 1
            time.sleep(2)
            
            result = client.get_result(task_id)
            print(f"   Attempt {attempt}: {result.status}")
            
            if result.is_success:
                print(f"✅ Success!")
                print(f"   Token: {result.turnstile_value[:50]}...")
                print(f"   Time: {result.elapsed_time_seconds}s")
                break
            elif result.is_error:
                print(f"❌ Failed: {result.reason}")
                break
        else:
            print("⏰ Timeout: Task didn't complete in 60 seconds")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def custom_configuration_example():
    """Custom configuration example"""
    print("\n⚙️ Custom Configuration Example")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    # Custom client configuration
    client = RapidCaptchaClient(
        api_key=api_key,
        timeout=120,        # 2 minutes timeout
        max_retries=5,      # 5 retries for failed requests
        retry_delay=3.0     # 3 seconds between retries
    )
    
    try:
        print("🔍 Solving with custom configuration...")
        result = client.solve_turnstile(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True,
            poll_interval=1.0  # Poll every 1 second
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🚀 RapidCaptcha Python SDK - Basic Usage Examples")
    print("=" * 55)
    
    # Run all examples
    basic_turnstile_example()
    manual_sitekey_example()
    convenience_function_example()
    manual_task_management_example()
    custom_configuration_example()
    
    print("\n✅ All examples completed!")
    print("\nTip: Set RAPIDCAPTCHA_API_KEY environment variable to test with real API")