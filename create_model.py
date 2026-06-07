"""Creates a demo Isolation Forest model and saves it as model.pkl"""
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest

# Train on synthetic normal data
np.random.seed(42)
X_train = np.column_stack([
    np.random.normal(25, 15, 1000).clip(0, 85),    # cpu_percent
    np.random.normal(512, 200, 1000).clip(50, 3000),  # memory_mb
    np.random.exponential(50000, 1000).clip(0, 800000),  # net_bytes_sent
    np.random.normal(50, 30, 1000).clip(0, 850),  # disk_read_ops
])

model = IsolationForest(contamination=0.05, random_state=42, n_jobs=-1)
model.fit(X_train)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

print("model.pkl created successfully")
