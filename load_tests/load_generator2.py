import asyncio
import httpx
import time
import os
from collections import Counter

URL = "http://localhost:8000/api/v1/events"
TOTAL_REQUESTS = int(os.getenv("TOTAL_REQUESTS", "10000"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "50"))

payload = {
    "service_name": "checkout-service",
    "event_type": "payment_processed",
    "environment": ["production"],
    "payload": "{\"order_id\": 99482, \"status\": \"success\"}",
    "latency_ms": 120
}

async def send_request(client, semaphore):
    async with semaphore:
        try:
            response = await client.post(URL, json=payload)
            return response.status_code
        except Exception as e:
            return str(e)

async def run_benchmark():
    semaphore = asyncio.Semaphore(CONCURRENCY)
    limits = httpx.Limits(max_keepalive_connections=CONCURRENCY, max_connections=CONCURRENCY)
    async with httpx.AsyncClient(limits=limits, timeout=10.0) as client:
        start_time = time.perf_counter()
        tasks = [send_request(client, semaphore) for _ in range(TOTAL_REQUESTS)]
        results = await asyncio.gather(*tasks)
        elapsed = time.perf_counter() - start_time
        status_counts = Counter(results)
        successful = sum(count for status, count in status_counts.items() if isinstance(status, int) and 200 <= status < 300)
        failed = TOTAL_REQUESTS - successful
        print(f"Completed {TOTAL_REQUESTS} requests in {elapsed:.2f}s ({TOTAL_REQUESTS/elapsed:.2f} req/sec)")
        print(f"Successful: {successful}; Failed: {failed}; Statuses: {dict(status_counts)}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())