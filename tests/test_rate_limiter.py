"""Test rate limiter functionality."""

import time
from datetime import datetime, timedelta
import pytest

from gemini_repl.utils.rate_limiter import RateLimiter, GlobalRateLimiter


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter("gemini-2.0-flash")
        
        assert limiter.model_name == "gemini-2.0-flash"
        assert limiter.rpm_limit == 15
        assert limiter.safety_margin == 0.9
        assert len(limiter.request_times) == 0
    
    def test_unknown_model_default(self):
        """Test default limit for unknown models."""
        limiter = RateLimiter("unknown-model")
        assert limiter.rpm_limit == 10  # Default
    
    def test_record_request(self):
        """Test recording requests."""
        limiter = RateLimiter("gemini-2.0-flash")
        
        # Record some requests
        limiter.record_request()
        limiter.record_request()
        
        assert len(limiter.request_times) == 2
    
    def test_wait_not_needed(self):
        """Test when no wait is needed."""
        limiter = RateLimiter("gemini-2.0-flash")  # 15 RPM
        
        # Record fewer requests than limit
        for _ in range(5):
            limiter.record_request()
        
        wait_time = limiter.wait_if_needed()
        assert wait_time == 0
    
    def test_wait_needed(self):
        """Test when wait is needed."""
        limiter = RateLimiter("gemini-2.5-flash")  # 10 RPM, 9 effective
        
        # Fill up to the limit
        for _ in range(9):
            limiter.record_request()
        
        # Next request should need to wait
        wait_time = limiter.wait_if_needed()
        assert wait_time > 0
        assert wait_time <= 60  # Should be less than a minute
    
    def test_old_requests_cleanup(self):
        """Test that old requests are cleaned up."""
        limiter = RateLimiter("gemini-2.0-flash")
        
        # Add an old request (older than 1 minute)
        old_time = datetime.now() - timedelta(minutes=2)
        limiter.request_times.append(old_time)
        
        # Add a recent request
        limiter.record_request()
        
        # Check status should clean up old request
        limiter.wait_if_needed()
        
        # Old request should be gone
        assert len([t for t in limiter.request_times if t == old_time]) == 0
    
    def test_get_status(self):
        """Test status reporting."""
        limiter = RateLimiter("gemini-2.0-flash-lite")  # 30 RPM
        
        # Record some requests
        for _ in range(10):
            limiter.record_request()
        
        status = limiter.get_status()
        
        assert status["model"] == "gemini-2.0-flash-lite"
        assert status["current_rpm"] == 10
        assert status["limit_rpm"] == 30
        assert status["effective_limit"] == 27
        assert status["remaining"] == 17
        assert 35 < status["percentage"] < 40  # ~37%


class TestGlobalRateLimiter:
    """Test the GlobalRateLimiter singleton."""
    
    def test_singleton_pattern(self):
        """Test that we get the same instance."""
        instance1 = GlobalRateLimiter()
        instance2 = GlobalRateLimiter()
        
        assert instance1 is instance2
    
    def test_get_limiter(self):
        """Test getting rate limiters."""
        limiter1 = GlobalRateLimiter.get_limiter("gemini-2.0-flash")
        limiter2 = GlobalRateLimiter.get_limiter("gemini-2.0-flash")
        
        # Should get the same limiter for same model
        assert limiter1 is limiter2
        
        # Different model should get different limiter
        limiter3 = GlobalRateLimiter.get_limiter("gemini-2.5-flash")
        assert limiter3 is not limiter1
        assert limiter3.model_name == "gemini-2.5-flash"
    
    def test_status_bar(self):
        """Test status bar generation."""
        # Clear any existing state
        GlobalRateLimiter._instance = None
        GlobalRateLimiter._limiter = None
        
        # Get a fresh limiter
        limiter = GlobalRateLimiter.get_limiter("gemini-2.0-flash")
        limiter.request_times.clear()
        
        # Test empty
        bar = GlobalRateLimiter.get_status_bar()
        assert "0/13 RPM" in bar  # 15 * 0.9 = 13.5 -> 13
        assert "░" in bar  # Should be empty
        
        # Add some requests
        for _ in range(7):
            limiter.record_request()
        
        bar = GlobalRateLimiter.get_status_bar()
        assert "7/13 RPM" in bar
        assert "█" in bar  # Should have some fill
    
    def test_status_bar_no_limiter(self):
        """Test status bar when no limiter initialized."""
        # Clear state
        GlobalRateLimiter._instance = None
        GlobalRateLimiter._limiter = None
        
        # Create instance but don't get limiter
        GlobalRateLimiter()
        
        bar = GlobalRateLimiter.get_status_bar()
        assert "not initialized" in bar


@pytest.mark.slow
class TestRateLimiterIntegration:
    """Integration tests that involve timing."""
    
    def test_wait_with_display(self):
        """Test the wait with display functionality."""
        limiter = RateLimiter("gemini-2.5-flash")  # Low limit for testing
        
        # Fill up the limit
        for _ in range(9):  # 10 RPM * 0.9 = 9
            limiter.record_request()
        
        # This should trigger a wait
        start = time.time()
        waited = limiter.wait_with_display()
        duration = time.time() - start
        
        assert waited is True
        assert duration > 0  # Should have waited some time
    
    def test_no_wait_display(self):
        """Test when no wait is needed."""
        limiter = RateLimiter("gemini-2.0-flash-lite")  # High limit
        
        # Just a few requests
        for _ in range(5):
            limiter.record_request()
        
        waited = limiter.wait_with_display()
        assert waited is False
