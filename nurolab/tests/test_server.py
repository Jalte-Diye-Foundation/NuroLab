# File: nurolab/tests/test_server.py
#
# Automated tests for the NuroLab backend REST endpoints.
# Run with:  python nurolab/tests/test_server.py   (backend must already be running)
#
# Each test is a small function that makes a request and checks the response.
# We use a tiny custom runner (not pytest) so failures print a plain,
# readable PASS/FAIL line with a clear reason.

import sys
import requests

BASE_URL = "http://127.0.0.1:8000"
TEST_USER_ID = "test-user-001"
TIMEOUT_SEC = 5

_results = []  # (name, passed: bool, message: str)


def check(name, condition, message=""):
    _results.append((name, bool(condition), message))


def url(path):
    return BASE_URL + path


def _is_json(response):
    try:
        response.json()
        return True
    except ValueError:
        return False


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
def test_health():
    try:
        r = requests.get(url("/health"), timeout=TIMEOUT_SEC)
    except requests.exceptions.ConnectionError:
        check("health: server reachable", False, "Could not connect -- is the server running?")
        return
    check("health: status 200", r.status_code == 200, f"got {r.status_code}")
    check("health: response is JSON", _is_json(r), "response body was not valid JSON")
    if _is_json(r):
        body = r.json()
        check("health: has 'status' field", "status" in body, f"body={body}")
        check("health: has 'database' field", "database" in body, f"body={body}")


# ---------------------------------------------------------------------------
# Calibration — build_baseline (normal + bad input), then status
# ---------------------------------------------------------------------------
def test_build_baseline_normal():
    payload = {
        "user_id": TEST_USER_ID,
        "alpha": [1.1, 1.2, 1.0, 1.3, 1.15],
        "beta": [0.8, 0.9, 0.85, 0.95, 0.88],
        "theta": [0.5, 0.55, 0.52, 0.6, 0.53],
    }
    r = requests.post(url("/calibration/build_baseline"), json=payload, timeout=TIMEOUT_SEC)
    check("build_baseline (valid input): status 200", r.status_code == 200, f"got {r.status_code}, body={r.text}")
    if _is_json(r):
        body = r.json()
        check("build_baseline: response has 'baseline' field", "baseline" in body, f"body={body}")


def test_build_baseline_bad_input():
    # alpha/beta/theta arrays of mismatched length -- schema should reject this.
    payload = {
        "user_id": TEST_USER_ID,
        "alpha": [1.1, 1.2],
        "beta": [0.8],
        "theta": [0.5, 0.55],
    }
    r = requests.post(url("/calibration/build_baseline"), json=payload, timeout=TIMEOUT_SEC)
    check(
        "build_baseline (mismatched array lengths): rejected with 4xx",
        400 <= r.status_code < 500,
        f"expected a 4xx rejection, got {r.status_code}",
    )


def test_calibration_status_known_user():
    # Depends on test_build_baseline_normal having run first.
    r = requests.get(url(f"/calibration/status/{TEST_USER_ID}"), timeout=TIMEOUT_SEC)
    check("calibration_status (known user): status 200", r.status_code == 200, f"got {r.status_code}")
    if _is_json(r):
        body = r.json()
        check("calibration_status: calibrated is true", body.get("calibrated") is True, f"body={body}")


def test_calibration_status_unknown_user():
    r = requests.get(url("/calibration/status/no-such-user-xyz"), timeout=TIMEOUT_SEC)
    check("calibration_status (unknown user): status 200", r.status_code == 200, f"got {r.status_code}")
    if _is_json(r):
        body = r.json()
        check("calibration_status (unknown user): calibrated is false", body.get("calibrated") is False, f"body={body}")


# ---------------------------------------------------------------------------
# Session save (normal + bad input), then history
# ---------------------------------------------------------------------------
def test_session_save_normal():
    payload = {
        "user_id": TEST_USER_ID,
        "alpha": 1.2,
        "beta": 0.8,
        "theta": 0.5,
        "deviation_score": 12.4,
        "risk_tier": "low",
    }
    r = requests.post(url("/session/save"), json=payload, timeout=TIMEOUT_SEC)
    check("session_save (valid input): status 200", r.status_code == 200, f"got {r.status_code}, body={r.text}")
    if _is_json(r):
        body = r.json()
        check("session_save: response has 'session_id'", "session_id" in body, f"body={body}")


def test_session_save_bad_input():
    # Invalid risk_tier -- schema only allows low/moderate/high.
    payload = {
        "user_id": TEST_USER_ID,
        "alpha": 1.2,
        "beta": 0.8,
        "theta": 0.5,
        "deviation_score": 12.4,
        "risk_tier": "extreme",  # not a valid value
    }
    r = requests.post(url("/session/save"), json=payload, timeout=TIMEOUT_SEC)
    check(
        "session_save (invalid risk_tier): rejected with 4xx",
        400 <= r.status_code < 500,
        f"expected a 4xx rejection, got {r.status_code}",
    )


