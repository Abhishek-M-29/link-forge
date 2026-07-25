import requests
import jwt
import time
import uuid

BASE_URL = "http://127.0.0.1:8000"
API_URL = f"{BASE_URL}/api/v1"

def test():
    print("\n--- 1. Register/login work and return valid JWTs ---")
    user_a = f"usera_{uuid.uuid4().hex[:8]}"
    pwd_a = "password123"
    
    r_reg = requests.post(f"{API_URL}/auth/register", json={"username": user_a, "email": f"{user_a}@test.com", "password": pwd_a})
    assert r_reg.status_code == 201, f"Failed to register User A: {r_reg.text}"
    user_a_id = r_reg.json()["id"]
    print("User A registered successfully.")
    
    r_log = requests.post(f"{API_URL}/auth/login", json={"email": f"{user_a}@test.com", "password": pwd_a})
    assert r_log.status_code == 200, "Failed to login User A"
    access_token_a = r_log.json()["access_token"]
    
    claims = jwt.decode(access_token_a, options={"verify_signature": False})
    print(f"Decoded claims: {claims}")
    assert claims["sub"] == user_a_id, "Subject claim does not match user ID"
    assert claims["type"] == "access", "Token type is not 'access'"
    print("Valid JWT claims sanity-checked.")
    
    print("\n--- 2. An expired or tampered access token is rejected with 401 ---")
    tampered_token = access_token_a[:-5] + "aaaaa"
    r_tampered = requests.post(f"{API_URL}/urls", headers={"Authorization": f"Bearer {tampered_token}"}, json={"original_url": "https://example.com"})
    assert r_tampered.status_code == 401, f"Expected 401, got {r_tampered.status_code}"
    print("Tampered token rejected with 401.")
    
    print("\n--- 3. A user cannot PATCH/DELETE another user's URL (403) ---")
    user_b = f"userb_{uuid.uuid4().hex[:8]}"
    pwd_b = "password123"
    r_reg_b = requests.post(f"{API_URL}/auth/register", json={"username": user_b, "email": f"{user_b}@test.com", "password": pwd_b})
    assert r_reg_b.status_code == 201, "Failed to register User B"
    r_log_b = requests.post(f"{API_URL}/auth/login", json={"email": f"{user_b}@test.com", "password": pwd_b})
    access_token_b = r_log_b.json()["access_token"]
    
    r_create = requests.post(f"{API_URL}/urls", headers={"Authorization": f"Bearer {access_token_a}"}, json={"original_url": "https://url-a.com"})
    assert r_create.status_code == 201, f"Failed to create URL for User A: {r_create.text}"
    url_id = r_create.json()["id"]
    print(f"User A created URL {url_id}")
    
    r_patch = requests.patch(f"{API_URL}/urls/{url_id}", headers={"Authorization": f"Bearer {access_token_b}"}, json={"is_active": False})
    print(f"User B PATCH status: {r_patch.status_code} - {r_patch.text}")
    assert r_patch.status_code == 403, f"Expected 403, got {r_patch.status_code}"
    
    r_delete = requests.delete(f"{API_URL}/urls/{url_id}", headers={"Authorization": f"Bearer {access_token_b}"})
    print(f"User B DELETE status: {r_delete.status_code} - {r_delete.text}")
    assert r_delete.status_code == 403, f"Expected 403, got {r_delete.status_code}"
    
    print("\n--- 4. Dashboard endpoint supports search, sort, pagination together ---")
    urls_to_create = [
        {"original_url": "https://test1.com"},
        {"original_url": "https://test2.com"},
        {"original_url": "https://somethingelse.com"},
        {"original_url": "https://test3.com"},
    ]
    for u in urls_to_create:
        requests.post(f"{API_URL}/urls", headers={"Authorization": f"Bearer {access_token_a}"}, json=u)
        time.sleep(0.1) 
        
    r_dash = requests.get(f"{API_URL}/urls?q=test&sort_by=created_at&order=desc&page=1&page_size=2", headers={"Authorization": f"Bearer {access_token_a}"})
    assert r_dash.status_code == 200
    results = r_dash.json()
    assert len(results) == 2, f"Expected 2 results, got {len(results)}"
    
    print("Page 1 Results:")
    for r in results:
        print(f" - {r['original_url']} (created_at: {r['created_at']})")
        assert "test" in r["original_url"] or "test" in r["short_code"]
        
    r_dash2 = requests.get(f"{API_URL}/urls?q=test&sort_by=created_at&order=desc&page=2&page_size=2", headers={"Authorization": f"Bearer {access_token_a}"})
    assert r_dash2.status_code == 200
    results2 = r_dash2.json()
    assert len(results2) == 1, f"Expected 1 result, got {len(results2)}"
    print("Page 2 Results:")
    for r in results2:
        print(f" - {r['original_url']} (created_at: {r['created_at']})")
        
    print("\nAll verifications passed successfully!")

if __name__ == "__main__":
    test()
