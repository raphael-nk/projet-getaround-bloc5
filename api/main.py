"""
GetAround Pricing API — FastAPI
================================
Endpoints:
  GET  /health   — API and model status
  POST /predict  — Daily rental price predictions
  GET  /docs     — Swagger UI (auto-generated)
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from fastapi import FastAPI
from pydantic import BaseModel, Field

API_DIR = Path(__file__).resolve().parent
MODEL_PATH = API_DIR / "models" / "best_pricing_model_xgb.pkl"

FEATURE_COLUMNS = [
    "model_key",
    "mileage",
    "engine_power",
    "fuel",
    "paint_color",
    "car_type",
    "private_parking_available",
    "has_gps",
    "has_air_conditioning",
    "automatic_car",
    "has_getaround_connect",
    "has_speed_regulator",
    "winter_tires",
]

_model = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model
    if MODEL_PATH.exists():
        _model = joblib.load(MODEL_PATH)
    yield
    _model = None


app = FastAPI(
    title="GetAround Pricing API",
    description="ML API for optimal daily rental price prediction (GetAround / Jedha).",
    version="1.0.0",
    lifespan=lifespan,
)


class VehicleInput(BaseModel):
    model_key: str
    mileage: float = Field(..., ge=0)
    engine_power: float = Field(..., ge=0)
    fuel: str
    paint_color: str
    car_type: str
    private_parking_available: bool
    has_gps: bool
    has_air_conditioning: bool
    automatic_car: bool
    has_getaround_connect: bool
    has_speed_regulator: bool
    winter_tires: bool


class PredictRequest(BaseModel):
    input: list[VehicleInput]


class PredictResponse(BaseModel):
    prediction: list[float]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str


@app.get("/", tags=["meta"])
def root():
    return {
        "service": "GetAround Pricing API",
        "docs": "/docs",
        "health": "/health",
        "predict": "POST /predict",
    }


@app.get("/health", response_model=HealthResponse, tags=["meta"])
def health():
    return HealthResponse(
        status="ok" if _model is not None else "degraded",
        model_loaded=_model is not None,
        model_path=str(MODEL_PATH),
    )


@app.post("/predict", response_model=PredictResponse, tags=["ml"])
def predict(body: PredictRequest):
    rows: list[dict[str, Any]] = [v.model_dump() for v in body.input]
    df = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    preds = _model.predict(df)
    return PredictResponse(prediction=[float(p) for p in preds])
