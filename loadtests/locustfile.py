import uuid
from locust import HttpUser, task, between

class LinkForgeUser(HttpUser):
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        self.short_codes = []
        
        # Create a unique user for this locust instance
        user_hash = uuid.uuid4().hex[:8]
        username = f"user_{user_hash}"
        email = f"{username}@example.com"
        password = "password123"
        
        # Register
        self.client.post("/api/v1/auth/register", json={
            "username": username,
            "email": email,
            "password": password
        })
        
        # Login
        login_res = self.client.post("/api/v1/auth/login", json={
            "email": email,
            "password": password
        })
        
        if login_res.status_code == 200:
            token = login_res.json()["access_token"]
            self.client.headers.update({"Authorization": f"Bearer {token}"})
            
        # Create initial URL
        response = self.client.post("/api/v1/urls", json={"original_url": "https://example.com"})
        if response.status_code == 201:
            self.short_codes.append(response.json()["short_code"])

    @task(9)
    def follow_redirect(self):
        if self.short_codes:
            code = self.short_codes[0]
            self.client.get(f"/{code}", name="/[short_code]", allow_redirects=False)

    @task(1)
    def create_url(self):
        response = self.client.post("/api/v1/urls", json={"original_url": "https://example.com/page"})
        if response.status_code == 201:
            self.short_codes.append(response.json()["short_code"])
