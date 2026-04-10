import os
import yaml
import mlflow
import logging
import pandas as pd
from pathlib import Path
from sklearn.metrics import precision_score, recall_score, f1_score, average_precision_score
from imblearn.over_sampling import SMOTE
from xgboost import XGBClassifier

from src.data.ingest import ingest_and_split_data
from src.features.feature_engineering import FraudFeatureEngineer

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path="configs/base.yaml"):
    """Loads the project configuration from a YAML file."""
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def train_model():
    """Executes the end-to-end training pipeline with MLflow tracking."""
    config = load_config()
    
    # 1. Ingest Data
    logging.info("Ingesting data...")
    X_train, X_val, y_train, y_val = ingest_and_split_data()
    
    # Handle subsampling if dev_mode is active
    if config.get('data', {}).get('dev_mode'):
        sample_size = config['data']['dev_sample_size']
        logging.info(f"DEV MODE ACTIVE: Subsampling {sample_size} rows.")
        X_train = X_train.sample(n=sample_size, random_state=42)
        y_train = y_train.loc[X_train.index]
        X_val = X_val.sample(n=int(sample_size * 0.2), random_state=42)
        y_val = y_val.loc[X_val.index]

    # 2. Feature Engineering
    logging.info("Applying Feature Engineering...")
    fe = FraudFeatureEngineer()
    X_train_fe = fe.build_features(X_train)
    X_val_fe = fe.build_features(X_val)

    # Column alignment to ensure train and validation sets match
    X_val_fe = X_val_fe.reindex(columns=X_train_fe.columns, fill_value=0)

    # 3. SMOTE (Applied ONLY to training data)
    logging.info("Applying SMOTE to training data...")
    smote = SMOTE(sampling_strategy=config['model']['smote_sampling_strategy'], random_state=42)
    X_train_resampled, y_train_resampled = smote.fit_resample(X_train_fe, y_train)
    logging.info(f"Pre-SMOTE fraud cases: {sum(y_train)}, Post-SMOTE fraud cases: {sum(y_train_resampled)}")

    # 4. MLflow Experiment Tracking
    # Local SQLite for metadata; artifact storage is defined in base.yaml
    mlflow.set_tracking_uri("sqlite:///mlflow.db")
    mlflow.set_experiment(config['project']['name'])
    
    # Retrieve S3 artifact path from config
    artifact_location = config.get('aws', {}).get('mlflow_artifact_path')
    
    with mlflow.start_run(run_name="xgb_smote_s3_ready"):
        logging.info("Training XGBoost model...")
        
        xgb_params = config['model']['xgb_params']
        mlflow.log_params(xgb_params)
        mlflow.log_param("smote_strategy", config['model']['smote_sampling_strategy'])
        mlflow.log_param("dev_mode", config['data']['dev_mode'])

        model = XGBClassifier(**xgb_params, random_state=42)
        model.fit(X_train_resampled, y_train_resampled)

        logging.info("Evaluating model...")
        y_pred = model.predict(X_val_fe)
        y_prob = model.predict_proba(X_val_fe)[:, 1]

        # Fraud detection metrics focus on Recall and PR-AUC
        metrics = {
            "precision": precision_score(y_val, y_pred, zero_division=0),
            "recall": recall_score(y_val, y_pred, zero_division=0),
            "f1": f1_score(y_val, y_pred, zero_division=0),
            "pr_auc": average_precision_score(y_val, y_prob)
        }
        
        mlflow.log_metrics(metrics)
        logging.info(f"Validation Metrics: {metrics}")

        # 5. Model Registry and Artifact Logging
        # Logging with a registered model name enables version control in the MLflow Model Registry
        logging.info(f"Logging model artifacts to: {artifact_location or 'local storage'}")
        
        mlflow.xgboost.log_model(
            xgb_model=model, 
            artifact_path="model",
            registered_model_name="fraud-detection-model"
        )
        
        logging.info("Model training and logging complete. Ready for Model Registry.")

if __name__ == "__main__":
    train_model()