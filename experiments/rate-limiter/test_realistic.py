#!/usr/bin/env python3
"""Test rate limiter with realistic REPL usage."""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gemini_repl.utils.rate_limiter import RateLimiter, GlobalRateLimiter


def test_repl_simulation():
    """Simulate realistic REPL usage patterns."""
    print("🎮 Simulating REPL Usage with Rate Limiter")
    print("=" * 60)
    
    # Use the default model
    limiter = GlobalRateLimiter.get_limiter("gemini-2.0-flash-lite")
    
    print(f"Model: gemini-2.0-flash-lite")
    print(f"Rate Limit: 30 RPM")
    print(f"Effective Limit: 27 RPM (90% safety margin)")
    print("\nSimulating user queries...\n")
    
    # Simulate realistic queries
    queries = [
        "What is 2 + 2?",
        "Show that in bc syntax",
        "Now show it in Elisp",
        "What about APL?",
        "Explain the Makefile targets",
        "What does the test target do?",
        "Show me the project structure",
        "What Python version is used?",
        "List the dependencies",
        "How do I run tests?",
    ]
    
    # First, simulate normal usage (queries every few seconds)
    print("📝 Normal usage pattern (1 query every 3 seconds):")
    for i, query in enumerate(queries[:5]):
        limiter.record_request()
        status = limiter.get_status()
        print(f"   Query {i+1}: \"{query}\" - {GlobalRateLimiter.get_status_bar()}")
        time.sleep(3)
    
    print("\n⚡ Rapid usage pattern (queries as fast as possible):")
    # Now simulate rapid queries
    rapid_start = time.time()
    for i in range(25):  # This should approach the limit
        wait_time = limiter.wait_if_needed()
        
        if wait_time > 0:
            print(f"\n   ⏸️  Approaching rate limit! Need to wait {wait_time:.1f}s")
            print(f"   Current usage: {GlobalRateLimiter.get_status_bar()}")
            limiter.wait_with_display()
            print(f"   ▶️  Resuming...")
        
        limiter.record_request()
        
        if i % 5 == 0:
            print(f"   Query {i+1}/25 - {GlobalRateLimiter.get_status_bar()}")
        
        # Very small delay to simulate processing
        time.sleep(0.05)
    
    rapid_time = time.time() - rapid_start
    print(f"\n📊 Rapid batch completed in {rapid_time:.1f}s")
    
    # Show final status
    final_status = limiter.get_status()
    print(f"\n📈 Final Status:")
    print(f"   Requests in last minute: {final_status['current_rpm']}")
    print(f"   Limit: {final_status['limit_rpm']} RPM")
    print(f"   Remaining capacity: {final_status['remaining']}")


def test_burst_protection():
    """Test protection against bursts."""
    print("\n\n🛡️  Testing Burst Protection")
    print("=" * 60)
    
    limiter = RateLimiter("gemini-2.5-flash")  # 10 RPM limit
    
    print(f"Testing with restrictive model: gemini-2.5-flash (10 RPM)")
    print(f"Effective limit: {int(limiter.rpm_limit * limiter.safety_margin)} RPM\n")
    
    # Try to make 15 requests immediately
    print("Attempting 15 rapid requests...")
    
    successful = 0
    waited = 0
    
    for i in range(15):
        wait_time = limiter.wait_if_needed()
        
        if wait_time > 0:
            waited += 1
            print(f"\n🛑 Request {i+1} blocked - would need to wait {wait_time:.1f}s")
            print(f"   (Skipping wait for demo purposes)")
            break
        else:
            limiter.record_request()
            successful += 1
            print(f"✅ Request {i+1} successful - {len(limiter.request_times)}/9 slots used")
    
    print(f"\n📊 Summary:")
    print(f"   Successful requests: {successful}")
    print(f"   Blocked requests: {waited}")
    print(f"   Protection working: {'✅ Yes' if waited > 0 else '❌ No'}")


def test_status_display():
    """Test the status bar at different usage levels."""
    print("\n\n🎨 Testing Status Display")
    print("=" * 60)
    
    limiter = GlobalRateLimiter.get_limiter("gemini-2.0-flash")  # 15 RPM
    
    print("Status bar at different usage levels:\n")
    
    # Clear any existing requests
    limiter._limiter.request_times.clear()
    
    # Test different fill levels
    test_levels = [0, 3, 7, 10, 13, 14]
    
    for level in test_levels:
        # Clear and add specific number of requests
        limiter._limiter.request_times.clear()
        for _ in range(level):
            limiter._limiter.record_request()
        
        status = limiter._limiter.get_status()
        bar = GlobalRateLimiter.get_status_bar()
        
        print(f"   {level:2d} requests: {bar} - {status['percentage']:5.1f}% full")
        
        # Add color coding hints
        if status['percentage'] >= 90:
            print("              ⚠️  Near limit!")
        elif status['percentage'] >= 70:
            print("              ⏰ Getting close...")


if __name__ == "__main__":
    test_repl_simulation()
    test_burst_protection()
    test_status_display()
    
    print("\n\n✅ All rate limiter tests complete!")
