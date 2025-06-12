
# DevOps Lab Platform 🧪

A Kubernetes-powered platform for **interview-based DevOps hands-on labs**, allowing users to simulate real-world scenarios through browser-accessible terminals backed by isolated lab environments.

---

## 🏗️ System Architecture

```plaintext
                       +------------------------+
                       |      Web Frontend      |
                       |   (React / HTML / JS)  |
                       +-----------+------------+
                                   |
                                   v
                       +------------------------+
                       |     Session Service     |
                       |  (FastAPI in Kubernetes)|
                       +-----------+------------+
                                   |
                  ┌─────────────────────────────────────────────┐
                  | Authenticated Request to Backend API        |
                  └─────────────────────────────────────────────┘
                                   |
                          [Generates Unique Lab ID]
                                   |
                                   v
       +------------------------------------------------------+
       |  Kubernetes Cluster (k3s on EC2)                      |
       |  Namespace: lab-<session_id>                          |
       |                                                      |
       |  +---------------+    +---------------------------+  |
       |  |  ttyd Pod     |    |  ClusterIP Service        |  |
       |  | (browser bash)|<-->|  Exposes port 7681        |  |
       |  +---------------+    +---------------------------+  |
       |        |                          ↑                  |
       |        +----> Ingress Path: /labs/<session_id> ------+
       +------------------------------------------------------+

```

---

## 🧪 Features

- **Auto-Creation of Labs**: On API call, a namespace, pod, service, ingress, and RBAC policy are created dynamically.
- **Multi-User Browser Terminals**: Isolated shell terminals for each session using [`ttyd`](https://github.com/tsl0922/ttyd).
- **Authentication Support**: JWT-based authentication layer for secure access.
- **In-Cluster Backend**: Session creation and authentication services run as Kubernetes pods.
- **TTL Cleanup Ready**: Labs can auto-expire (via TTL controller pod - optional).
- **Ingress Routing**: Users access their terminals via `/labs/<session_id>`.

---

## 🚀 Getting Started

### ✅ 1. Requirements

- EC2 instance with K3s installed
- `kubectl` + `helm` configured
- DockerHub (to push your images)
- Domain or public IP
- helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
- helm repo update

helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.publishService.enabled=true \
  --set controller.service.type=ClusterIP
---

### 🐳 2. Build & Push Docker Images

#### Backend (Lab Manager):
```bash
cd backend
docker build -t <your-dockerhub>/lab-backend:latest -f Dockerfile.backend .
docker push <your-dockerhub>/lab-backend:latest
```

#### Session Service:
```bash
cd session-service
docker build -t <your-dockerhub>/session-service:latest -f Dockerfile.session .
docker push <your-dockerhub>/session-service:latest
```

#### ttyd (Terminal Image):
```bash
cd docker
docker build -t <your-dockerhub>/ttyd-lab:latest -f Dockerfile.ttyd .
docker push <your-dockerhub>/ttyd-lab:latest
```

---

### ⚙️ 3. Deploy Services in Kubernetes

#### a. Ingress Controller (NGINX)
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx   --namespace ingress-nginx --create-namespace   --set controller.service.type=NodePort   --set controller.service.nodePorts.http=30082   --set controller.service.nodePorts.https=30443
```

#### b. Deploy Backend Services
Edit and apply Kubernetes YAMLs:
- `lab-backend.yaml`
- `session-service.yaml`
- `ttl-cleaner.yaml` *(optional)*

Update image names, ports, and `env` variables as needed.

---

## 🔐 Authentication

- Backend exposes `/token` for login
- Frontend should obtain token via:
```bash
curl -X POST http://<IP>:<PORT>/token -d "username=admin&password=admin"
```

- Use the token in `Authorization` header for `/api/lab-session` endpoint.

---

## 🖥️ Using the Platform

### 🌐 Start a Lab from Browser

1. Login via token:
   ```http
   POST /token → returns JWT
   ```

2. Create session:
   ```http
   GET /api/lab-session (with Bearer token)
   ```

3. Access browser terminal:
   ```
   http://<NodeIP>:30082/labs/<session_id>
   ```

---

## 🧼 Auto Cleanup (Optional)

- TTL cleaner pod periodically deletes labs older than N minutes.
- Deploy `ttl-cleaner.yaml` with `cronjob` or `infinite loop` python.

---

## 🤝 Contributors

- [Syed Nadeem](https://github.com/syednadeem) – System design & architecture

---

