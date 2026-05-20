"""
GetAround Pricing API — FastAPI
================================
Endpoints:
  GET  /health   — API and model status
  POST /predict  — Daily rental price predictions
  GET  /docs     — Swagger UI (auto-generated)

Model loading: MLflow production run (if server reachable), else local joblib/pkl.
"""

from __future__ import annotations

import logging
import os
import socket
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal
from urllib.parse import urlparse

import joblib
import mlflow
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from mlflow.tracking import MlflowClient
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

API_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = API_DIR.parent
MODEL_PATH = API_DIR / "models" / "best_pricing_model_xgb.pkl"

load_dotenv(PROJECT_ROOT / ".env")

# Fail fast to local model when MLflow server is down
os.environ.setdefault("MLFLOW_HTTP_REQUEST_TIMEOUT", "5")

MLFLOW_SERVER_URI = os.getenv("MLFLOW_SERVER_URI", "http://127.0.0.1:5000")
MLFLOW_EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT", "getaround-pricing")
MLFLOW_PRODUCTION_RUN_ID = os.getenv("MLFLOW_PRODUCTION_RUN_ID", "").strip()
MLFLOW_PRODUCTION_RUN_NAME = os.getenv(
    "MLFLOW_PRODUCTION_RUN_NAME", "production-best-model"
)

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
_model_source: Literal["mlflow", "local", "none"] = "none"
_model_uri: str = str(MODEL_PATH)
_mlflow_run_id: str | None = None


def _mlflow_server_reachable(timeout_s: float = 2.0) -> bool:
    parsed = urlparse(MLFLOW_SERVER_URI)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout_s):
            return True
    except OSError:
        return False


def _resolve_production_run_id(client: MlflowClient) -> str | None:
    if MLFLOW_PRODUCTION_RUN_ID:
        return MLFLOW_PRODUCTION_RUN_ID

    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENT)
    if experiment is None:
        logger.warning("MLflow experiment '%s' not found", MLFLOW_EXPERIMENT)
        return None

    runs = client.search_runs(
        [experiment.experiment_id],
        filter_string="tags.stage = 'production'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )
    if runs:
        return runs[0].info.run_id

    runs = client.search_runs(
        [experiment.experiment_id],
        filter_string=f"tags.mlflow.runName = '{MLFLOW_PRODUCTION_RUN_NAME}'",
        order_by=["attribute.start_time DESC"],
        max_results=1,
    )
    if runs:
        return runs[0].info.run_id

    return None


def _load_model_from_mlflow() -> Any | None:
    if not _mlflow_server_reachable():
        logger.warning("MLflow server not reachable at %s", MLFLOW_SERVER_URI)
        return None

    try:
        mlflow.set_tracking_uri(MLFLOW_SERVER_URI)
        client = MlflowClient(tracking_uri=MLFLOW_SERVER_URI)

        run_id = _resolve_production_run_id(client)
        if not run_id:
            logger.warning("No production MLflow run found")
            return None

        model_uri = f"runs:/{run_id}/model"
        model = mlflow.sklearn.load_model(model_uri)
        global _model_uri, _mlflow_run_id
        _model_uri = model_uri
        _mlflow_run_id = run_id
        logger.info("Loaded model from MLflow run %s", run_id)
        return model
    except Exception as exc:
        logger.warning("MLflow load failed (%s), will try local file", exc)
        return None


def _load_model_from_local() -> Any | None:
    if not MODEL_PATH.exists():
        logger.warning("Local model not found at %s", MODEL_PATH)
        return None
    global _model_uri, _mlflow_run_id
    _model_uri = str(MODEL_PATH)
    _mlflow_run_id = None
    logger.info("Loaded model from %s", MODEL_PATH)
    return joblib.load(MODEL_PATH)


def load_pricing_model() -> tuple[Any | None, Literal["mlflow", "local", "none"]]:
    model = _load_model_from_mlflow()
    if model is not None:
        return model, "mlflow"

    model = _load_model_from_local()
    if model is not None:
        return model, "local"

    return None, "none"


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _model_source
    _model, _model_source = load_pricing_model()
    yield
    _model = None
    _model_source = "none"


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
    model_source: Literal["mlflow", "local", "none"]
    model_uri: str
    mlflow_run_id: str | None = None
    mlflow_server_uri: str | None = None


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
        model_source=_model_source,
        model_uri=_model_uri,
        mlflow_run_id=_mlflow_run_id,
        mlflow_server_uri=MLFLOW_SERVER_URI if _model_source == "mlflow" else None,
    )


@app.post("/predict", response_model=PredictResponse, tags=["ml"])
def predict(body: PredictRequest):
    if _model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded. Start MLflow server or export api/models/best_pricing_model_xgb.pkl",
        )
    rows: list[dict[str, Any]] = [v.model_dump() for v in body.input]
    df = pd.DataFrame(rows, columns=FEATURE_COLUMNS)
    preds = _model.predict(df)
    return PredictResponse(prediction=[float(p) for p in preds])
