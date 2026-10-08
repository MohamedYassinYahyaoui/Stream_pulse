import pytest
import requests

BASE_URL = "http://localhost:8001/api/v1/analytics"

def test_health_check():
    response = requests.get("http://localhost:8001/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_analytics_summary():
    response = requests.get(f"{BASE_URL}/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_events"] > 0
    assert "p99_latency_ms" in data
    assert "avg_latency_ms" in data

def test_service_breakdown():
    response = requests.get(f"{BASE_URL}/services")
    assert response.status_code == 200
    services = response.json()
    assert isinstance(services, list)
    assert len(services) > 0