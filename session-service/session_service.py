from fastapi import FastAPI
import requests

app = FastAPI()

BACKEND_URL = "http://lab-backend.devops-labs.svc.cluster.local"

@app.get("/api/lab-session")
def create_lab():
    # 1. Get JWT token
    login_resp = requests.post(f"{BACKEND_URL}/token", data={"username": "admin", "password": "admin"})
    token = login_resp.json().get("access_token")
    if not token:
        return {"error": "Failed to authenticate with backend"}

    # 2. Start lab session
    lab_resp = requests.get(
        f"{BACKEND_URL}/start-lab",
        headers={"Authorization": f"Bearer {token}"}
    )

    return lab_resp.json()