def test_session_history_known_user():
    # Depends on test_session_save_normal having run first.
    r = requests.get(url(f"/session/history/{TEST_USER_ID}"), timeout=TIMEOUT_SEC)
    check("session_history (known user): status 200", r.status_code == 200, f"got {r.status_code}, body={r.text}")
    if _is_json(r):
        body = r.json()
        check("session_history: returns a non-empty list", isinstance(body, list) and len(body) > 0, f"body={body}")


def test_session_history_unknown_user():
    # NOTE: this endpoint returns an empty list for an unknown user, not a 404 --
    # there's no existence check in the handler, it just queries and returns
    # whatever it finds (nothing, in this case).
    r = requests.get(url("/session/history/no-such-user-xyz"), timeout=TIMEOUT_SEC)
    check("session_history (unknown user): status 200", r.status_code == 200, f"got {r.status_code}")
    if _is_json(r):
        body = r.json()
        check("session_history (unknown user): returns empty list", body == [], f"body={body}")


# ---------------------------------------------------------------------------
# Clinical predictions -- stateless, not session-based
# ---------------------------------------------------------------------------
def test_predict_epilepsy_normal():
    # Model requires at least 16 samples, single channel.
    payload = {"samples": [0.1, 0.2, 0.15, 0.05, -0.1, 0.12, 0.08, 0.03,
                            0.11, 0.19, 0.14, 0.06, -0.09, 0.13, 0.07, 0.04],
               "fs": 256}
    r = requests.post(url("/clinical/predict/epilepsy"), json=payload, timeout=TIMEOUT_SEC)
    check("predict_epilepsy (valid input): status 200", r.status_code == 200, f"got {r.status_code}, body={r.text}")
    if _is_json(r):
        body = r.json()
        check("predict_epilepsy: has 'predicted_label'", "predicted_label" in body, f"body={body}")


def test_predict_epilepsy_bad_input():
    # Fewer than 16 samples -- schema should reject this.
    payload = {"samples": [0.1, 0.2, 0.3], "fs": 256}
    r = requests.post(url("/clinical/predict/epilepsy"), json=payload, timeout=TIMEOUT_SEC)
    check(
        "predict_epilepsy (too few samples): rejected with 4xx",
        400 <= r.status_code < 500,
        f"expected a 4xx rejection, got {r.status_code}",
    )


def test_predict_depression_normal():
    # Model tolerates missing channels (zero-filled), so a small subset is fine.
    payload = {"channels": {"Fp1": [0.1, 0.2, 0.15, 0.05] * 10,
                             "Fp2": [0.11, 0.19, 0.14, 0.06] * 10},
               "fs": 256}
    r = requests.post(url("/clinical/predict/depression"), json=payload, timeout=TIMEOUT_SEC)
    check("predict_depression (valid input): status 200", r.status_code == 200, f"got {r.status_code}, body={r.text}")
    if _is_json(r):
        body = r.json()
        check("predict_depression: has 'missing_channels'", "missing_channels" in body, f"body={body}")
        check("predict_depression: has reliability_warning (documented low accuracy)",
              body.get("reliability_warning") is not None, f"body={body}")


def test_predict_depression_bad_input():
    # Empty channels dict -- schema requires at least 1.
    payload = {"channels": {}, "fs": 256}
    r = requests.post(url("/clinical/predict/depression"), json=payload, timeout=TIMEOUT_SEC)
    check(
        "predict_depression (empty channels): rejected with 4xx",
        400 <= r.status_code < 500,
        f"expected a 4xx rejection, got {r.status_code}",
    )


def test_clinical_models_status():
    r = requests.get(url("/clinical/models/status"), timeout=TIMEOUT_SEC)
    check("clinical_models_status: status 200", r.status_code == 200, f"got {r.status_code}")
    if _is_json(r):
        body = r.json()
        check("clinical_models_status: has 'epilepsy' and 'depression' keys",
              "epilepsy" in body and "depression" in body, f"body={body}")


# ---------------------------------------------------------------------------
# runner
# ---------------------------------------------------------------------------
def main():
    tests = [
        test_health,
        test_build_baseline_normal,
        test_build_baseline_bad_input,
        test_calibration_status_known_user,
        test_calibration_status_unknown_user,
        test_session_save_normal,
        test_session_save_bad_input,
        test_session_history_known_user,
        test_session_history_unknown_user,
        test_predict_epilepsy_normal,
        test_predict_epilepsy_bad_input,
        test_predict_depression_normal,
        test_predict_depression_bad_input,
        test_clinical_models_status,
    ]

    print(f"Running REST endpoint tests against {BASE_URL}\n" + "=" * 60)
    for t in tests:
        try:
            t()
        except Exception as e:
            check(t.__name__, False, f"test raised an unexpected error: {e}")

    n_pass = sum(1 for _, ok, _ in _results if ok)
    n_fail = len(_results) - n_pass

    for name, ok, message in _results:
        status = "PASS" if ok else "FAIL"
        line = f"[{status}] {name}"
        if not ok and message:
            line += f"  -- {message}"
        print(line)

    print("=" * 60)
    print(f"{n_pass} passed, {n_fail} failed, {len(_results)} total")
    sys.exit(0 if n_fail == 0 else 1)


if __name__ == "__main__":
    main()
