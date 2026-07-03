# File: nurolab/app_backend/tests/test_api.py
# Test suite for the NuroLab dashboard backend.
#
# Run with:
#   pytest app_backend/tests/test_api.py -v
#
# Each test uses a fresh temp SQLite DB (via monkeypatched engine) so tests
# don't pollute or depend on your real storage/nurolab.db.

from __future__ import annotations

import os
import tempfile

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from nurolab.app_backend import server
from nurolab.app_backend.models import database


@pytest.fixture()
def client(monkeypatch):
    """Fresh app + isolated SQLite DB per test."""
    tmp_dir = tempfile.mkdtemp()
    db_path = os.path.join(tmp_dir, "test_nurolab.db")
    test_engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    database.Base.metadata.create_all(bind=test_engine)

    monkeypatch.setattr(database, "engine", test_engine)
    monkeypatch.setattr(database, "SessionLocal", TestSessionLocal)
    monkeypatch.setattr(server, "SessionLocal", TestSessionLocal)

    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()

    server.app.dependency_overrides[database.get_db] = override_get_db

    with TestClient(server.app) as c:
        yield c

    server.app.dependency_overrides.clear()


# ── /health ──────────────────────────────────────────────────────────────────

def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["database"] is True
    assert body["models_loaded"] is True
    assert "timestamp" in body


# ── /calibration/build_baseline ─────────────────────────────────────────────

