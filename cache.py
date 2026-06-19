from collections import OrderedDict
from threading import Lock
import time


class LRUCache:
    """Basit, thread-safe LRU cache with optional TTL per entry.

    Not: küçük, local cache; production için redis/memcached önerilir.
    """

    def __init__(self, capacity: int = 1024, ttl_seconds: int = 0):
        self.capacity = int(capacity)
        self.ttl = int(ttl_seconds)
        # store key -> (value, timestamp)
        self.cache = OrderedDict()
        self.lock = Lock()

    def _is_expired(self, ts: float) -> bool:
        if self.ttl <= 0:
            return False
        return (time.time() - ts) > self.ttl

    def get(self, key: str):
        with self.lock:
            try:
                value, ts = self.cache.pop(key)
                if self._is_expired(ts):
                    # expired
                    return None
                # refresh position
                self.cache[key] = (value, ts)
                return value
            except KeyError:
                return None

    def set(self, key: str, value):
        with self.lock:
            if key in self.cache:
                self.cache.pop(key)
            self.cache[key] = (value, time.time())
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self):
        with self.lock:
            self.cache.clear()

    def set_ttl(self, ttl_seconds: int):
        with self.lock:
            self.ttl = int(ttl_seconds)
