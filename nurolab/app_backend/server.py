# File: nurolab/app_backend/server.py
# Backend API Server — FastAPI + WebSocket
#
# The app NEVER talks to Python or hardware directly.
# It opens a WebSocket to this server and receives JSON.
#
# Run with:
#   uvicorn nurolab.app_backend.server:app --reload --port 8000
#
# Install: pip install fastapi uvicorn websockets

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import numpy as np
from pathlib import Path

from nurolab.datasources.replay_source import SyntheticEEGSource
from nurolab.processing.windowing import SlidingWindowEngine
from nurolab.processing.filters import stage_a_pipeline
from nurolab.processing.features import extract_feature_vector, build_feature_names
from nurolab.processing.deviation_engine import DeviationEngine
from nurolab.ml.model_registry import ModelRegistry
from nurolab.ml.explain import explain_prediction, risk_tier_from_mahalanobis
from nurolab.app_backend.privacy_safeguards import PrivacySafeguardsEngine

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_ROOT = PROJECT_ROOT / "models"

app = FastAPI(title="NuroLab API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Data Source (swap ONE LINE to change the source) ───────────────────────────
#
#   SyntheticEEGSource()                  <- fake data, no dataset needed
#   ReplaySource(some_offline_source)     <- replay a real dataset file
#   LiveHardwareSource(port='/dev/ttyUSB0') <- real hardware
#
DATA_SOURCE = SyntheticEEGSource(
    n_channels=8,
    fs=256.0,
    channel_names=["Fp1", "Fp2", "F3", "F4", "T7", "T8", "O1", "O2"],
)

FEATURE_NAMES = build_feature_names(DATA_SOURCE.channel_names)

# Loaded models — skip conditions whose .pkl doesn't exist yet
MODELS = ModelRegistry({
    "depression": MODELS_ROOT / "nurolab_depression_svm.pkl",
    "epilepsy":   MODELS_ROOT / "nurolab_epilepsy_svm.pkl",
})

# Deviation engine — set after calibration completes
_deviation_engine: DeviationEngine | None = None
_privacy_engine = PrivacySafeguardsEngine()


# ── WebSocket: live EEG stream ─────────────────────────────────────────────────

@app.websocket("/ws/live")
async def live_stream(websocket: WebSocket):
    await websocket.accept()
    engine = SlidingWindowEngine(
        DATA_SOURCE, window_sec=20.0, stride_sec=2.0
    )
    try:
        for window, meta in engine.windows():
            # Stage A: filter
            filtered = stage_a_pipeline(window, DATA_SOURCE.sample_rate)

            # Stage C–E: feature extraction
            fv = extract_feature_vector(filtered, DATA_SOURCE.sample_rate)

            # ML inference (only if models are loaded)
            predictions = MODELS.predict_all(filtered, DATA_SOURCE.sample_rate)

            payload = {
                "window_start_time": meta["window_start_time"],
                "window_end_time":   meta["window_end_time"],
                "feature_vector":    fv.tolist(),
                "predictions":       predictions,
            }

            # Deviation from personal baseline (only after calibration)
            if _deviation_engine is not None:
                dev = _deviation_engine.evaluate(fv)
                payload["deviation"] = {
                    "mahalanobis":  dev["mahalanobis"],
                    "risk_tier":    risk_tier_from_mahalanobis(dev["mahalanobis"]),
                    "explanations": explain_prediction(dev["z_scores"], FEATURE_NAMES),
                }

            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(0)   # yield control so other tasks can run

    except WebSocketDisconnect:
        pass


# ── POST: build personal baseline after calibration wizard ────────────────────

@app.post("/calibration/build_baseline")
async def build_baseline(relaxed_windows: list):
    """
    Called after the app's calibration wizard finishes.

    Body: list of feature vectors (each a list of floats) collected
    during the relaxed-baseline phase.

    Returns: {status, n_windows}
    """
    global _deviation_engine
    X = np.array(relaxed_windows, dtype=float)
    _deviation_engine = DeviationEngine(X, FEATURE_NAMES)
    return {"status": "baseline_ready", "n_windows": len(X)}


# ── GET: check calibration status ─────────────────────────────────────────────

@app.get("/calibration/status")
async def calibration_status():
    return {
        "calibrated":   _deviation_engine is not None,
        "n_features":   len(FEATURE_NAMES),
        "data_source":  DATA_SOURCE.__class__.__name__,
        "models_loaded": list(MODELS.models.keys()),
    }


# ── GET: health check ─────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}
