"""
Simple response cache for faster repeat queries
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import json

class ResponseCache:
    """Cache for LLM responses"""
    
    def __init__(self, ttl_seconds: int = 300):  # 5 minute cache
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl_seconds
    
    def _make_key(self, model: str, prompt: str) -> str:
        """Create cache key from model and prompt"""
        key_str = f"{model}:{prompt}"
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, model: str, prompt: str) -> Optional[str]:
        """Get cached response if exists and not expired"""
        key = self._make_key(model, prompt)
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now() < entry['expires']:
                return entry['response']
            else:
                del self.cache[key]
        return None
    
    def set(self, model: str, prompt: str, response: str):
        """Cache a response"""
        key = self._make_key(model, prompt)
        self.cache[key] = {
            'response': response,
            'expires': datetime.now() + timedelta(seconds=self.ttl)
        }
    
    def clear(self):
        """Clear all cache"""
        self.cache.clear()

# Global cache instance
_cache = None

def get_cache():
    global _cache
    if _cache is None:
        _cache = ResponseCache()
    return _cache
