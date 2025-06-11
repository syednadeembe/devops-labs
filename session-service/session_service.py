from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
import os
import time

from kubernetes import client, config

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # OR specify "http://13.200.227.6:30090"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

    lab_data = lab_resp.json()
    if "message" not in lab_data:
        return {"error": "Lab session creation failed"}

    session_id = lab_data["message"].split("session ID: ")[-1]
    namespace = f"lab-{session_id}"

    # 3. Wait for ttyd pod to become ready
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    pod_ready = False

    for _ in range(20):  # wait up to 20 seconds
        pods = v1.list_namespaced_pod(namespace=namespace)
        for pod in pods.items:
            if "ttyd" in pod.metadata.name:
                conditions = pod.status.conditions or []
                ready = any(c.type == "Ready" and c.status == "True" for c in conditions)
                if pod.status.phase == "Running" and ready:
                    pod_ready = True
                    break
        if pod_ready:
            break
        time.sleep(1)

    return {"message": f"Lab started with session ID: {session_id}"}

