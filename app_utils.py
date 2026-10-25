import re, time
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_hits = {}

def norm(s): return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def throttled(key, limit=10, window=300):
    now = time.time(); _hits[key] = [t for t in _hits.get(key, []) if now - t < window]
    return len(_hits[key]) >= limit

def hit(key): _hits.setdefault(key, []).append(time.time())
