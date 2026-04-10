import os
from pathlib import Path

def automate_ml_services():
    print("🚀 Generating Manifests for MLflow and KServe...")
    base_dir = Path("fraud-mlops-project")
    k8s_dir = base_dir / "infra" / "kubernetes"
    (k8s_dir / "mlflow").mkdir(parents=True, exist_ok=True)
    (k8s_dir / "kserve").mkdir(parents=True, exist_ok=True)

    # 1. MLflow Deployment Manifest
    # Note: We use environmental variables to point to S3
    mlflow_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: mlflow-server
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mlflow
  template:
    metadata:
      labels:
        app: mlflow
    spec:
      containers:
      - name: mlflow
        image: ghcr.io/mlflow/mlflow:latest
        ports:
        - containerPort: 5000
        env:
        - name: AWS_ACCESS_KEY_ID
          valueFrom: { secretKeyRef: { name: aws-secrets, key: access-key } }
        - name: AWS_SECRET_ACCESS_KEY
          valueFrom: { secretKeyRef: { name: aws-secrets, key: secret-key } }
        command: ["mlflow", "server"]
        args: [
          "--host", "0.0.0.0",
          "--port", "5000",
          "--backend-store-uri", "sqlite:///mlflow.db", # In prod, swap for postgres://
          "--default-artifact-root", "s3://wasim-fraud-mlops-artifacts/mlflow/"
        ]
---
apiVersion: v1
kind: Service
metadata:
  name: mlflow-service
spec:
  type: LoadBalancer
  ports:
  - port: 80
    targetPort: 5000
  selector:
    app: mlflow
"""

    # 2. KServe InferenceService Manifest
    # This is how you deploy the actual Fraud Detection model
    kserve_yaml = """apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: fraud-detection
spec:
  predictor:
    xgboost:
      storageUri: "s3://wasim-fraud-mlops-artifacts/mlflow/1/your-run-id/artifacts/model"
      resources:
        limits:
          cpu: "1"
          memory: "2Gi"
"""

    # Write files
    with open(k8s_dir / "mlflow" / "mlflow-server.yaml", "w") as f:
        f.write(mlflow_yaml)
    with open(k8s_dir / "kserve" / "inference-service.yaml", "w") as f:
        f.write(kserve_yaml)
    
    print(f"✅ Created MLflow manifests in: {k8s_dir}/mlflow")
    print(f"✅ Created KServe manifests in: {k8s_dir}/kserve")

if __name__ == "__main__":
    automate_ml_services()