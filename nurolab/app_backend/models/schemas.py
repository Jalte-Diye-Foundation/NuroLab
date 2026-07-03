# File: nurolab/app_backend/models/schemas.py
# Pydantic request/response models for the NuroLab API.

from __future__ import annotations

import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    models_loaded: bool
    database: bool
    timestamp: datetime.datetime


# ── Calibration / Baseline ─────────────────────────────────────────────────

class BuildBaselineRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    alpha: List[float] = Field(..., min_length=1)
    beta: List[float] = Field(..., min_length=1)
    theta: List[float] = Field(..., min_length=1)

    @field_validator("beta")
    @classmethod
    def _beta_len_matches_alpha(cls, v, info):
        alpha = info.data.get("alpha")
        if alpha is not None and len(v) != len(alpha):
            raise ValueError("alpha, beta, and theta arrays must be the same length")
        return v

    @field_validator("theta")
    @classmethod
    def _theta_len_matches_alpha(cls, v, info):
        alpha = info.data.get("alpha")
        if alpha is not None and len(v) != len(alpha):
            raise ValueError("alpha, beta, and theta arrays must be the same length")
        return v


class BaselineStats(BaseModel):
    alpha_mean: float
    beta_mean: float
    theta_mean: float
    alpha_std: float
    beta_std: float
    theta_std: float
    n_samples: int
    quality: str


class BuildBaselineResponse(BaseModel):
    status: str
    baseline: BaselineStats


class CalibrationStatusResponse(BaseModel):
    calibrated: bool
    samples: int = 0
    quality: str = "none"
    created_at: Optional[datetime.datetime] = None


# ── Sessions ────────────────────────────────────────────────────────────────

class SaveSessionRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    alpha: float
    beta: float
    theta: float
    deviation_score: float
    risk_tier: str
    stress_prediction: Optional[float] = None
    attention_prediction: Optional[float] = None
    fatigue_prediction: Optional[float] = None

    @field_validator("risk_tier")
    @classmethod
    def _valid_tier(cls, v: str) -> str:
        allowed = {"low", "moderate", "high"}
        if v.lower() not in allowed:
            raise ValueError(f"risk_tier must be one of {allowed}")
        return v.lower()


class SaveSessionResponse(BaseModel):
    status: str
    session_id: int


class SessionHistoryItem(BaseModel):
    timestamp: datetime.datetime
    alpha: float
    beta: float
    theta: float
    deviation_score: float
    risk_tier: str


# ── WebSocket live payload (for documentation / client typing only) ────────

class LiveStreamPayload(BaseModel):
    timestamp: datetime.datetime
    alpha_de: float
    beta_de: float
    theta_de: float
    deviation_score: float
    risk_tier: str
    stress_prediction: float
    attention_prediction: float
    fatigue_prediction: float


# ── Clinical models (epilepsy / depression SVM pipelines) ──────────────────

class EpilepsyPredictRequest(BaseModel):
    """Single-channel EEG samples (the model expects one channel, internally
    labeled 'EEG1' — send whichever channel you want scored)."""
    samples: List[float] = Field(..., min_length=16)
    fs: float = Field(..., gt=0)


class DepressionPredictRequest(BaseModel):
    """Multi-channel EEG samples keyed by 10-20-style channel name.

    The model was trained on a 66-channel montage (see GET
    /clinical/models/status for the full required channel list). You do not
    need to supply all 66 — missing channels are zero-filled — but omitting
    channels significantly degrades reliability, and is reported back in
    `missing_channels`.
    """
    channels: dict[str, List[float]] = Field(..., min_length=1)
    fs: float = Field(..., gt=0)


class ClinicalPredictResponse(BaseModel):
    condition: str
    predicted_label: str
    probabilities: dict[str, float]
    missing_channels: List[str] = Field(default_factory=list)
    reliability_warning: Optional[str] = None


class ClinicalModelInfo(BaseModel):
    loaded: bool
    condition: Optional[str] = None
    cv_accuracy: Optional[float] = None
    cv_std: Optional[float] = None
    n_features_expected: Optional[int] = None
    required_channels: Optional[List[str]] = None
    label_map: Optional[dict] = None


class ClinicalModelsStatusResponse(BaseModel):
    epilepsy: ClinicalModelInfo
    depression: ClinicalModelInfo

