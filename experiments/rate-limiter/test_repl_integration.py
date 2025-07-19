#!/usr/bin/env python3
"""Test rate limiter integration with REPL."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gemini_repl.core.api_client import GeminiClient
from gemini_repl.utils.rate_limiter import GlobalRateLimiter


def test_api_integration():
    """Test rate limiter with actual API client."""
    print("🧪 Testing Rate Limiter with API Client")
    print("=" * 50)
    
    # Check API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set - skipping API test")
        return
    
    try:
        # Create client
        client = GeminiClient()
        print(f"✅ Client initialized with model: {client.model_name}")
        print(f"   Rate limit: {client.rate_limiter.rpm_limit} RPM")
        
        # Test a simple query
        messages = [{"role": "user", "content": "Say 'test' and nothing else"}]
        
        print("\n📤 Sending test request...")
        response = client.send_message(messages)
        
        if response and response.text:
            print(f"✅ Response received: {response.text.strip()}")
        
        # Check rate limiter status
        status = GlobalRateLimiter.get_status_bar()
        print(f"\n📊 Rate limiter status: {status}")
        
        # Test multiple rapid requests
        print("\n🚀 Testing rapid requests...")
        for i in range(5):
            print(f"\n   Request {i+1}/5: ", end="", flush=True)
            
            messages = [{"role": "user", "content": f"Count to {i+1}"}]
            response = client.send_message(messages)
            
            if response and response.text:
                print("✅")
                print(f"   Status: {GlobalRateLimiter.get_status_bar()}")
            else:
                print("❌ No response")
        
        print("\n✅ Integration test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_rate_limit_visual():
    """Test visual feedback during rate limiting."""
    print("\n\n🎨 Testing Visual Rate Limit Feedback")
    print("=" * 50)
    
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not set - skipping visual test")
        return
    
    try:
        # Create client with low-limit model
        os.environ["GEMINI_MODEL"] = "gemini-2.5-flash"  # 10 RPM
        client = GeminiClient()
        
        print(f"Using model: {client.model_name} (10 RPM limit)")
        print("Attempting to trigger rate limit...\n")
        
        # Make requests until we hit the limit
        for i in range(12):
            print(f"Request {i+1}: ", end="", flush=True)
            
            messages = [{"role": "user", "content": "Hi"}]
            response = client.send_message(messages)
            
            if response and response.text:
                print(f"✅ - {GlobalRateLimiter.get_status_bar()}")
            else:
                print("❌")
        
        print("\n✅ Visual test complete!")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        # Reset to default model
        if "GEMINI_MODEL" in os.environ:
            del os.environ["GEMINI_MODEL"]


if __name__ == "__main__":
    test_api_integration()
    test_rate_limit_visual()
