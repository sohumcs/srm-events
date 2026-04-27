from collections import defaultdict, deque
from datetime import datetime
import time

class MetricsStore:
    def __init__(self):
        self.request_log = deque(maxlen=1000)
        self.endpoint_counts = defaultdict(int)
        self.status_counts = defaultdict(int)
        self.response_times = deque(maxlen=200)
        self.start_time = time.time()
        self.error_count = 0

    def record_request(self, path: str, status_code: int, duration_ms: float):
        self.request_log.append({
            "path": path,
            "status": status_code,
            "duration_ms": round(duration_ms, 2),
            "timestamp": datetime.utcnow().isoformat()
        })
        self.endpoint_counts[path] += 1
        self.status_counts[str(status_code)] += 1
        self.response_times.append(duration_ms)
        if status_code >= 400:
            self.error_count += 1

    def get_summary(self):
        times = list(self.response_times)
        avg_rt = round(sum(times) / len(times), 2) if times else 0
        max_rt = round(max(times), 2) if times else 0
        min_rt = round(min(times), 2) if times else 0
        uptime = round(time.time() - self.start_time, 1)
        total_requests = sum(self.endpoint_counts.values())
        error_rate = round((self.error_count / max(total_requests, 1)) * 100, 2)

        return {
            "uptime_seconds": uptime,
            "total_requests": total_requests,
            "error_count": self.error_count,
            "error_rate_percent": error_rate,
            "avg_response_ms": avg_rt,
            "max_response_ms": max_rt,
            "min_response_ms": min_rt,
            "top_endpoints": dict(sorted(self.endpoint_counts.items(), key=lambda x: -x[1])[:8]),
            "status_distribution": dict(self.status_counts)
        }

    def get_request_history(self):
        return list(self.request_log)[-50:]

    def get_performance_data(self):
        times = list(self.response_times)
        buckets = {"<50ms": 0, "50-100ms": 0, "100-200ms": 0, ">200ms": 0}
        for t in times:
            if t < 50: buckets["<50ms"] += 1
            elif t < 100: buckets["50-100ms"] += 1
            elif t < 200: buckets["100-200ms"] += 1
            else: buckets[">200ms"] += 1
        return {"response_time_distribution": buckets, "samples": len(times)}

metrics_store = MetricsStore()
