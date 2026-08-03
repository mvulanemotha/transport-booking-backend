import json
import redis.asyncio as redis
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta
import pickle

from app.core.config import settings


class RedisClient:
    """Redis client wrapper for caching and session management"""

    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def connect(self) -> None:
        """Connect to Redis"""
        if self._client is None:
            self._client = redis.from_url(
                str(settings.REDIS_URL),
                encoding="utf-8",
                decode_responses=False,
                max_connections=settings.REDIS_POOL_SIZE,
            )

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> redis.Redis:
        """Get Redis client"""
        if self._client is None:
            raise RuntimeError("Redis client not connected. Call connect() first.")
        return self._client

    # ==================== String Operations ====================

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """Set a key-value pair"""
        if serialize:
            value = json.dumps(value)
        result = await self.client.set(key, value)
        if expire:
            await self.client.expire(key, expire)
        return result

    async def get(
        self,
        key: str,
        deserialize: bool = True
    ) -> Optional[Any]:
        """Get a value by key"""
        value = await self.client.get(key)
        if value and deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys"""
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.client.exists(key) > 0

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on key"""
        return await self.client.expire(key, seconds)

    # ==================== Hash Operations ====================

    async def hset(
        self,
        key: str,
        field: str,
        value: Any,
        serialize: bool = True
    ) -> int:
        """Set a field in a hash"""
        if serialize:
            value = json.dumps(value)
        return await self.client.hset(key, field, value)

    async def hget(
        self,
        key: str,
        field: str,
        deserialize: bool = True
    ) -> Optional[Any]:
        """Get a field from a hash"""
        value = await self.client.hget(key, field)
        if value and deserialize:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def hgetall(
        self,
        key: str,
        deserialize: bool = True
    ) -> Dict[str, Any]:
        """Get all fields from a hash"""
        values = await self.client.hgetall(key)
        if deserialize:
            result = {}
            for k, v in values.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v
            return result
        return values

    async def hdel(self, key: str, *fields: str) -> int:
        """Delete fields from a hash"""
        return await self.client.hdel(key, *fields)

    # ==================== List Operations ====================

    async def lpush(self, key: str, *values: Any) -> int:
        """Push values to the left of a list"""
        return await self.client.lpush(key, *values)

    async def rpush(self, key: str, *values: Any) -> int:
        """Push values to the right of a list"""
        return await self.client.rpush(key, *values)

    async def lpop(self, key: str) -> Optional[Any]:
        """Pop a value from the left of a list"""
        value = await self.client.lpop(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def rpop(self, key: str) -> Optional[Any]:
        """Pop a value from the right of a list"""
        value = await self.client.rpop(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    async def lrange(
        self,
        key: str,
        start: int,
        end: int,
        deserialize: bool = True
    ) -> List[Any]:
        """Get a range of values from a list"""
        values = await self.client.lrange(key, start, end)
        if deserialize:
            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except json.JSONDecodeError:
                    result.append(v)
            return result
        return values

    # ==================== Set Operations ====================

    async def sadd(self, key: str, *values: Any) -> int:
        """Add values to a set"""
        return await self.client.sadd(key, *values)

    async def srem(self, key: str, *values: Any) -> int:
        """Remove values from a set"""
        return await self.client.srem(key, *values)

    async def smembers(self, key: str) -> set:
        """Get all members of a set"""
        return await self.client.smembers(key)

    async def sismember(self, key: str, value: Any) -> bool:
        """Check if a value is in a set"""
        return await self.client.sismember(key, value)

    # ==================== Session Operations ====================

    async def set_session(
        self,
        session_id: str,
        data: Dict[str, Any],
        expiry_seconds: int = 3600
    ) -> bool:
        """Set session data"""
        return await self.set(
            f"session:{session_id}",
            data,
            expire=expiry_seconds
        )

    async def get_session(
        self,
        session_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get session data"""
        return await self.get(f"session:{session_id}")

    async def delete_session(self, session_id: str) -> int:
        """Delete session"""
        return await self.delete(f"session:{session_id}")

    # ==================== Cache Operations ====================

    async def cache_set(
        self,
        key: str,
        value: Any,
        expiry_seconds: int = 300
    ) -> bool:
        """Set cached data with expiration"""
        return await self.set(
            f"cache:{key}",
            value,
            expire=expiry_seconds
        )

    async def cache_get(self, key: str) -> Optional[Any]:
        """Get cached data"""
        return await self.get(f"cache:{key}")

    async def cache_delete(self, key: str) -> int:
        """Delete cached data"""
        return await self.delete(f"cache:{key}")

    async def cache_clear_pattern(self, pattern: str) -> int:
        """Clear all cache keys matching a pattern"""
        keys = await self.client.keys(f"cache:{pattern}")
        if keys:
            return await self.client.delete(*keys)
        return 0

    # ==================== Rate Limiting ====================

    async def rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60
    ) -> tuple[int, bool]:
        """
        Rate limit check

        Returns:
            (count, allowed) - count of requests in window, whether request is allowed
        """
        current = await self.client.incr(f"rate_limit:{key}")
        if current == 1:
            await self.client.expire(f"rate_limit:{key}", window_seconds)

        return current, current <= limit

    # ==================== Lock Operations ====================

    async def acquire_lock(
        self,
        key: str,
        timeout_seconds: int = 10
    ) -> bool:
        """Acquire a distributed lock"""
        # Use SET NX (not exists) to acquire lock
        result = await self.client.set(
            f"lock:{key}",
            "locked",
            nx=True,
            ex=timeout_seconds
        )
        return bool(result)

    async def release_lock(self, key: str) -> int:
        """Release a distributed lock"""
        return await self.delete(f"lock:{key}")

    # ==================== Queue Operations ====================

    async def enqueue(self, queue_name: str, item: Any) -> int:
        """Add item to queue"""
        return await self.rpush(f"queue:{queue_name}", json.dumps(item))

    async def dequeue(self, queue_name: str) -> Optional[Any]:
        """Get item from queue"""
        return await self.lpop(f"queue:{queue_name}")

    async def get_queue_length(self, queue_name: str) -> int:
        """Get queue length"""
        return await self.client.llen(f"queue:{queue_name}")

    # ==================== Admin Operations ====================

    async def flush_all(self) -> bool:
        """Flush all Redis data (use with caution!)"""
        return await self.client.flushall()

    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching pattern"""
        return await self.client.keys(pattern)

    async def get_info(self) -> Dict[str, Any]:
        """Get Redis server info"""
        return await self.client.info()


# Singleton instance
redis_client = RedisClient()


async def get_redis() -> RedisClient:
    """Dependency for getting Redis client"""
    await redis_client.connect()
    return redis_client