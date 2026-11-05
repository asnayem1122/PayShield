"""In-memory rate limiter for authentication endpoints to mitigate brute force attacks."""

from collections import defaultdict
from datetime import datetime, timedelta, timezone
import threading


class RateLimiter:
    """Thread-safe sliding-window rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: dict[str, list[datetime]] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """Check if request for key is within rate limit; records timestamp if allowed."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self.window_seconds)

        with self._lock:
            # Filter timestamps within active sliding window
            timestamps = [ts for ts in self._requests[key] if ts > cutoff]
            if len(timestamps) >= self.max_requests:
                self._requests[key] = timestamps
                return False

            timestamps.append(now)
            self._requests[key] = timestamps
            return True

    def reset(self) -> None:
        """Reset rate limiter state (used in testing)."""
        with self._lock:
            self._requests.clear()


login_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)
