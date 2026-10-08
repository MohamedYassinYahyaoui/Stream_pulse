import os
import asyncio
import logging
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
import clickhouse_connect

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

app = FastAPI(
    title="StreamPulse Analytics API",
    description="Real-time analytics engine exposing system metrics and performance percentiles from ClickHouse.",
    version="1.0.0"
)

# Environment configuration
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "clickhouse")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", "8123"))
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "default")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD", "")


def run_clickhouse_query(query: str) -> Any:
    """Synchronous helper to execute ClickHouse queries."""
    client = clickhouse_connect.get_client(
        host=CLICKHOUSE_HOST,
        port=CLICKHOUSE_PORT,
        username=CLICKHOUSE_USER,
        password=CLICKHOUSE_PASSWORD
    )
    return client.query(query)


@app.get("/health", tags=["System"])
async def health_check():
    """Service health check endpoint."""
    return {"status": "healthy"}


@app.get("/api/v1/analytics/summary", tags=["Analytics"])
async def get_summary() -> Dict[str, Any]:
    """Retrieve aggregate metric metrics including event counts and latency percentiles (P95, P99)."""
    query = """
    SELECT 
        count() as total_events,
        avg(latency_ms) as avg_latency_ms,
        quantile(0.99)(latency_ms) as p99_latency_ms,
        quantile(0.95)(latency_ms) as p95_latency_ms
    FROM default.system_events
    """
    try:
        result = await asyncio.to_thread(run_clickhouse_query, query)
        row = result.first_row
        
        if not row or row[0] == 0:
            return {
                "total_events": 0,
                "avg_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "p95_latency_ms": 0.0
            }

        return {
            "total_events": row[0],
            "avg_latency_ms": round(row[1], 2) if row[1] is not None else 0.0,
            "p99_latency_ms": round(row[2], 2) if row[2] is not None else 0.0,
            "p95_latency_ms": round(row[3], 2) if row[3] is not None else 0.0
        }
    except Exception as e:
        logging.error(f"Error querying summary analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")


@app.get("/api/v1/analytics/services", tags=["Analytics"])
async def get_service_metrics() -> List[Dict[str, Any]]:
    """Retrieve breakdown of event volume and latency distribution grouped by service."""
    query = """
    SELECT 
        service_name,
        count() as event_count,
        avg(latency_ms) as avg_latency,
        quantile(0.99)(latency_ms) as p99_latency
    FROM default.system_events
    GROUP BY service_name
    ORDER BY event_count DESC
    """
    try:
        result = await asyncio.to_thread(run_clickhouse_query, query)
        
        return [
            {
                "service_name": str(row[0]),
                "event_count": row[1],
                "avg_latency_ms": round(row[2], 2) if row[2] is not None else 0.0,
                "p99_latency_ms": round(row[3], 2) if row[3] is not None else 0.0
            }
            for row in result.result_rows
        ]
    except Exception as e:
        logging.error(f"Error querying service analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")