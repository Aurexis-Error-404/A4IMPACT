import time

_CACHE: dict[str, tuple[dict, float]] = {}
_TTL = 3600  # 1 hour


def get(key: str) -> dict | None:
    entry = _CACHE.get(key)
    if entry is None:
        return None
    value, expires_at = entry
    if time.monotonic() > expires_at:
        del _CACHE[key]
        return None
    return value


def set(key: str, value: dict) -> None:
    _CACHE[key] = (value, time.monotonic() + _TTL)


def clear() -> None:
    _CACHE.clear()
