
from pathlib import Path

import numpy as np
import pandas as pd


def generate_telemetry():
    rng = np.random.default_rng(42)
    n = 1440

    timestamps = pd.date_range(
        start="2026-10-12 00:00:00",
        periods=n,
        freq="min",
    )

    condition = np.full(n, "normal", dtype=object)
    condition[480:720] = "high_load"
    condition[720:840] = "cooling_degradation"
    condition[840:960] = "vibration_anomaly"
    condition[960:1080] = "power_anomaly"

    # Simulate CPU workload.
    minute = np.arange(n)
    cpu = 35 + 12 * np.sin(2 * np.pi * minute / 1440)
    cpu += rng.normal(0, 5, n)
    cpu = np.clip(cpu, 5, 85)

    high_load = condition == "high_load"
    cpu[high_load] = np.clip(
        rng.normal(88, 5, high_load.sum()), 65, 100
    )

    # Temperature and humidity.
    temperature = 27 + 0.10 * cpu + rng.normal(0, 1.5, n)
    humidity = np.clip(rng.normal(52, 5, n), 30, 75)

    cooling = condition == "cooling_degradation"
    temperature[cooling] += np.linspace(2, 13, cooling.sum())

    cpu_temperature = (
        30 + 0.48 * cpu
        + 0.35 * (temperature - 30)
        + rng.normal(0, 2, n)
    )

    # Simulated vibration in g.
    vibration = np.abs(rng.normal(0.025, 0.006, n))
    vibration_problem = condition == "vibration_anomaly"
    vibration[vibration_problem] = np.abs(
        rng.normal(0.12, 0.025, vibration_problem.sum())
    )

    # Simulated electrical measurements.
    voltage = rng.normal(12.0, 0.15, n)
    current = 0.65 + 0.012 * cpu + rng.normal(0, 0.08, n)

    power_problem = condition == "power_anomaly"
    voltage[power_problem] -= rng.normal(
        1.2, 0.25, power_problem.sum()
    )
    current[power_problem] += rng.normal(
        0.5, 0.1, power_problem.sum()
    )

    power = voltage * current

    df = pd.DataFrame({
        "timestamp": timestamps,
        "device_id": "server-001",
        "temperature": np.round(temperature, 2),
        "humidity": np.round(humidity, 2),
        "vibration": np.round(vibration, 4),
        "voltage": np.round(voltage, 2),
        "current": np.round(current, 3),
        "power": np.round(power, 2),
        "cpu_utilization": np.round(cpu, 2),
        "cpu_temperature": np.round(cpu_temperature, 2),
        "condition": condition,
    })

    # Reference labels are for evaluation only.
    df["is_abnormal"] = (df["condition"] != "normal").astype(int)

    output = (
        Path(__file__).resolve().parents[1]
        / "data" / "raw" / "telemetry.csv"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)

    print(f"\nDataset saved to: {output}")
    print(f"Total records: {len(df)}")
    print("\nOperating conditions:")
    print(df["condition"].value_counts())
    print("\nSample records:")
    print(df.head())
    print("\nMissing values:")
    print(df.isnull().sum())


if __name__ == "__main__":
    generate_telemetry()
