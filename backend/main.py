from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt
from datetime import datetime, timedelta
from kubernetes import client, config
import uuid

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT setup
SECRET_KEY = "supersecretkey"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# Kubernetes clients
config.load_incluster_config()
core_v1 = client.CoreV1Api()
rbac_v1 = client.RbacAuthorizationV1Api()
networking_v1 = client.NetworkingV1Api()

@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username != "admin" or form_data.password != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": form_data.username, "exp": expire}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/")
def root():
    return {"message": "DevOps Lab backend running"}

@app.get("/start-lab")
def start_lab(token: str = Depends(oauth2_scheme)):
    session_id = str(uuid.uuid4())[:8]
    create_lab(session_id)
    return {"message": f"Lab started with session ID: {session_id}"}


def create_lab(session_id: str):
    namespace = f"lab-{session_id}"
    core_v1.create_namespace(client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace)))

    # Pod
    pod_manifest = client.V1Pod(
        metadata=client.V1ObjectMeta(name="lab-terminal", labels={"app": "lab-terminal"}),
        spec=client.V1PodSpec(
            containers=[
                client.V1Container(
                    name="ttyd",
                    image="syednadeembe/ttyd-lab:latest",
                    ports=[client.V1ContainerPort(container_port=7681)],
                    command=["ttyd", "--writable", "bash"]
                )
            ]
        )
    )
    core_v1.create_namespaced_pod(namespace=namespace, body=pod_manifest)

    # Service
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name="lab-terminal-service"),
        spec=client.V1ServiceSpec(
            selector={"app": "lab-terminal"},
            ports=[client.V1ServicePort(port=80, target_port=7681)],
            type="ClusterIP"
        )
    )
    core_v1.create_namespaced_service(namespace=namespace, body=service)

    # Ingress
    ingress = client.V1Ingress(
        metadata=client.V1ObjectMeta(name="lab-terminal-ingress", annotations={
            "nginx.ingress.kubernetes.io/rewrite-target": "/"
        }),
        spec=client.V1IngressSpec(
            ingress_class_name="nginx",
            rules=[
                client.V1IngressRule(
                    http=client.V1HTTPIngressRuleValue(
                        paths=[
                            client.V1HTTPIngressPath(
                                path=f"/labs/{session_id}",
                                path_type="Prefix",
                                backend=client.V1IngressBackend(
                                    service=client.V1IngressServiceBackend(
                                        name="lab-terminal-service",
                                        port=client.V1ServiceBackendPort(number=80)
                                    )
                                )
                            )
                        ]
                    )
                )
            ]
        )
    )
    networking_v1.create_namespaced_ingress(namespace=namespace, body=ingress)

    # RBAC
    role_binding = client.V1RoleBinding(
        metadata=client.V1ObjectMeta(name="lab-access-binding"),
        subjects=[
            {
                "kind": "ServiceAccount",
                "name": "default",
                "namespace": namespace
            }
        ],
        role_ref=client.V1RoleRef(
            kind="ClusterRole",
            name="admin",
            api_group="rbac.authorization.k8s.io"
        )
    )
    rbac_v1.create_namespaced_role_binding(namespace=namespace, body=role_binding)

