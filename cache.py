from collections import OrderedDict
from threading import Lock


class LRUCache:
    """Basit, thread-safe LRU cache.

    Not: küçük, local cache; production için redis/memcached önerilir.
    """

    def __init__(self, capacity: int = 1024):
        self.capacity = int(capacity)
        self.cache = OrderedDict()
        self.lock = Lock()

    def get(self, key: str):
        with self.lock:
            try:
                value = self.cache.pop(key)
                self.cache[key] = value
                return value
            except KeyError:
                return None

    def set(self, key: str, value):
        with self.lock:
            if key in self.cache:
                # move to end
                self.cache.pop(key)
            self.cache[key] = value
            if len(self.cache) > self.capacity:
                self.cache.popitem(last=False)

    def clear(self):
        with self.lock:
            self.cache.clear()
