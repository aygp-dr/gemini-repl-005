"""Rate limiter to prevent API quota exhaustion."""

import time
from collections import deque
from datetime import datetime, timedelta
from typing import Dict


class RateLimiter:
    """Rate limiter with per-minute request tracking."""
    
    # Model rate limits (requests per minute)
    MODEL_LIMITS = {
        "gemini-2.0-flash-lite": 30,
        "gemini-2.0-flash": 15,
        "gemini-2.5-flash": 10,
        "gemini-2.5-flash-lite-preview-06-17": 15,
        "gemini-2.0-flash-exp": 10,
        "gemini-2.5-pro": 5,
        "gemini-1.5-flash": 15,  # Deprecated
    }
    
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.rpm_limit = self.MODEL_LIMITS.get(model_name, 10)  # Default to 10 if unknown
        self.request_times = deque()  # Track request timestamps
        self.safety_margin = 0.9  # Use only 90% of limit to be safe
        
    def wait_if_needed(self) -> float:
        """
        Check if we need to wait before making a request.
        Returns the wait time in seconds (0 if no wait needed).
        """
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Remove requests older than 1 minute
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()
        
        # Check if we're at the limit
        effective_limit = int(self.rpm_limit * self.safety_margin)
        if len(self.request_times) >= effective_limit:
            # Calculate how long to wait
            oldest_request = self.request_times[0]
            wait_until = oldest_request + timedelta(minutes=1)
            wait_seconds = (wait_until - now).total_seconds()
            
            if wait_seconds > 0:
                return wait_seconds
        
        return 0
    
    def record_request(self):
        """Record that a request was made."""
        self.request_times.append(datetime.now())
    
    def get_status(self) -> Dict[str, any]:
        """Get current rate limit status."""
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        
        # Clean old requests
        while self.request_times and self.request_times[0] < one_minute_ago:
            self.request_times.popleft()
        
        current_rpm = len(self.request_times)
        effective_limit = int(self.rpm_limit * self.safety_margin)
        
        return {
            "model": self.model_name,
            "current_rpm": current_rpm,
            "limit_rpm": self.rpm_limit,
            "effective_limit": effective_limit,
            "remaining": max(0, effective_limit - current_rpm),
            "percentage": (current_rpm / effective_limit * 100) if effective_limit > 0 else 0
        }
    
    def wait_with_display(self) -> bool:
        """
        Wait if needed with a visual countdown.
        Returns True if we had to wait, False otherwise.
        """
        wait_time = self.wait_if_needed()
        
        if wait_time > 0:
            print(f"\n⏳ Rate limit approaching ({self.get_status()['current_rpm']}/{self.get_status()['effective_limit']} RPM)")
            print(f"   Waiting {wait_time:.1f}s to avoid hitting limit...")
            
            # Visual countdown
            remaining = wait_time
            while remaining > 0:
                print(f"\r   {remaining:.1f}s remaining...", end="", flush=True)
                sleep_time = min(0.1, remaining)
                time.sleep(sleep_time)
                remaining -= sleep_time
            
            print("\r✅ Ready to continue!        ")
            return True
        
        return False


class GlobalRateLimiter:
    """Singleton rate limiter for the application."""
    
    _instance = None
    _limiter = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_limiter(cls, model_name: str) -> RateLimiter:
        """Get or create rate limiter for model."""
        instance = cls()
        if instance._limiter is None or instance._limiter.model_name != model_name:
            instance._limiter = RateLimiter(model_name)
        return instance._limiter
    
    @classmethod
    def get_status_bar(cls) -> str:
        """Get a compact status bar for display."""
        instance = cls()
        if instance._limiter:
            status = instance._limiter.get_status()
            bar_width = 20
            filled = int((status['percentage'] / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            return f"[{bar}] {status['current_rpm']}/{status['effective_limit']} RPM"
        return "[Rate limiter not initialized]"
