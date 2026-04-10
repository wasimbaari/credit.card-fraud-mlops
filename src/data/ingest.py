import pandas as pd
import yaml
from sklearn.model_selection import train_test_split
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(config_path="configs/base.yaml"):
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

def ingest_and_split_data():
    config = load_config()
    train_path = Path(config['data']['raw_train_path'])
    
    if not train_path.exists():
        logging.error(f"File not found at {train_path}.")
        return None, None, None, None

    logging.info(f"Loading data from {train_path}")
    df = pd.read_csv(train_path)
    
    if 'Unnamed: 0' in df.columns:
        df = df.drop(columns=['Unnamed: 0'])

    target = config['model']['target_column']
    X = df.drop(columns=[target])
    y = df[target]

    logging.info("Splitting data for local validation...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, 
        test_size=config['data']['test_size'], 
        random_state=config['data']['random_state'],
        stratify=y 
    )
    
    logging.info(f"Train shape: {X_train.shape}, Validation shape: {X_test.shape}")
    return X_train, X_test, y_train, y_test

if __name__ == "__main__":
    ingest_and_split_data()
