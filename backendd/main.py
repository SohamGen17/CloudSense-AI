
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware 

# --------------------------------------------------
# Paths and database
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "ml" / "models" / "isolation_forest.joblib"
DATABASE_PATH = BASE_DIR / "backendd" / "cloudsense.db"

DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)
Base = declarative_base()


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    device_id = Column(String, index=True, nullable=False)
    temperature = Column(Float, nullable=False)
    humidity = Column(Float, nullable=False)
    vibration = Column(Float, nullable=False)
    voltage = Column(Float, nullable=False)
    current = Column(Float, nullable=False)
    power = Column(Float, nullable=False)
    cpu_utilization = Column(Float, nullable=False)
    cpu_temperature = Column(Float, nullable=False)
    anomaly = Column(Boolean, nullable=False)
    anomaly_score = Column(Float, nullable=False)
    risk_level = Column(String, nullable=False)


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------
# Load trained ML model
# --------------------------------------------------

artifacts = joblib.load(MODEL_PATH)
model = artifacts["model"]
scaler = artifacts["scaler"]
FEATURES = artifacts["features"]


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="CloudSense-AI API",
    description="ML-based infrastructure anomaly detection",
    version="1.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Telemetry(BaseModel):
    device_id: str = "server-001"
    temperature: float = Field(ge=-20, le=100)
    humidity: float = Field(ge=0, le=100)
    vibration: float = Field(ge=0)
    voltage: float = Field(ge=0)
    current: float = Field(ge=0)
    power: float = Field(ge=0)
    cpu_utilization: float = Field(ge=0, le=100)
    cpu_temperature: float = Field(ge=-20, le=120)


def record_to_dict(record: TelemetryRecord):
    return {
        "id": record.id,
        "timestamp": record.timestamp.isoformat(),
        "device_id": record.device_id,
        "temperature": record.temperature,
        "humidity": record.humidity,
        "vibration": record.vibration,
        "voltage": record.voltage,
        "current": record.current,
        "power": record.power,
        "cpu_utilization": record.cpu_utilization,
        "cpu_temperature": record.cpu_temperature,
        "anomaly": record.anomaly,
        "anomaly_score": record.anomaly_score,
        "risk_level": record.risk_level,
    }


@app.get("/")
def root():
    return {
        "message": "CloudSense-AI API is running",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None,
        "database": "configured",
    }


# --------------------------------------------------
# Predict and save telemetry
# --------------------------------------------------

@app.post("/api/predict")
def predict(data: Telemetry, db: Session = Depends(get_db)):
    try:
        row = pd.DataFrame([data.model_dump()])[FEATURES]
        scaled = scaler.transform(row)

        prediction = int(model.predict(scaled)[0])
        anomaly_score = float(-model.score_samples(scaled)[0])
        is_anomaly = prediction == -1

        # This is a simplified flag-based status, not a
        # calibrated probability of equipment failure.
        risk_level = "HIGH" if is_anomaly else "LOW"

        record = TelemetryRecord(
            **data.model_dump(),
            anomaly=is_anomaly,
            anomaly_score=anomaly_score,
            risk_level=risk_level,
        )

        db.add(record)
        db.commit()
        db.refresh(record)

        result = record_to_dict(record)
        result["message"] = (
            "Unusual telemetry detected"
            if is_anomaly
            else "Telemetry appears normal"
        )
        return result

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Prediction or database save failed: {exc}",
        ) from exc


# --------------------------------------------------
# Dashboard endpoints
# --------------------------------------------------

@app.get("/api/telemetry/latest")
def latest_telemetry(db: Session = Depends(get_db)):
    record = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.id.desc())
        .first()
    )

    if record is None:
        return {"message": "No telemetry has been recorded yet"}

    return record_to_dict(record)


@app.get("/api/telemetry")
def telemetry_history(
    limit: int = Query(default=100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    records = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.id.desc())
        .limit(limit)
        .all()
    )

    return {
        "count": len(records),
        "records": [record_to_dict(r) for r in records],
    }


@app.get("/api/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(TelemetryRecord.id)).scalar() or 0
    anomalies = (
        db.query(func.count(TelemetryRecord.id))
        .filter(TelemetryRecord.anomaly.is_(True))
        .scalar()
        or 0
    )

    latest = (
        db.query(TelemetryRecord)
        .order_by(TelemetryRecord.id.desc())
        .first()
    )

    return {
        "total_readings": total,
        "anomaly_count": anomalies,
        "normal_count": total - anomalies,
        "anomaly_percentage": round(anomalies / total * 100, 2)
        if total else 0,
        "latest_reading": record_to_dict(latest) if latest else None,
    }
