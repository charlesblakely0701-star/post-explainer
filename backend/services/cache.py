"""Simple in-memory caching service."""

import hashlib
import json
from typing import Optional, Any
from datetime import datetime, timedelta
import logging

from config import get_settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Simple in-memory cache service.
    For MVP, we use a dict. Can be replaced with Redis later.
    """
    
    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        settings = get_settings()
        self.ttl = timedelta(seconds=settings.cache_ttl)
    
    def _generate_key(self, text: str) -> str:
        """Generate a cache key from post text."""
        normalized = text.lower().strip()
        return f"explain:{hashlib.sha256(normalized.encode()).hexdigest()[:16]}"
    
    def get(self, text: str) -> Optional[dict]:
        """
        Get cached result for a post.
        
        Args:
            text: The post text
            
        Returns:
            Cached result dict or None if not found/expired
        """
        key = self._generate_key(text)
        
        if key not in self._cache:
            return None
        
        value, timestamp = self._cache[key]
        
        # Check if expired
        if datetime.now() - timestamp > self.ttl:
            del self._cache[key]
            return None
        
        logger.debug(f"Cache hit for key: {key}")
        return value
    
    def set(self, text: str, value: dict) -> None:
        """
        Cache a result.
        
        Args:
            text: The post text (used as key)
            value: The result to cache
        """
        key = self._generate_key(text)
        self._cache[key] = (value, datetime.now())
        logger.debug(f"Cached result for key: {key}")
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp > self.ttl
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        return len(expired_keys)

