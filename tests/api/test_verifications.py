import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.main import app
from app.database.session import engine
from app.database.config import settings
from app.cache.redis_client import redis_client

client = TestClient(app)

def test_verification_suite():
    # Setup user
    client.post("/api/v1/auth/register", json={"username": "verify_user", "email": "verify@test.com", "password": "password123"})
    login_res = client.post("/api/v1/auth/login", json={"email": "verify@test.com", "password": "password123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a URL
    url_res = client.post("/api/v1/urls", json={"original_url": "https://cachetest.com"}, headers=headers)
    assert url_res.status_code == 201
    url_data = url_res.json()
    short_code = url_data["short_code"]
    url_id = url_data["id"]

    # Clear redis just in case
    redis_client.delete(f"url:{short_code}")

    # Track SQL queries
    query_count = {"select": 0, "update": 0}

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        stmt = statement.strip().lower()
        if stmt.startswith("select") and "urls" in stmt:
            query_count["select"] += 1
        if stmt.startswith("update") and "urls" in stmt:
            query_count["update"] += 1

    event.listen(engine, "before_cursor_execute", before_cursor_execute)

    # First request: Cache miss, should SELECT and UPDATE
    res1 = client.get(f"/{short_code}", follow_redirects=False)
    assert res1.status_code == 302
    assert query_count["select"] > 0
    
    # Reset counts
    query_count["select"] = 0
    query_count["update"] = 0

    # Second request: Cache hit, should NOT SELECT, only UPDATE (clicks)
    res2 = client.get(f"/{short_code}", follow_redirects=False)
    assert res2.status_code == 302
    assert query_count["select"] == 0, "A SELECT query was executed on a cache hit!"
    assert query_count["update"] > 0, "An UPDATE query was NOT executed for click count!"
    print("Verification 1 passed: Cache hit does not touch Postgres for SELECT.")

    event.remove(engine, "before_cursor_execute", before_cursor_execute)

    # 2. Deactivating a URL immediately stops redirect
    # Verify it works currently
    res3 = client.get(f"/{short_code}", follow_redirects=False)
    assert res3.status_code == 302
    
    # Deactivate
    patch_res = client.patch(f"/api/v1/urls/{url_id}", json={"is_active": False}, headers=headers)
    assert patch_res.status_code == 200
    
    # Try redirect again
    res4 = client.get(f"/{short_code}", follow_redirects=False)
    assert res4.status_code == 410
    print("Verification 2 passed: Deactivating a URL immediately stops the redirect.")

    # 3. Exceeding rate limit returns 429
    # We create another URL to hit
    res5 = client.post("/api/v1/urls", json={"original_url": "https://ratelimit.com"}, headers=headers)
    assert res5.status_code == 201
    
    # Try hitting POST /api/v1/urls 10 more times (12 total for this IP which is over 10/min)
    status_codes = set()
    for _ in range(10):
        r = client.post("/api/v1/urls", json={"original_url": "https://spam.com"}, headers=headers)
        status_codes.add(r.status_code)
    
    assert 429 in status_codes, "Rate limit did not return 429"
    assert 500 not in status_codes, "Rate limit returned a stack trace (500) instead of 429"
    print("Verification 3 passed: Exceeding rate limit returns 429 properly.")

    print("All verifications passed!")
