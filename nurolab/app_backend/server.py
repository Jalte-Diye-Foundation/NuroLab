# File: nurolab/app_backend/server.py
# NuroLab Dashboard Backend — FastAPI + WebSocket + SQLite
#
# Run with (from the directory that CONTAINS nurolab/, i.e. the project root):
#   uvicorn nurolab.app_backend.server:app --reload --port 8000
#
# Install: pip install -r requirements.txt
# See README.md for full setup instructions.

from __future__ import annotations
from nurolab.processing.analytics import (
    alpha_beta_ratio, engagement_index, relaxation_index,
    cognitive_load_index, signal_quality_score
)
from fastapi.responses import Response
from nurolab.app_backend.report_generator import generate_report
import asyncio
import datetime
import json
import logging
from pathlib import Path
from typing import List

import numpy as np

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session as ORMSession

from nurolab.app_backend.models.database import Baseline, SessionLocal, get_db, init_db
from nurolab.app_backend.models.schemas import (
    BaselineStats,
    BuildBaselineRequest,
    BuildBaselineResponse,
    CalibrationStatusResponse,
    ClinicalModelInfo,
    ClinicalModelsStatusResponse,
    ClinicalPredictResponse,
    DepressionPredictRequest,
    EpilepsyPredictRequest,
    HealthResponse,
    SaveSessionRequest,
    SaveSessionResponse,
    SessionHistoryItem,
)
from nurolab.app_backend.services import baseline_service, analytics_service, prediction_service, session_service
from nurolab.app_backend.eeg.streaming import SimulatedEEGSource, eeg_producer
from nurolab.app_backend.eeg.preprocessing import preprocess_pipeline
from nurolab.app_backend.ml.model_registry import ModelRegistry
from nurolab.app_backend.ml.clinical_registry import ClinicalModelRegistry

MODELS_STORE_DIR = Path(__file__).resolve().parent / "models_store"
CLINICAL_MODELS_DIR = Path(__file__).resolve().parent / "clinical_models"

logger = logging.getLogger("nurolab")
logging.basicConfig(level=logging.INFO)

APP_VERSION = "1.0"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    logger.info("NuroLab backend started. Database initialized at storage/nurolab.db")
    yield


