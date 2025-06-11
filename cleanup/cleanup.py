from kubernetes import client, config
from datetime import datetime, timezone

config.load_incluster_config()
v1 = client.CoreV1Api()

for ns in v1.list_namespace().items:
    if ns.metadata.name.startswith("lab-"):
        age = datetime.now(timezone.utc) - ns.metadata.creation_timestamp
        if age.total_seconds() > 3600:
            print(f"Deleting namespace: {ns.metadata.name}")
            v1.delete_namespace(ns.metadata.name)
