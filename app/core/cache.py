from typing import Optional, Any, Dict
from datetime import datetime, timedelta
import json
import asyncio
from collections import OrderedDict


class SimpleCache:
    """
    Simple in-memory cache with TTL support
    No Redis required - use this for development
    """

    def __init__(self, max_size: int = 1000):
        self._cache: OrderedDict = OrderedDict()
        self._expiry: Dict[str, datetime] = {}
        self._max_size = max_size
        self._lock = asyncio.Lock()

    async def set(
        self,
        key: str,
        value: Any,
        expire_seconds: Optional[int] = None
    ) -> bool:
        """Set a value in the cache"""
        async with self._lock:
            # Clean up old entries if cache is full
            if len(self._cache) >= self._max_size:
                self._cleanup()

            self._cache[key] = value
            if expire_seconds:
                self._expiry[key] = datetime.utcnow() + timedelta(seconds=expire_seconds)
            else:
                self._expiry.pop(key, None)

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return True

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from the cache"""
        async with self._lock:
            # Check if expired
            if key in self._expiry and self._expiry[key] < datetime.utcnow():
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
                return None

            value = self._cache.get(key)
            if value is not None:
                # Move to end (most recently used)
                self._cache.move_to_end(key)
            return value

    async def delete(self, key: str) -> bool:
        """Delete a value from the cache"""
        async with self._lock:
            if key in self._cache:
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
                return True
            return False

    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self._lock:
            self._cache.clear()
            self._expiry.clear()

    async def exists(self, key: str) -> bool:
        """Check if a key exists and is not expired"""
        async with self._lock:
            if key not in self._cache:
                return False
            if key in self._expiry and self._expiry[key] < datetime.utcnow():
                self._cache.pop(key, None)
                self._expiry.pop(key, None)
                return False
            return True

    async def get_or_set(
        self,
        key: str,
        callback,
        expire_seconds: Optional[int] = None
    ) -> Any:
        """Get a value, or set it if not exists"""
        value = await self.get(key)
        if value is not None:
            return value

        value = await callback()
        await self.set(key, value, expire_seconds)
        return value

    def _cleanup(self):
        """Remove expired or oldest entries"""
        # Remove expired entries first
        now = datetime.utcnow()
        expired = [k for k, v in self._expiry.items() if v < now]
        for k in expired:
            self._cache.pop(k, None)
            self._expiry.pop(k, None)

        # If still over limit, remove oldest entries
        while len(self._cache) > self._max_size:
            # Pop first item (oldest)
            key, _ = self._cache.popitem(last=False)
            self._expiry.pop(key, None)

    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "expiry_count": len(self._expiry),
            "keys": list(self._cache.keys())[:10]  # Show first 10 keys
        }


# Create singleton instance
cache = SimpleCache(max_size=1000)


async def get_cache() -> SimpleCache:
    """Dependency for getting cache instance"""
    return cache