"""
Rate limiter and cache for AI commands.
"""

import time
from collections import defaultdict

_cache = {}
CACHE_TTL = 1800

_user_requests = defaultdict(list)
MAX_REQUESTS_PER_HOUR = 3


def get_cached(key: str):
    if key in _cache:
        result, timestamp = _cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return result
        del _cache[key]
    return None


def set_cached(key: str, result: str):
    _cache[key] = (result, time.time())


def check_rate_limit(chat_id: int) -> tuple:
    now = time.time()
    _user_requests[chat_id] = [t for t in _user_requests[chat_id] if t > now - 3600]
    count = len(_user_requests[chat_id])
    if count >= MAX_REQUESTS_PER_HOUR:
        wait = int((_user_requests[chat_id][0] + 3600 - now) / 60)
        return False, f"⚠️ Rate limit: {count}/{MAX_REQUESTS_PER_HOUR} AI requests this hour.\nTry again in `{wait} min`."
    _user_requests[chat_id].append(now)
    return True, f"_{MAX_REQUESTS_PER_HOUR - count - 1} AI requests remaining this hour_"