app = FastAPI(title="NuroLab API", version=APP_VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load real trained models if present under app_backend/models_store/*.pkl.
# Any model that's missing falls back to the heuristic functions in
# prediction_service.py automatically — nothing else needs to change.
MODEL_REGISTRY = ModelRegistry({
    "stress": MODELS_STORE_DIR / "stress_model.pkl",
    "attention": MODELS_STORE_DIR / "attention_model.pkl",
    "fatigue": MODELS_STORE_DIR / "fatigue_model.pkl",
})
MODELS_LOADED = True  # heuristic fallback always keeps the API functional

# Clinical models — epilepsy (3-class) and depression (2-class) SVM pipelines.
# These are a separate, stateless prediction surface: /clinical/predict/*.
# They are NOT wired into the simulated /ws/live stream, because that stream
# only simulates 8 channels while these models expect specific clinical
# montages (1 channel for epilepsy, up to 66 for depression) — see
# GET /clinical/models/status for exact requirements.
CLINICAL_MODELS = ClinicalModelRegistry({
    "epilepsy": CLINICAL_MODELS_DIR / "nurolab_epilepsy_svm.pkl",
    "depression": CLINICAL_MODELS_DIR / "nurolab_depression_svm.pkl",
})

# ── Data source for the live websocket stream ───────────────────────────────
#
# Swap SimulatedEEGSource -> HardwareEEGSource (see eeg/streaming.py) to
# switch to real hardware. No other code in this file needs to change.
EEG_SOURCE = SimulatedEEGSource(n_channels=8, fs=256.0, window_sec=2.0)


# ── GET /health ──────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
async def health():
    db_ok = True
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Database health check failed: %s", exc)
        db_ok = False

    return HealthResponse(
        status="healthy" if db_ok else "degraded",
        version=APP_VERSION,
        models_loaded=MODELS_LOADED,
        database=db_ok,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


# ── POST /calibration/build_baseline ────────────────────────────────────────

@app.post("/calibration/build_baseline", response_model=BuildBaselineResponse)
async def build_baseline(payload: BuildBaselineRequest, db: ORMSession = Depends(get_db)):
    try:
        baseline = baseline_service.build_baseline(
            db, payload.user_id, payload.alpha, payload.beta, payload.theta
        )
    except Exception as exc:
        logger.exception("Failed to build baseline for user %s", payload.user_id)
        raise HTTPException(status_code=400, detail=f"Failed to build baseline: {exc}") from exc

    return BuildBaselineResponse(
        status="success",
        baseline=BaselineStats(
            alpha_mean=baseline.alpha_mean,
            beta_mean=baseline.beta_mean,
            theta_mean=baseline.theta_mean,
            alpha_std=baseline.alpha_std,
            beta_std=baseline.beta_std,
            theta_std=baseline.theta_std,
            n_samples=baseline.n_samples,
            quality=baseline.quality,
        ),
    )


# ── GET /calibration/status/{user_id} ───────────────────────────────────────

@app.get("/calibration/status/{user_id}", response_model=CalibrationStatusResponse)
async def calibration_status(user_id: str, db: ORMSession = Depends(get_db)):
    baseline = baseline_service.get_latest_baseline(db, user_id)
    if baseline is None:
        return CalibrationStatusResponse(calibrated=False, samples=0, quality="none", created_at=None)

    return CalibrationStatusResponse(
        calibrated=True,
        samples=baseline.n_samples,
        quality=baseline.quality,
        created_at=baseline.created_at,
    )


# ── POST /session/save ──────────────────────────────────────────────────────

@app.post("/session/save", response_model=SaveSessionResponse)
async def save_session(payload: SaveSessionRequest, db: ORMSession = Depends(get_db)):
    try:
        record = session_service.save_session(
            db,
            user_id=payload.user_id,
            alpha=payload.alpha,
            beta=payload.beta,
            theta=payload.theta,
            deviation_score=payload.deviation_score,
            risk_tier=payload.risk_tier,
            stress_prediction=payload.stress_prediction,
            attention_prediction=payload.attention_prediction,
            fatigue_prediction=payload.fatigue_prediction,
        )
    except Exception as exc:
        logger.exception("Failed to save session for user %s", payload.user_id)
        raise HTTPException(status_code=400, detail=f"Failed to save session: {exc}") from exc

    return SaveSessionResponse(status="saved", session_id=record.id)


# ── GET /session/history/{user_id} ──────────────────────────────────────────

@app.get("/session/history/{user_id}", response_model=List[SessionHistoryItem])
async def session_history(
    user_id: str,
    limit: int = Query(default=50, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="desc", pattern="^(asc|desc)$"),
    db: ORMSession = Depends(get_db),
):
    records = session_service.get_history(db, user_id, limit=limit, offset=offset, sort=sort)
    return [
        SessionHistoryItem(
            timestamp=r.timestamp,
            alpha=r.alpha,
            beta=r.beta,
            theta=r.theta,
            deviation_score=r.deviation_score,
            risk_tier=r.risk_tier,
        )
        for r in records
    ]


# ── WebSocket connection manager ────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.add(websocket)
        logger.info("WS connected. Active connections: %d", len(self.active))

    def disconnect(self, websocket: WebSocket):
        self.active.discard(websocket)
        logger.info("WS disconnected. Active connections: %d", len(self.active))


manager = ConnectionManager()


# ── WEBSOCKET /ws/live ───────────────────────────────────────────────────────

@app.websocket("/ws/live")
async def live_stream(websocket: WebSocket, user_id: str = "anonymous"):
    """Streams simulated live EEG-derived metrics every ~2 seconds.

    Query param `user_id` (e.g. ws://host/ws/live?user_id=abc) is used to
    look up that user's baseline, if one exists, for deviation scoring.
    Falls back to a neutral synthetic baseline if the user hasn't calibrated.
    """
    await manager.connect(websocket)

    db = SessionLocal()
    try:
        baseline = baseline_service.get_latest_baseline(db, user_id)

        async for window in eeg_producer(EEG_SOURCE, interval_sec=2.0):
            try:
                filtered = preprocess_pipeline(window, EEG_SOURCE.fs)
                de = analytics_service.compute_DE(filtered, EEG_SOURCE.fs)

                current = {"alpha": de["alpha_de"], "beta": de["beta_de"], "theta": de["theta_de"]}
                extra_metrics = {
                    "delta_de": round(de["delta_de"], 4),
                    "gamma_de": round(de["gamma_de"], 4),
                    "alpha_beta_ratio": round(alpha_beta_ratio(de["alpha_de"], de["beta_de"]), 4),
                    "engagement_index": round(engagement_index(de["beta_de"], de["alpha_de"], de["theta_de"]), 4),
                    "relaxation_index": round(relaxation_index(de["alpha_de"], de["beta_de"]), 4),
                    "cognitive_load": round(cognitive_load_index(de["theta_de"], de["alpha_de"]), 4),
                    "signal_quality": round(signal_quality_score(filtered), 4),
                }

                if baseline is not None:
                    deviation_score = analytics_service.compute_deviation(current, baseline)
                else:
                    # No calibration yet: report a neutral low deviation.
                    deviation_score = 0.0

                risk_tier = analytics_service.compute_risk(deviation_score)
                predictions = prediction_service.predict_all(
                    de["alpha_de"], de["beta_de"], de["theta_de"], registry=MODEL_REGISTRY
                )

                payload = {
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "alpha_de": round(de["alpha_de"], 4),
                    "beta_de": round(de["beta_de"], 4),
                    "theta_de": round(de["theta_de"], 4),
                    "deviation_score": deviation_score,
                    "risk_tier": risk_tier,
                    **extra_metrics,
                    **predictions,
                }

                await websocket.send_text(json.dumps(payload))

            except (WebSocketDisconnect, RuntimeError):
                # RuntimeError covers "Cannot call send once a close message
                # has been sent" if disconnect races the send.
                raise
            except Exception as exc:
                # Don't kill the stream on a single bad window — log and
                # send an error frame, then keep going.
                logger.exception("Error processing EEG window: %s", exc)
                try:
                    await websocket.send_text(json.dumps({"error": str(exc)}))
                except Exception:
                    raise WebSocketDisconnect()

    except WebSocketDisconnect:
        pass
    except asyncio.CancelledError:
        pass
    finally:
        manager.disconnect(websocket)
        db.close()


# ── GET /models/status ───────────────────────────────────────────────────────

@app.get("/models/status")
async def models_status():
    """Shows which real trained models are loaded vs falling back to heuristics."""
    all_names = ["stress", "attention", "fatigue"]
    loaded = MODEL_REGISTRY.loaded_names()
    return {
        "loaded_models": loaded,
        "fallback_models": [n for n in all_names if n not in loaded],
        "models_store_dir": str(MODELS_STORE_DIR),
    }


# ── Clinical models: epilepsy / depression ──────────────────────────────────

DEPRESSION_RELIABILITY_WARNING = (
    "This model's own recorded cross-validation accuracy is ~38% "
    "(fold range 10-58%) on a 7-subject training set — not reliable for "
    "real decisions. Treat output as experimental only."
)


def _clinical_model_info(name: str) -> ClinicalModelInfo:
    model = CLINICAL_MODELS.get(name)
    if model is None:
        return ClinicalModelInfo(loaded=False)
    return ClinicalModelInfo(
        loaded=True,
        condition=model.condition,
        cv_accuracy=model.cv_accuracy,
        cv_std=model.cv_std,
        n_features_expected=len(model.feature_names),
        required_channels=model.required_channels,
        label_map=model.label_map,
    )


@app.get("/clinical/models/status", response_model=ClinicalModelsStatusResponse)
async def clinical_models_status():
    """Metadata for the clinical SVM models: accuracy, required channels, labels."""
    return ClinicalModelsStatusResponse(
        epilepsy=_clinical_model_info("epilepsy"),
        depression=_clinical_model_info("depression"),
    )


@app.post("/clinical/predict/epilepsy", response_model=ClinicalPredictResponse)
async def predict_epilepsy(payload: EpilepsyPredictRequest):
    model = CLINICAL_MODELS.get("epilepsy")
    if model is None:
        raise HTTPException(status_code=503, detail="Epilepsy model is not loaded on this server.")

    channel_data = {"EEG1": np.array(payload.samples, dtype=float)}
    try:
        feature_vector, missing = model.build_feature_vector(channel_data, payload.fs)
        result = model.predict(feature_vector)
    except Exception as exc:
        logger.exception("Epilepsy prediction failed")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    return ClinicalPredictResponse(
        condition="epilepsy",
        predicted_label=result["predicted_label"],
        probabilities=result["probabilities"],
        missing_channels=missing,
        reliability_warning=None,
    )


@app.post("/clinical/predict/depression", response_model=ClinicalPredictResponse)
async def predict_depression(payload: DepressionPredictRequest):
    model = CLINICAL_MODELS.get("depression")
    if model is None:
        raise HTTPException(status_code=503, detail="Depression model is not loaded on this server.")

    channel_data = {name: np.array(samples, dtype=float) for name, samples in payload.channels.items()}
    try:
        feature_vector, missing = model.build_feature_vector(channel_data, payload.fs)
        result = model.predict(feature_vector)
    except Exception as exc:
        logger.exception("Depression prediction failed")
        raise HTTPException(status_code=400, detail=f"Prediction failed: {exc}") from exc

    warning = DEPRESSION_RELIABILITY_WARNING
    if missing:
        warning += f" Additionally, {len(missing)}/{len(model.required_channels)} required channels were missing and zero-filled, further reducing reliability."

    return ClinicalPredictResponse(
        condition="depression",
        predicted_label=result["predicted_label"],
        probabilities=result["probabilities"],
        missing_channels=missing,
        reliability_warning=warning,
    )


# ── Root ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "NuroLab API",
        "version": APP_VERSION,
        "docs": "/docs",
        "websocket": "/ws/live",
    }
