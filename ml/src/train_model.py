
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_PATH = BASE_DIR / "data" / "raw" / "telemetry.csv"
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)

# Load the synthetic dataset.
df = pd.read_csv(DATA_PATH)

FEATURES = [
    "temperature",
    "humidity",
    "vibration",
    "voltage",
    "current",
    "power",
    "cpu_utilization",
    "cpu_temperature",
]

X = df[FEATURES].copy()
y_true = df["is_abnormal"]

# Standardize features so they are on comparable scales.
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train without using condition or is_abnormal labels.
model = IsolationForest(
    n_estimators=200,
    contamination=0.4167,
    random_state=42,
)
model.fit(X_scaled)

# Isolation Forest: -1 = anomaly, 1 = normal.
predictions = model.predict(X_scaled)
df["predicted_anomaly"] = (predictions == -1).astype(int)

# Anomaly score: larger values mean more anomalous.
df["anomaly_score"] = -model.score_samples(X_scaled)

print("\nClassification report (synthetic reference labels):")
print(classification_report(
    y_true,
    df["predicted_anomaly"],
    target_names=["Normal", "Abnormal"],
    zero_division=0,
))

print("Confusion matrix [rows=true, columns=predicted]:")
print(confusion_matrix(y_true, df["predicted_anomaly"]))

# Save the model artifacts and scored dataset.
joblib.dump(
    {"model": model, "scaler": scaler, "features": FEATURES},
    MODEL_DIR / "isolation_forest.joblib",
)
df.to_csv(BASE_DIR / "data" / "processed" / "scored_telemetry.csv", index=False)

print(f"\nModel saved to: {MODEL_DIR / 'isolation_forest.joblib'}")
print("Scored dataset saved to data/processed/scored_telemetry.csv")

# Visualize CPU temperature and detected anomalies.
plt.figure(figsize=(13, 5))
plt.plot(df["cpu_temperature"].to_numpy(), label="CPU temperature", linewidth=1)
anomalies = df["predicted_anomaly"] == 1
plt.scatter(
    df.index[anomalies],
    df.loc[anomalies, "cpu_temperature"],
    label="Detected anomaly",
    s=12,
)
plt.xlabel("Minute")
plt.ylabel("CPU temperature (°C)")
plt.title("CloudSense-AI: Isolation Forest anomaly detection")
plt.legend()
plt.tight_layout()

plot_path = BASE_DIR / "data" / "processed" / "anomaly_plot.png"
plt.savefig(plot_path, dpi=150)
print(f"Plot saved to: {plot_path}")
plt.show()
