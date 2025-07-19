#!/usr/bin/env python3
"""Test the rate limiter implementation."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gemini_repl.utils.rate_limiter import RateLimiter, GlobalRateLimiter


def test_basic_rate_limiting():
    """Test basic rate limiting functionality."""
    print("🧪 Testing Basic Rate Limiting")
    print("=" * 50)
    
    # Create limiter for a model with 10 RPM limit
    limiter = RateLimiter("gemini-2.5-flash")
    
    print(f"Model: {limiter.model_name}")
    print(f"RPM Limit: {limiter.rpm_limit}")
    print(f"Effective Limit (90%): {int(limiter.rpm_limit * limiter.safety_margin)}")
    
    # Simulate requests
    print("\n📊 Simulating requests...")
    for i in range(12):
        wait_time = limiter.wait_if_needed()
        
        if wait_time > 0:
            print(f"\n⚠️  Request #{i+1} - Need to wait {wait_time:.1f}s")
            limiter.wait_with_display()
        else:
            print(f"✅ Request #{i+1} - No wait needed")
            limiter.record_request()
            
        # Show status
        status = limiter.get_status()
        print(f"   Status: {status['current_rpm']}/{status['effective_limit']} RPM ({status['percentage']:.1f}%)")
        
        # Small delay to simulate request processing
        time.sleep(0.5)
    
    print("\n✅ Basic rate limiting test complete!")


def test_global_limiter():
    """Test the global rate limiter singleton."""
    print("\n\n🧪 Testing Global Rate Limiter")
    print("=" * 50)
    
    # Get limiter instances
    limiter1 = GlobalRateLimiter.get_limiter("gemini-2.0-flash-lite")
    limiter2 = GlobalRateLimiter.get_limiter("gemini-2.0-flash-lite")
    
    print(f"Limiter 1 ID: {id(limiter1)}")
    print(f"Limiter 2 ID: {id(limiter2)}")
    print(f"Same instance? {limiter1 is limiter2}")
    
    # Test status bar
    print("\n📊 Status Bar Examples:")
    
    # Simulate different usage levels
    for i in range(0, 28, 5):
        # Clear and add requests
        limiter1.request_times.clear()
        for _ in range(i):
            limiter1.record_request()
        
        status_bar = GlobalRateLimiter.get_status_bar()
        print(f"   {i} requests: {status_bar}")
    
    print("\n✅ Global limiter test complete!")


def test_model_switching():
    """Test switching between different models."""
    print("\n\n🧪 Testing Model Switching")
    print("=" * 50)
    
    models = [
        "gemini-2.0-flash-lite",  # 30 RPM
        "gemini-2.0-flash",       # 15 RPM
        "gemini-2.5-flash",       # 10 RPM
    ]
    
    for model in models:
        limiter = GlobalRateLimiter.get_limiter(model)
        status = limiter.get_status()
        
        print(f"\n📋 Model: {model}")
        print(f"   Limit: {status['limit_rpm']} RPM")
        print(f"   Effective: {status['effective_limit']} RPM")
        print(f"   Status Bar: {GlobalRateLimiter.get_status_bar()}")
    
    print("\n✅ Model switching test complete!")


def test_real_scenario():
    """Simulate a real usage scenario."""
    print("\n\n🧪 Testing Real Usage Scenario")
    print("=" * 50)
    
    # Use the recommended model
    limiter = GlobalRateLimiter.get_limiter("gemini-2.0-flash-lite")
    
    print("Simulating rapid REPL usage...")
    print("(Making 35 requests to exceed 30 RPM limit)\n")
    
    start_time = time.time()
    
    for i in range(35):
        # Check if we need to wait
        if limiter.wait_with_display():
            print(f"⏸️  Resumed after rate limit wait")
        
        # Record the request
        limiter.record_request()
        
        # Show progress every 5 requests
        if (i + 1) % 5 == 0:
            elapsed = time.time() - start_time
            print(f"📍 Progress: {i+1}/35 requests in {elapsed:.1f}s - {GlobalRateLimiter.get_status_bar()}")
        
        # Simulate some processing time
        time.sleep(0.1)
    
    total_time = time.time() - start_time
    print(f"\n✅ Completed 35 requests in {total_time:.1f}s")
    print(f"   Average: {35/total_time:.1f} requests/second")


if __name__ == "__main__":
    # Run all tests
    test_basic_rate_limiting()
    test_global_limiter()
    test_model_switching()
    test_real_scenario()
