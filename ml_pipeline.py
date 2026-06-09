"""
Train an IsolationForest on data/live_data.json collected by collect_data.py.
Saves model to model.pkl.
"""

import json
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
import joblib

DATA_PATH       = "data/live_data.json"
MODEL_PATH      = "model.pkl"
CONTAMINATION   = 0.05
FEATURE_COLUMNS = ["cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops"]


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    with open(path) as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    df = df.dropna(subset=FEATURE_COLUMNS)
    # Clip extreme outliers (top 0.1%) to reduce noise from kernel bursts
    for col in FEATURE_COLUMNS:
        df[col] = df[col].clip(upper=df[col].quantile(0.999))
    return df


def train(df: pd.DataFrame) -> IsolationForest:
    model = IsolationForest(
        n_estimators=200,
        contamination=CONTAMINATION,
        random_state=42,
        max_samples="auto",
        n_jobs=-1,
    )
    model.fit(df[FEATURE_COLUMNS].values)
    return model


def run_anomaly_detection(df: pd.DataFrame, model: IsolationForest):
    X = df[FEATURE_COLUMNS].values
    df = df.copy()
    df["anomaly_score"] = model.score_samples(X)
    df["is_anomaly"]    = model.predict(X) == -1
    return df, df[df["is_anomaly"]].reset_index(drop=True)


if __name__ == "__main__":
    import os

    print(f"Loading {DATA_PATH}...")
    df = load_data()
    print(f"  {len(df)} records, {df['process_name'].nunique()} unique processes")
    print(f"  Feature ranges:")
    for col in FEATURE_COLUMNS:
        print(f"    {col}: [{df[col].min():.2f}, {df[col].max():.2f}]  mean={df[col].mean():.2f}")

    print("\nTraining IsolationForest...")
    model = train(df)
    joblib.dump(model, MODEL_PATH)
    size_kb = os.path.getsize(MODEL_PATH) / 1024
    print(f"Model saved to {MODEL_PATH} ({size_kb:.1f} KB)")
    print(f"Decision threshold (offset_): {model.offset_:.4f}")

    df_all, df_anom = run_anomaly_detection(df, model)
    print(f"Anomaly rate on training data: {len(df_anom)}/{len(df_all)} ({len(df_anom)/len(df_all)*100:.1f}%)")
    print("\nTop 5 anomalous processes:")
    print(df_anom.nsmallest(5, "anomaly_score")[
        ["process_name", "pid", "cpu_percent", "memory_mb", "net_bytes_sent", "disk_read_ops", "anomaly_score"]
    ].to_string(index=False))
