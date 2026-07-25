def test_create_url_returns_short_code(client, auth_headers_for_two_users):
    headers, _ = auth_headers_for_two_users
    response = client.post("/api/v1/urls", json={"original_url": "https://example.com"}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert "short_code" in body
    assert body["original_url"] == "https://example.com/"

def test_create_url_rejects_invalid_url(client, auth_headers_for_two_users):
    headers, _ = auth_headers_for_two_users
    response = client.post("/api/v1/urls", json={"original_url": "not-a-url"}, headers=headers)
    assert response.status_code == 422

def test_redirect_follows_to_original_url(client, auth_headers_for_two_users):
    headers, _ = auth_headers_for_two_users
    create = client.post("/api/v1/urls", json={"original_url": "https://example.com"}, headers=headers)
    short_code = create.json()["short_code"]
    response = client.get(f"/{short_code}", follow_redirects=False)
    # Using TestClient from httpx, a redirect is 307 or 302
    assert response.status_code in (302, 307)
    assert response.headers["location"] == "https://example.com/"

def test_redirect_returns_404_for_unknown_code(client):
    response = client.get("/doesnotexist")
    assert response.status_code == 404