def test_build_baseline_success(client):
    payload = {
        "user_id": "user1",
        "alpha": [1.0, 1.2, 0.9, 1.1, 1.05] * 10,
        "beta": [0.5, 0.6, 0.55, 0.52, 0.58] * 10,
        "theta": [0.8, 0.85, 0.78, 0.82, 0.81] * 10,
    }
    resp = client.post("/calibration/build_baseline", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert body["baseline"]["n_samples"] == 50
    assert body["baseline"]["quality"] in {"good", "fair", "poor"}


def test_build_baseline_mismatched_lengths(client):
    payload = {
        "user_id": "user1",
        "alpha": [1.0, 1.2],
        "beta": [0.5],
        "theta": [0.8, 0.7],
    }
    resp = client.post("/calibration/build_baseline", json=payload)
    assert resp.status_code == 422  # pydantic validation error


# ── /calibration/status/{user_id} ───────────────────────────────────────────

def test_calibration_status_not_calibrated(client):
    resp = client.get("/calibration/status/no_such_user")
    assert resp.status_code == 200
    body = resp.json()
    assert body["calibrated"] is False


def test_calibration_status_after_baseline(client):
    payload = {
        "user_id": "user2",
        "alpha": [1.0] * 60,
        "beta": [0.5] * 60,
        "theta": [0.8] * 60,
    }
    client.post("/calibration/build_baseline", json=payload)

    resp = client.get("/calibration/status/user2")
    body = resp.json()
    assert body["calibrated"] is True
    assert body["samples"] == 60


# ── /session/save ────────────────────────────────────────────────────────────

def test_save_session(client):
    payload = {
        "user_id": "user3",
        "alpha": 0.4,
        "beta": 0.6,
        "theta": 0.5,
        "deviation_score": 18,
        "risk_tier": "moderate",
        "stress_prediction": 0.8,
        "attention_prediction": 0.7,
        "fatigue_prediction": 0.3,
    }
    resp = client.post("/session/save", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "saved"
    assert isinstance(body["session_id"], int)


def test_save_session_invalid_risk_tier(client):
    payload = {
        "user_id": "user3",
        "alpha": 0.4,
        "beta": 0.6,
        "theta": 0.5,
        "deviation_score": 18,
        "risk_tier": "extreme",  # invalid
    }
    resp = client.post("/session/save", json=payload)
    assert resp.status_code == 422


# ── /session/history/{user_id} ──────────────────────────────────────────────

def test_session_history(client):
    for i in range(3):
        client.post(
            "/session/save",
            json={
                "user_id": "user4",
                "alpha": 0.4 + i * 0.1,
                "beta": 0.6,
                "theta": 0.5,
                "deviation_score": 10 + i,
                "risk_tier": "low",
            },
        )

    resp = client.get("/session/history/user4")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 3
    # default sort is desc by timestamp
    assert body[0]["deviation_score"] >= body[-1]["deviation_score"] - 5


def test_session_history_pagination(client):
    for i in range(5):
        client.post(
            "/session/save",
            json={
                "user_id": "user5",
                "alpha": 0.4,
                "beta": 0.6,
                "theta": 0.5,
                "deviation_score": 10,
                "risk_tier": "low",
            },
        )

    resp = client.get("/session/history/user5?limit=2&offset=1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_session_history_empty_for_unknown_user(client):
    resp = client.get("/session/history/nobody")
    assert resp.status_code == 200
    assert resp.json() == []


# ── WS /ws/live ──────────────────────────────────────────────────────────────

def test_ws_live_streams_payload(client):
    with client.websocket_connect("/ws/live?user_id=wsuser") as websocket:
        data = websocket.receive_json()
        assert "alpha_de" in data
        assert "beta_de" in data
        assert "theta_de" in data
        assert "deviation_score" in data
        assert "risk_tier" in data
        assert data["risk_tier"] in {"low", "moderate", "high"}
        assert "stress_prediction" in data
        assert "attention_prediction" in data
        assert "fatigue_prediction" in data


# ── Clinical models: epilepsy / depression ──────────────────────────────────

def test_clinical_models_status(client):
    resp = client.get("/clinical/models/status")
    assert resp.status_code == 200
    body = resp.json()
    assert body["epilepsy"]["loaded"] is True
    assert body["epilepsy"]["n_features_expected"] == 8
    assert body["depression"]["loaded"] is True
    assert body["depression"]["n_features_expected"] == 528
    # Depression's own recorded accuracy should be surfaced, not hidden.
    assert body["depression"]["cv_accuracy"] < 0.5


def test_predict_epilepsy(client):
    import random
    random.seed(1)
    samples = [random.gauss(0, 1) for _ in range(512)]
    resp = client.post("/clinical/predict/epilepsy", json={"samples": samples, "fs": 256})
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_label"] in {"normal", "interictal", "seizure"}
    assert abs(sum(body["probabilities"].values()) - 1.0) < 1e-6
    assert body["missing_channels"] == []


def test_predict_epilepsy_too_few_samples(client):
    resp = client.post("/clinical/predict/epilepsy", json={"samples": [0.1, 0.2], "fs": 256})
    assert resp.status_code == 422  # below min_length


def test_predict_depression_partial_channels_flags_missing(client):
    import random
    random.seed(2)
    channels = {"FP1": [random.gauss(0, 1) for _ in range(512)]}
    resp = client.post("/clinical/predict/depression", json={"channels": channels, "fs": 256})
    assert resp.status_code == 200
    body = resp.json()
    assert body["predicted_label"] in {"control", "depressed"}
    assert len(body["missing_channels"]) > 0
    assert "reliability_warning" in body
    assert body["reliability_warning"] is not None
    assert "38%" in body["reliability_warning"] or "not reliable" in body["reliability_warning"]


def test_predict_depression_reliability_warning_always_present(client):
    """Even with zero missing channels, the warning must still appear —
    the model's own cross-validation accuracy is the problem, not just
    incomplete input."""
    import random
    random.seed(3)
    # Deliberately supply just a couple of the required channels; regardless
    # of how many are supplied, reliability_warning must never be None.
    channels = {"FP1": [random.gauss(0, 1) for _ in range(512)], "CZ": [random.gauss(0, 1) for _ in range(512)]}
    resp = client.post("/clinical/predict/depression", json={"channels": channels, "fs": 256})
    body = resp.json()
    assert body["reliability_warning"] is not None

