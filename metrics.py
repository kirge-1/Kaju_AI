import threading
import time
from statistics import median, quantiles

_lock = threading.Lock()
_records = []  # list of (timestamp, tag, duration_ms)


def record_latency(tag: str, duration_ms: float) -> None:
    ts = time.time()
    with _lock:
        _records.append((ts, tag, float(duration_ms)))
        # keep bounded history
        if len(_records) > 10000:
            del _records[0:1000]


def snapshot(tag: str = None):
    with _lock:
        data = list(_records)
    if tag:
        data = [d for d in data if d[1] == tag]
    return data


def percentiles(tag: str = None):
    data = [d[2] for d in snapshot(tag)]
    if not data:
        return {"p50": None, "p95": None}
    data_sorted = sorted(data)
    p50 = median(data_sorted)
    # p95 via quantiles
    try:
        p95 = quantiles(data_sorted, n=100)[94]
    except Exception:
        p95 = data_sorted[int(len(data_sorted) * 0.95) - 1]
    return {"p50": p50, "p95": p95}


def clear():
    with _lock:
        _records.clear()
