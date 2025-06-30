import os
import asyncio
import time
from rapidcaptcha import RapidCaptchaClient

async def basic_async_example():
    """Basic async solving example"""
    print("🔄 Basic Async Example")
    print("-" * 25)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        # Async health check
        print("🏥 Checking API health...")
        health = await client.health_check_async()
        print(f"✅ API Status: {health['status']}")
        
        # Async Turnstile solving
        print("\n🔍 Solving Turnstile asynchronously...")
        result = await client.solve_turnstile_async(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def concurrent_solving_example():
    """Concurrent solving example"""
    print("\n⚡ Concurrent Solving Example")
    print("-" * 32)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    # URLs to solve concurrently
    urls = [
        "https://2captcha.com/demo/cloudflare-turnstile",
        "https://2captcha.com/demo/cloudflare-turnstile",
        "https://2captcha.com/demo/cloudflare-turnstile"
    ]
    
    print(f"🚀 Starting {len(urls)} concurrent solves...")
    start_time = time.time()
    
    try:
        # Create tasks for concurrent execution
        tasks = [
            client.solve_turnstile_async(url, auto_detect=True)
            for url in urls
        ]
        
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        end_time = time.time()
        
        # Process results
        successful = 0
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                print(f"   Task {i}: ❌ Error: {result}")
            elif result.is_success:
                print(f"   Task {i}: ✅ Success ({result.elapsed_time_seconds}s)")
                successful += 1
            else:
                print(f"   Task {i}: ❌ Failed: {result.reason}")
        
        print(f"\n📊 Results: {successful}/{len(urls)} successful")
        print(f"⏱️ Total time: {end_time - start_time:.1f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def manual_async_task_management():
    """Manual async task management"""
    print("\n🎛️ Manual Async Task Management")
    print("-" * 35)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    try:
        # Submit task asynchronously
        print("📤 Submitting task asynchronously...")
        task_id = await client.submit_turnstile_async(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        print(f"✅ Task submitted: {task_id}")
        
        # Poll for result asynchronously
        print("🔄 Polling for result asynchronously...")
        result = await client.wait_for_result_async(task_id, poll_interval=1.0)
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
            print(f"   Time: {result.elapsed_time_seconds}s")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

async def async_with_error_handling():
    """Async example with comprehensive error handling"""
    print("\n🛡️ Async with Error Handling")
    print("-" * 30)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    from rapidcaptcha import (
        APIKeyError, RateLimitError, ValidationError,
        TaskNotFoundError, TimeoutError
    )
    
    try:
        print("🔍 Solving with error handling...")
        result = await client.solve_turnstile_async(
            url="https://2captcha.com/demo/cloudflare-turnstile",
            auto_detect=True
        )
        
        if result.is_success:
            print(f"✅ Success!")
            print(f"   Token: {result.turnstile_value[:50]}...")
        else:
            print(f"❌ Failed: {result.reason}")
            
    except APIKeyError:
        print("❌ Invalid API key")
    except RateLimitError:
        print("❌ Rate limit exceeded - please wait")
    except ValidationError as e:
        print(f"❌ Invalid parameters: {e}")
    except TaskNotFoundError:
        print("❌ Task not found")
    except TimeoutError:
        print("❌ Operation timed out")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

async def batch_processing_example():
    """Batch processing with semaphore for rate limiting"""
    print("\n📦 Batch Processing Example")
    print("-" * 30)
    
    api_key = os.getenv("RAPIDCAPTCHA_API_KEY")
    if not api_key:
        print("❌ Please set RAPIDCAPTCHA_API_KEY environment variable")
        return
    
    client = RapidCaptchaClient(api_key)
    
    # Simulate multiple URLs to process
    urls = [
        "https://2captcha.com/demo/cloudflare-turnstile"
    ] * 5  # 5 identical URLs for demo
    
    # Semaphore to limit concurrent requests (respect API limits)
    semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
    
    async def solve_with_semaphore(url):
        """Solve with semaphore to respect rate limits"""
        async with semaphore:
            try:
                result = await client.solve_turnstile_async(url, auto_detect=True)
                return result
            except Exception as e:
                print(f"❌ Error solving {url}: {e}")
                return None
    
    print(f"🚀 Processing {len(urls)} URLs with rate limiting...")
    start_time = time.time()
    
    try:
        # Process all URLs with rate limiting
        results = await asyncio.gather(*[
            solve_with_semaphore(url) for url in urls
        ])
        
        end_time = time.time()
        
        # Count successful results
        successful = sum(1 for r in results if r and r.is_success)
        
        print(f"📊 Batch complete:")
        print(f"   ✅ Successful: {successful}/{len(urls)}")
        print(f"   ⏱️ Total time: {end_time - start_time:.1f}s")
        print(f"   📈 Rate: {len(urls)/(end_time - start_time):.1f} solves/second")
        
    except Exception as e:
        print(f"❌ Batch processing error: {e}")

async def main():
    """Main async function to run all examples"""
    print("🚀 RapidCaptcha Python SDK - Async Usage Examples")
    print("=" * 55)
    
    # Run all async examples
    await basic_async_example()
    await concurrent_solving_example()
    await manual_async_task_management()
    await async_with_error_handling()
    await batch_processing_example()
    
    print("\n✅ All async examples completed!")

if __name__ == "__main__":
    try:
        # Check if aiohttp is available
        import aiohttp
        asyncio.run(main())
    except ImportError:
        print("❌ aiohttp is required for async examples")
        print("Install with: pip install aiohttp")
        print("Or install with async support: pip install rapidcaptcha[async]")